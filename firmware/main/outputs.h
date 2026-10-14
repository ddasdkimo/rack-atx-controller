// 74HC595 frame writer + MC14541B ARM sequencing. One hardware action at a time.
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "driver/spi_master.h"

typedef enum { BUTTON_POWER = 0, BUTTON_RESET = 1 } button_t;

typedef struct {
    bool ready;          // init completed, outputs cleared, OE enabled
    bool arm;            // ARM pin currently high
    bool oe_enabled;     // OE_N currently low
    bool busy;           // a press is executing
    uint32_t presses;    // total presses since boot
} outputs_state_t;

// Must be called after the SPI bus (shared with W5500) exists. Sequence: OE high, ARM low,
// shift 24 zeros, latch, then OE low.
esp_err_t outputs_init(spi_host_device_t host);

// Blocking press: single bit frame -> latch -> ARM high -> ms -> ARM low -> zero frame -> gap.
// Returns ESP_ERR_INVALID_ARG for bad host/ms, ESP_ERR_INVALID_STATE if busy or not ready.
esp_err_t outputs_press(uint8_t host, button_t button, uint32_t ms, uint32_t *actual_ms);

// Emergency: ARM low, zero frame, OE high. Used on fatal errors.
void outputs_safe_state(void);

outputs_state_t outputs_get_state(void);
