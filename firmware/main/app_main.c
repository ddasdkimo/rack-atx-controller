// Rack ATX controller B.2 firmware entry. Order matters: outputs are driven to a safe state
// before anything else, the shared SPI bus is created by the Ethernet driver, then the
// 74HC595 chain is cleared and enabled, then the network services start.
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_task_wdt.h"
#include "nvs_flash.h"
#include "driver/gpio.h"
#include "board.h"
#include "config.h"
#include "audit.h"
#include "outputs.h"
#include "eth.h"
#include "auth.h"
#include "lease.h"
#include "policy.h"
#include "api.h"
#include "console.h"

static const char *TAG = "main";

static void early_safe_pins(void)
{
    // Before any driver runs: ARM low, OE high (external pull-up already does this), latch low.
    gpio_reset_pin(PIN_TIMER_ARM);
    gpio_set_direction(PIN_TIMER_ARM, GPIO_MODE_OUTPUT);
    gpio_set_level(PIN_TIMER_ARM, 0);
    gpio_reset_pin(PIN_OUT_OE_N);
    gpio_set_direction(PIN_OUT_OE_N, GPIO_MODE_OUTPUT);
    gpio_set_level(PIN_OUT_OE_N, 1);
    gpio_reset_pin(PIN_OUT_LATCH);
    gpio_set_direction(PIN_OUT_LATCH, GPIO_MODE_OUTPUT);
    gpio_set_level(PIN_OUT_LATCH, 0);
}

void app_main(void)
{
    early_safe_pins();
    ESP_LOGI(TAG, "rack-atx-controller %s", FW_VERSION);

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);
    ESP_ERROR_CHECK(config_load());

    audit_init();
    policy_init();
    lease_init();
    auth_init();
    audit_add("boot", "", 0, "", 0, FW_VERSION);

    // Task watchdog: main task + the HTTP server task feed it; a press feeds it every second.
    esp_task_wdt_config_t wdt = {.timeout_ms = 15000, .idle_core_mask = 0, .trigger_panic = true};
    esp_task_wdt_reconfigure(&wdt);
    esp_task_wdt_add(NULL);

    ESP_ERROR_CHECK(eth_init());                 // creates the SPI bus
    ESP_ERROR_CHECK(outputs_init(SPI_HOST_USED)); // clears 595 chain, then OE low
    ESP_ERROR_CHECK(api_start());
    if (console_start() != ESP_OK) {
        ESP_LOGW(TAG, "console unavailable");
    }
    if (!g_cfg.key_set[0] && !g_cfg.key_set[1]) {
        ESP_LOGW(TAG, "no node keys configured: network commands will be rejected; use the USB console");
    }

    for (;;) {
        esp_task_wdt_reset();
        vTaskDelay(pdMS_TO_TICKS(1000));
        // Expire stale leases even when no request arrives, so the audit log shows it promptly.
        (void)lease_get();
    }
}
