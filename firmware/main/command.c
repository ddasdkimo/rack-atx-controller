#include "command.h"
#include <string.h>
#include <stdio.h>
#include "esp_timer.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "board.h"
#include "config.h"
#include "lease.h"
#include "policy.h"
#include "audit.h"
#include "eth.h"

static const char *TAG = "command";

static struct {
    bool valid;
    uint32_t seq;
    char node[4];
    uint8_t host;
    char button[8];
    uint32_t ms;
    char result[24];
    int64_t at_us;
} s_last;

static void set_result(cmd_result_t *r, cmd_status_t st, const char *code)
{
    r->status = st;
    strncpy(r->code, code, sizeof(r->code) - 1);
    r->code[sizeof(r->code) - 1] = 0;
}

cmd_result_t command_press(int node, uint8_t host, button_t button, uint32_t ms)
{
    cmd_result_t r = {0};
    const char *node_name = node >= 0 ? config_node_name(node) : "console";
    const char *btn = button == BUTTON_POWER ? "power" : "reset";

    if (host < 1 || host > HOST_COUNT || ms < PRESS_MIN_MS || ms > PRESS_MAX_MS) {
        set_result(&r, CMD_INVALID, "bad_argument");
        return r;
    }
    if (node >= 0) {
        if (!lease_is_holder(node)) {
            set_result(&r, CMD_FORBIDDEN, "no_lease");
            audit_add("press", node_name, host, btn, ms, "deny:no_lease");
            return r;
        }
        if (g_cfg.node_host[node] != 0 && g_cfg.node_host[node] == host) {
            set_result(&r, CMD_FORBIDDEN, "self_target");
            audit_add("press", node_name, host, btn, ms, "deny:self_target");
            return r;
        }
    } else if (!g_cfg.console_ctl) {
        set_result(&r, CMD_FORBIDDEN, "console_disabled");
        return r;
    }
    policy_result_t p = policy_check(host);
    if (p != POLICY_OK) {
        set_result(&r, CMD_FORBIDDEN, policy_result_str(p));
        char res[24];
        snprintf(res, sizeof(res), "deny:%s", policy_result_str(p));
        audit_add("press", node_name, host, btn, ms, res);
        return r;
    }
    outputs_state_t st = outputs_get_state();
    if (!st.ready) {
        set_result(&r, CMD_HW_FAULT, "outputs_not_ready");
        return r;
    }
    if (st.busy) {
        set_result(&r, CMD_BUSY, "busy");
        return r;
    }
    // Record before acting so a crash mid-press still counts toward the limits after reboot
    // is not possible (RAM only); record first anyway to close the race between two callers.
    policy_record(host);
    uint32_t actual = 0;
    esp_err_t err = outputs_press(host, button, ms, &actual);
    if (err == ESP_ERR_INVALID_STATE) {
        set_result(&r, CMD_BUSY, "busy");
        audit_add("press", node_name, host, btn, ms, "deny:busy");
        return r;
    }
    if (err != ESP_OK) {
        set_result(&r, CMD_HW_FAULT, "hw_fault");
        r.seq = audit_add("press", node_name, host, btn, ms, "hw_fault");
    } else {
        set_result(&r, CMD_OK, "ok");
        r.actual_ms = actual;
        r.seq = audit_add("press", node_name, host, btn, ms, "ok");
    }
    s_last.valid = true;
    s_last.seq = r.seq;
    strncpy(s_last.node, node_name, sizeof(s_last.node) - 1);
    s_last.host = host;
    strncpy(s_last.button, btn, sizeof(s_last.button) - 1);
    s_last.ms = ms;
    strncpy(s_last.result, r.code, sizeof(s_last.result) - 1);
    s_last.at_us = esp_timer_get_time();
    ESP_LOGI(TAG, "press by %s host=%u %s %lu ms -> %s", node_name, host, btn, (unsigned long)ms, r.code);
    return r;
}

cJSON *command_lease_json(void)
{
    cJSON *o = cJSON_CreateObject();
    lease_state_t l = lease_get();
    if (l.holder >= 0) {
        cJSON_AddStringToObject(o, "holder", config_node_name(l.holder));
        cJSON_AddNumberToObject(o, "expires_in_s", (double)lease_expires_in_s());
    } else {
        cJSON_AddNullToObject(o, "holder");
        cJSON_AddNullToObject(o, "expires_in_s");
    }
    return o;
}

cJSON *command_nodes_json(void)
{
    cJSON *o = cJSON_CreateObject();
    for (int i = 0; i < NODE_COUNT; i++) {
        cJSON *n = cJSON_CreateObject();
        cJSON_AddNumberToObject(n, "host", g_cfg.node_host[i]);
        int64_t age = lease_heartbeat_age_s(i);
        if (age < 0) cJSON_AddNullToObject(n, "last_heartbeat_s");
        else cJSON_AddNumberToObject(n, "last_heartbeat_s", (double)age);
        cJSON_AddItemToObject(o, config_node_name(i), n);
    }
    return o;
}

cJSON *command_status_json(void)
{
    cJSON *o = cJSON_CreateObject();
    cJSON_AddStringToObject(o, "fw", FW_VERSION);
    cJSON_AddNumberToObject(o, "uptime_s", (double)(esp_timer_get_time() / 1000000));
    cJSON_AddBoolToObject(o, "link", eth_link_up());
    char ip[16];
    eth_get_ip(ip, sizeof(ip));
    cJSON_AddStringToObject(o, "ip", ip);

    outputs_state_t st = outputs_get_state();
    cJSON *hw = cJSON_CreateObject();
    cJSON_AddBoolToObject(hw, "arm", st.arm);
    cJSON_AddBoolToObject(hw, "oe_enabled", st.oe_enabled);
    cJSON_AddBoolToObject(hw, "busy", st.busy);
    cJSON_AddBoolToObject(hw, "ready", st.ready);
    cJSON_AddBoolToObject(hw, "usb_vbus", gpio_get_level(PIN_USB_VBUS_SENSE) != 0);
    cJSON_AddNumberToObject(hw, "presses", st.presses);
    cJSON_AddItemToObject(o, "hw", hw);

    cJSON_AddItemToObject(o, "lease", command_lease_json());
    cJSON_AddItemToObject(o, "nodes", command_nodes_json());

    cJSON *pol = cJSON_CreateObject();
    cJSON_AddNumberToObject(pol, "cooldown_s", g_cfg.cooldown_s);
    cJSON_AddNumberToObject(pol, "max_per_hour", g_cfg.max_per_hour);
    cJSON_AddNumberToObject(pol, "takeover_s", g_cfg.takeover_s);
    cJSON_AddNumberToObject(pol, "lease_ttl_s", g_cfg.lease_ttl_s);
    cJSON_AddItemToObject(o, "policy", pol);

    if (s_last.valid) {
        cJSON *lc = cJSON_CreateObject();
        cJSON_AddNumberToObject(lc, "seq", s_last.seq);
        cJSON_AddStringToObject(lc, "node", s_last.node);
        cJSON_AddNumberToObject(lc, "host", s_last.host);
        cJSON_AddStringToObject(lc, "button", s_last.button);
        cJSON_AddNumberToObject(lc, "ms", s_last.ms);
        cJSON_AddStringToObject(lc, "result", s_last.result);
        cJSON_AddNumberToObject(lc, "age_s", (double)((esp_timer_get_time() - s_last.at_us) / 1000000));
        cJSON_AddItemToObject(o, "last_command", lc);
    } else {
        cJSON_AddNullToObject(o, "last_command");
    }

    cJSON *hosts = cJSON_CreateArray();
    for (uint8_t h = 1; h <= HOST_COUNT; h++) {
        cJSON *e = cJSON_CreateObject();
        cJSON_AddNumberToObject(e, "host", h);
        cJSON_AddNumberToObject(e, "cooldown_left_s", policy_cooldown_left_s(h));
        cJSON_AddNumberToObject(e, "used_last_hour", policy_used_last_hour(h));
        cJSON_AddItemToArray(hosts, e);
    }
    cJSON_AddItemToObject(o, "hosts", hosts);
    return o;
}
