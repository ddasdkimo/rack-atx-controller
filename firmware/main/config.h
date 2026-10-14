// Persistent configuration in NVS namespace "atx".
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#define NODE_COUNT 2            // index 0 = "A", 1 = "B"
#define KEY_LEN 32

typedef struct {
    bool dhcp;
    char ip[16], mask[16], gw[16];
    uint8_t key[NODE_COUNT][KEY_LEN];
    bool key_set[NODE_COUNT];
    uint8_t node_host[NODE_COUNT];   // 1..10, 0 = unknown (self-target check disabled for that node)
    uint32_t cooldown_s;
    uint32_t max_per_hour;
    uint32_t takeover_s;
    uint32_t lease_ttl_s;
    bool console_ctl;
} app_config_t;

extern app_config_t g_cfg;

esp_err_t config_load(void);           // defaults + NVS overrides
esp_err_t config_save(void);
esp_err_t config_set(const char *key, const char *value);   // console "config set"
void config_print(void);               // masks keys
int config_node_index(const char *name);   // "A"->0, "B"->1, else -1
const char *config_node_name(int idx);

// Replay floor persistence (last accepted X-Ts per node).
esp_err_t config_load_ts(uint64_t ts[NODE_COUNT]);
esp_err_t config_store_ts(const uint64_t ts[NODE_COUNT]);
