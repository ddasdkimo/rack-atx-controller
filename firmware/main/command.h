// Shared command layer used by both the HTTP API and the USB console.
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "outputs.h"
#include "cJSON.h"

typedef enum {
    CMD_OK = 0,
    CMD_INVALID,        // 400
    CMD_FORBIDDEN,      // 403 (lease / self target / policy)
    CMD_BUSY,           // 409
    CMD_HW_FAULT,       // 503
} cmd_status_t;

typedef struct {
    cmd_status_t status;
    char code[32];      // machine-readable reason
    uint32_t seq;
    uint32_t actual_ms;
} cmd_result_t;

// node: 0/1 for authenticated nodes, -1 for the console (no lease required, policy still applies).
cmd_result_t command_press(int node, uint8_t host, button_t button, uint32_t ms);

// Full status document (caller deletes).
cJSON *command_status_json(void);
cJSON *command_lease_json(void);
cJSON *command_nodes_json(void);
