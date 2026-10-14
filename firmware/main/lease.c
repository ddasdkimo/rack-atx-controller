#include "lease.h"
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "esp_timer.h"
#include "audit.h"

static lease_state_t s;
static SemaphoreHandle_t s_lock;

static int64_t now_us(void) { return esp_timer_get_time(); }

void lease_init(void)
{
    s_lock = xSemaphoreCreateMutex();
    memset(&s, 0, sizeof(s));
    s.holder = -1;
    s.prev_holder = -1;
}

// Caller holds the lock.
static void expire_if_stale(void)
{
    if (s.holder >= 0 && now_us() >= s.expires_us) {
        audit_add("lease_expire", config_node_name(s.holder), 0, "", 0, "ttl");
        s.prev_holder = s.holder;
        s.holder = -1;
    }
}

void lease_heartbeat(int node)
{
    if (node < 0 || node >= NODE_COUNT) return;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    s.last_heartbeat_us[node] = now_us();
    xSemaphoreGive(s_lock);
}

lease_result_t lease_acquire(int node)
{
    if (node < 0 || node >= NODE_COUNT) return LEASE_BAD_NODE;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    expire_if_stale();
    lease_result_t r = LEASE_OK;
    if (s.holder == node) {
        s.expires_us = now_us() + (int64_t)g_cfg.lease_ttl_s * 1000000;
    } else if (s.holder >= 0) {
        r = LEASE_HELD_BY_OTHER;
    } else {
        // No live lease. If the previous holder was the other node and it still heartbeats,
        // the lease merely lapsed (monitor forgot to renew); refuse a takeover so a healthy
        // primary is not displaced.
        int other = node == 0 ? 1 : 0;
        int64_t hb = s.last_heartbeat_us[other];
        if (s.prev_holder == other && hb != 0 && (now_us() - hb) < (int64_t)g_cfg.takeover_s * 1000000) {
            r = LEASE_HOLDER_RECENTLY_ALIVE;
        } else {
            s.holder = node;
            s.expires_us = now_us() + (int64_t)g_cfg.lease_ttl_s * 1000000;
        }
    }
    xSemaphoreGive(s_lock);
    audit_add(r == LEASE_OK ? "lease_grant" : "lease_deny", config_node_name(node), 0, "acquire", 0, lease_result_str(r));
    return r;
}

lease_result_t lease_renew(int node)
{
    if (node < 0 || node >= NODE_COUNT) return LEASE_BAD_NODE;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    expire_if_stale();
    lease_result_t r;
    if (s.holder == node) {
        s.expires_us = now_us() + (int64_t)g_cfg.lease_ttl_s * 1000000;
        r = LEASE_OK;
    } else if (s.holder >= 0) {
        r = LEASE_HELD_BY_OTHER;
    } else {
        r = LEASE_NOT_HOLDER;
    }
    xSemaphoreGive(s_lock);
    return r;
}

lease_result_t lease_release(int node)
{
    if (node < 0 || node >= NODE_COUNT) return LEASE_BAD_NODE;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    expire_if_stale();
    lease_result_t r = (s.holder == node) ? LEASE_OK : LEASE_NOT_HOLDER;
    if (r == LEASE_OK) { s.holder = -1; s.prev_holder = -1; }   // voluntary release: other node may acquire at once
    xSemaphoreGive(s_lock);
    audit_add("lease_release", config_node_name(node), 0, "", 0, lease_result_str(r));
    return r;
}

void lease_force_clear(const char *who)
{
    xSemaphoreTake(s_lock, portMAX_DELAY);
    s.holder = -1;
    s.prev_holder = -1;
    xSemaphoreGive(s_lock);
    audit_add("lease_release", who ? who : "console", 0, "force", 0, "ok");
}

bool lease_is_holder(int node)
{
    xSemaphoreTake(s_lock, portMAX_DELAY);
    expire_if_stale();
    bool ok = (s.holder == node && node >= 0);
    xSemaphoreGive(s_lock);
    return ok;
}

lease_state_t lease_get(void)
{
    xSemaphoreTake(s_lock, portMAX_DELAY);
    expire_if_stale();
    lease_state_t c = s;
    xSemaphoreGive(s_lock);
    return c;
}

const char *lease_result_str(lease_result_t r)
{
    switch (r) {
    case LEASE_OK: return "ok";
    case LEASE_HELD_BY_OTHER: return "held_by_other";
    case LEASE_HOLDER_RECENTLY_ALIVE: return "holder_recently_alive";
    case LEASE_NOT_HOLDER: return "not_holder";
    default: return "bad_node";
    }
}

int64_t lease_expires_in_s(void)
{
    lease_state_t c = lease_get();
    if (c.holder < 0) return -1;
    int64_t d = (c.expires_us - now_us()) / 1000000;
    return d < 0 ? 0 : d;
}

int64_t lease_heartbeat_age_s(int node)
{
    if (node < 0 || node >= NODE_COUNT) return -1;
    lease_state_t c = lease_get();
    if (c.last_heartbeat_us[node] == 0) return -1;
    return (now_us() - c.last_heartbeat_us[node]) / 1000000;
}
