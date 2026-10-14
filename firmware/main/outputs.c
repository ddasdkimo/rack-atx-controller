#include "outputs.h"
#include "board.h"
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_task_wdt.h"
#include "esp_rom_sys.h"

static const char *TAG = "outputs";
static spi_device_handle_t s_sr;
static SemaphoreHandle_t s_lock;
static outputs_state_t s_state;

// Build the 3-byte wire frame for a single DRV index (1..20) or 0 for all off.
static void build_frame(uint8_t drv, uint8_t frame[SR_DEVICES])
{
    memset(frame, 0, SR_DEVICES);
    if (drv == 0 || drv > DRV_COUNT) {
        return;
    }
    uint8_t dev = (drv - 1) / 8;     // 0 = U4, 1 = U5, 2 = U6
    uint8_t bit = (drv - 1) % 8;     // bit0 = QA
    // Wire order: U6 first, U4 last -> index SR_DEVICES-1-dev
    frame[SR_DEVICES - 1 - dev] = (uint8_t)(1u << bit);
}

// Shift one complete 24-bit frame and pulse RCLK while holding the shared bus, so no W5500
// transaction can clock extra bits into the shift register between the frame and the latch.
static esp_err_t write_frame(const uint8_t frame[SR_DEVICES])
{
    spi_transaction_t t = {
        .length = 8 * SR_DEVICES,
        .tx_buffer = frame,
    };
    esp_err_t err = spi_device_acquire_bus(s_sr, portMAX_DELAY);
    if (err != ESP_OK) {
        return err;
    }
    err = spi_device_polling_transmit(s_sr, &t);
    if (err == ESP_OK) {
        gpio_set_level(PIN_OUT_LATCH, 1);
        esp_rom_delay_us(2);
        gpio_set_level(PIN_OUT_LATCH, 0);
    }
    spi_device_release_bus(s_sr);
    return err;
}

esp_err_t outputs_init(spi_host_device_t host)
{
    s_lock = xSemaphoreCreateMutex();
    if (!s_lock) {
        return ESP_ERR_NO_MEM;
    }
    // Pins default to safe levels through external resistors; drive them explicitly anyway.
    gpio_config_t io = {
        .pin_bit_mask = (1ULL << PIN_TIMER_ARM) | (1ULL << PIN_OUT_OE_N) | (1ULL << PIN_OUT_LATCH),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_set_level(PIN_OUT_OE_N, 1);
    gpio_set_level(PIN_TIMER_ARM, 0);
    gpio_set_level(PIN_OUT_LATCH, 0);
    ESP_ERROR_CHECK(gpio_config(&io));
    gpio_set_level(PIN_OUT_OE_N, 1);
    gpio_set_level(PIN_TIMER_ARM, 0);
    gpio_set_level(PIN_OUT_LATCH, 0);

    gpio_config_t vbus = {
        .pin_bit_mask = (1ULL << PIN_USB_VBUS_SENSE),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&vbus));

    spi_device_interface_config_t dev = {
        .clock_speed_hz = SR_SPI_CLOCK_HZ,
        .mode = 0,
        .spics_io_num = -1,   // no chip select: RCLK is pulsed manually
        .queue_size = 1,
    };
    esp_err_t err = spi_bus_add_device(host, &dev, &s_sr);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "spi_bus_add_device failed: %s", esp_err_to_name(err));
        return err;
    }

    uint8_t zero[SR_DEVICES] = {0};
    err = write_frame(zero);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "initial clear failed: %s", esp_err_to_name(err));
        return err;
    }
    gpio_set_level(PIN_OUT_OE_N, 0);
    s_state.oe_enabled = true;
    s_state.ready = true;
    ESP_LOGI(TAG, "outputs cleared, OE enabled, ARM low");
    return ESP_OK;
}

esp_err_t outputs_press(uint8_t host, button_t button, uint32_t ms, uint32_t *actual_ms)
{
    if (host < 1 || host > HOST_COUNT || ms < PRESS_MIN_MS || ms > PRESS_MAX_MS) {
        return ESP_ERR_INVALID_ARG;
    }
    if (!s_state.ready) {
        return ESP_ERR_INVALID_STATE;
    }
    if (xSemaphoreTake(s_lock, 0) != pdTRUE) {
        return ESP_ERR_INVALID_STATE;   // busy
    }
    s_state.busy = true;

    uint8_t drv = (button == BUTTON_POWER) ? DRV_POWER(host) : DRV_RESET(host);
    uint8_t frame[SR_DEVICES], zero[SR_DEVICES] = {0};
    build_frame(drv, frame);

    esp_err_t err = write_frame(frame);
    int64_t t0 = 0, t1 = 0;
    if (err == ESP_OK) {
        // Rail on: ARM releases the MC14541B master reset and enables the Q200 gate. The
        // photorelay LED current only exists while PHOTO_5V is up, so the base drive written
        // above is harmless until this edge.
        t0 = esp_timer_get_time();
        gpio_set_level(PIN_TIMER_ARM, 1);
        s_state.arm = true;
        // Feed the task watchdog across long holds (up to 10 s).
        uint32_t left = ms;
        while (left > 0) {
            uint32_t chunk = left > 1000 ? 1000 : left;
            vTaskDelay(pdMS_TO_TICKS(chunk));
            esp_task_wdt_reset();
            left -= chunk;
        }
        gpio_set_level(PIN_TIMER_ARM, 0);
        s_state.arm = false;
        t1 = esp_timer_get_time();
    }
    esp_err_t err2 = write_frame(zero);
    vTaskDelay(pdMS_TO_TICKS(ARM_LOW_GAP_MS));

    if (err == ESP_OK && err2 != ESP_OK) {
        err = err2;
    }
    if (err == ESP_OK) {
        s_state.presses++;
        if (actual_ms) {
            *actual_ms = (uint32_t)((t1 - t0) / 1000);
        }
        ESP_LOGI(TAG, "press host %u %s %lu ms (drv %u)", host, button == BUTTON_POWER ? "power" : "reset",
                 (unsigned long)ms, drv);
    } else {
        ESP_LOGE(TAG, "press failed: %s", esp_err_to_name(err));
        outputs_safe_state();
    }
    s_state.busy = false;
    xSemaphoreGive(s_lock);
    return err;
}

void outputs_safe_state(void)
{
    gpio_set_level(PIN_TIMER_ARM, 0);
    s_state.arm = false;
    uint8_t zero[SR_DEVICES] = {0};
    (void)write_frame(zero);
    gpio_set_level(PIN_OUT_OE_N, 1);
    s_state.oe_enabled = false;
    s_state.ready = false;
    ESP_LOGW(TAG, "outputs forced to safe state (OE high); reboot to recover");
}

outputs_state_t outputs_get_state(void)
{
    return s_state;
}
