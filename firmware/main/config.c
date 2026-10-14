#include "config.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"

static const char *TAG = "config";
static const char *NS = "atx";
app_config_t g_cfg;

static const char *NODE_NAMES[NODE_COUNT] = {"A", "B"};

int config_node_index(const char *name)
{
    if (!name) return -1;
    for (int i = 0; i < NODE_COUNT; i++) {
        if (strcmp(name, NODE_NAMES[i]) == 0) return i;
    }
    return -1;
}

const char *config_node_name(int idx)
{
    return (idx >= 0 && idx < NODE_COUNT) ? NODE_NAMES[idx] : "?";
}

static void set_defaults(void)
{
    memset(&g_cfg, 0, sizeof(g_cfg));
    g_cfg.dhcp = true;
    strcpy(g_cfg.ip, "192.168.10.20");
    strcpy(g_cfg.mask, "255.255.255.0");
    strcpy(g_cfg.gw, "192.168.10.1");
    g_cfg.cooldown_s = 60;
    g_cfg.max_per_hour = 6;
    g_cfg.takeover_s = 180;
    g_cfg.lease_ttl_s = 60;
    g_cfg.console_ctl = false;
}

static int hex_nibble(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    c = (char)tolower((unsigned char)c);
    if (c >= 'a' && c <= 'f') return 10 + c - 'a';
    return -1;
}

static bool parse_hex(const char *s, uint8_t *out, size_t n)
{
    if (strlen(s) != 2 * n) return false;
    for (size_t i = 0; i < n; i++) {
        int hi = hex_nibble(s[2 * i]), lo = hex_nibble(s[2 * i + 1]);
        if (hi < 0 || lo < 0) return false;
        out[i] = (uint8_t)((hi << 4) | lo);
    }
    return true;
}

static bool valid_ipv4(const char *s)
{
    unsigned a, b, c, d;
    char tail;
    if (sscanf(s, "%u.%u.%u.%u%c", &a, &b, &c, &d, &tail) != 4) return false;
    return a < 256 && b < 256 && c < 256 && d < 256 && strlen(s) < 16;
}

esp_err_t config_load(void)
{
    set_defaults();
    nvs_handle_t h;
    esp_err_t err = nvs_open(NS, NVS_READONLY, &h);
    if (err == ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGW(TAG, "no stored config, using defaults");
        return ESP_OK;
    }
    if (err != ESP_OK) return err;
    uint8_t u8;
    uint32_t u32;
    size_t len;
    if (nvs_get_u8(h, "dhcp", &u8) == ESP_OK) g_cfg.dhcp = u8;
    len = sizeof(g_cfg.ip);   nvs_get_str(h, "ip", g_cfg.ip, &len);
    len = sizeof(g_cfg.mask); nvs_get_str(h, "mask", g_cfg.mask, &len);
    len = sizeof(g_cfg.gw);   nvs_get_str(h, "gw", g_cfg.gw, &len);
    for (int i = 0; i < NODE_COUNT; i++) {
        char k[8];
        snprintf(k, sizeof(k), "key_%d", i);
        len = KEY_LEN;
        if (nvs_get_blob(h, k, g_cfg.key[i], &len) == ESP_OK && len == KEY_LEN) g_cfg.key_set[i] = true;
        snprintf(k, sizeof(k), "host_%d", i);
        if (nvs_get_u8(h, k, &u8) == ESP_OK) g_cfg.node_host[i] = u8;
    }
    if (nvs_get_u32(h, "cooldown_s", &u32) == ESP_OK) g_cfg.cooldown_s = u32;
    if (nvs_get_u32(h, "max_ph", &u32) == ESP_OK) g_cfg.max_per_hour = u32;
    if (nvs_get_u32(h, "takeover_s", &u32) == ESP_OK) g_cfg.takeover_s = u32;
    if (nvs_get_u32(h, "lease_ttl", &u32) == ESP_OK) g_cfg.lease_ttl_s = u32;
    if (nvs_get_u8(h, "console_ctl", &u8) == ESP_OK) g_cfg.console_ctl = u8;
    nvs_close(h);
    return ESP_OK;
}

esp_err_t config_save(void)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(NS, NVS_READWRITE, &h);
    if (err != ESP_OK) return err;
    nvs_set_u8(h, "dhcp", g_cfg.dhcp);
    nvs_set_str(h, "ip", g_cfg.ip);
    nvs_set_str(h, "mask", g_cfg.mask);
    nvs_set_str(h, "gw", g_cfg.gw);
    for (int i = 0; i < NODE_COUNT; i++) {
        char k[8];
        if (g_cfg.key_set[i]) {
            snprintf(k, sizeof(k), "key_%d", i);
            nvs_set_blob(h, k, g_cfg.key[i], KEY_LEN);
        }
        snprintf(k, sizeof(k), "host_%d", i);
        nvs_set_u8(h, k, g_cfg.node_host[i]);
    }
    nvs_set_u32(h, "cooldown_s", g_cfg.cooldown_s);
    nvs_set_u32(h, "max_ph", g_cfg.max_per_hour);
    nvs_set_u32(h, "takeover_s", g_cfg.takeover_s);
    nvs_set_u32(h, "lease_ttl", g_cfg.lease_ttl_s);
    nvs_set_u8(h, "console_ctl", g_cfg.console_ctl);
    err = nvs_commit(h);
    nvs_close(h);
    return err;
}

esp_err_t config_set(const char *key, const char *value)
{
    if (!key || !value) return ESP_ERR_INVALID_ARG;
    if (strcmp(key, "dhcp") == 0) { g_cfg.dhcp = atoi(value) != 0; return ESP_OK; }
    if (strcmp(key, "ip") == 0 || strcmp(key, "mask") == 0 || strcmp(key, "gw") == 0) {
        if (!valid_ipv4(value)) return ESP_ERR_INVALID_ARG;
        strcpy(strcmp(key, "ip") == 0 ? g_cfg.ip : strcmp(key, "mask") == 0 ? g_cfg.mask : g_cfg.gw, value);
        return ESP_OK;
    }
    if (strcmp(key, "key_a") == 0 || strcmp(key, "key_b") == 0) {
        int i = key[4] - 'a';
        if (!parse_hex(value, g_cfg.key[i], KEY_LEN)) return ESP_ERR_INVALID_ARG;
        g_cfg.key_set[i] = true;
        return ESP_OK;
    }
    if (strcmp(key, "host_a") == 0 || strcmp(key, "host_b") == 0) {
        int v = atoi(value);
        if (v < 0 || v > 10) return ESP_ERR_INVALID_ARG;
        g_cfg.node_host[key[5] - 'a'] = (uint8_t)v;
        return ESP_OK;
    }
    long v = strtol(value, NULL, 10);
    if (v < 0) return ESP_ERR_INVALID_ARG;
    if (strcmp(key, "cooldown_s") == 0) { g_cfg.cooldown_s = (uint32_t)v; return ESP_OK; }
    if (strcmp(key, "max_per_hour") == 0) { g_cfg.max_per_hour = (uint32_t)v; return ESP_OK; }
    if (strcmp(key, "takeover_s") == 0) { g_cfg.takeover_s = (uint32_t)v; return ESP_OK; }
    if (strcmp(key, "lease_ttl_s") == 0) { if (v < 10 || v > 3600) return ESP_ERR_INVALID_ARG; g_cfg.lease_ttl_s = (uint32_t)v; return ESP_OK; }
    if (strcmp(key, "console_ctl") == 0) { g_cfg.console_ctl = v != 0; return ESP_OK; }
    return ESP_ERR_NOT_FOUND;
}

void config_print(void)
{
    printf("dhcp=%d ip=%s mask=%s gw=%s\n", g_cfg.dhcp, g_cfg.ip, g_cfg.mask, g_cfg.gw);
    for (int i = 0; i < NODE_COUNT; i++) {
        printf("node %s: key=%s host=%u\n", config_node_name(i), g_cfg.key_set[i] ? "set" : "MISSING", g_cfg.node_host[i]);
    }
    printf("cooldown_s=%lu max_per_hour=%lu takeover_s=%lu lease_ttl_s=%lu console_ctl=%d\n",
           (unsigned long)g_cfg.cooldown_s, (unsigned long)g_cfg.max_per_hour, (unsigned long)g_cfg.takeover_s,
           (unsigned long)g_cfg.lease_ttl_s, g_cfg.console_ctl);
}

esp_err_t config_load_ts(uint64_t ts[NODE_COUNT])
{
    memset(ts, 0, sizeof(uint64_t) * NODE_COUNT);
    nvs_handle_t h;
    if (nvs_open(NS, NVS_READONLY, &h) != ESP_OK) return ESP_OK;
    for (int i = 0; i < NODE_COUNT; i++) {
        char k[8];
        snprintf(k, sizeof(k), "ts_%d", i);
        nvs_get_u64(h, k, &ts[i]);
    }
    nvs_close(h);
    return ESP_OK;
}

esp_err_t config_store_ts(const uint64_t ts[NODE_COUNT])
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(NS, NVS_READWRITE, &h);
    if (err != ESP_OK) return err;
    for (int i = 0; i < NODE_COUNT; i++) {
        char k[8];
        snprintf(k, sizeof(k), "ts_%d", i);
        nvs_set_u64(h, k, ts[i]);
    }
    err = nvs_commit(h);
    nvs_close(h);
    return err;
}
