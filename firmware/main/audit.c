#include "audit.h"
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "esp_timer.h"
#include "esp_log.h"

static audit_entry_t s_ring[AUDIT_DEPTH];
static uint32_t s_seq;
static SemaphoreHandle_t s_lock;

void audit_init(void)
{
    s_lock = xSemaphoreCreateMutex();
    memset(s_ring, 0, sizeof(s_ring));
    s_seq = 0;
}

static void copy_str(char *dst, size_t n, const char *src)
{
    if (!src) src = "";
    strncpy(dst, src, n - 1);
    dst[n - 1] = 0;
}

uint32_t audit_add(const char *kind, const char *node, uint8_t host, const char *button, uint32_t ms, const char *result)
{
    xSemaphoreTake(s_lock, portMAX_DELAY);
    uint32_t seq = ++s_seq;
    audit_entry_t *e = &s_ring[seq % AUDIT_DEPTH];
    e->seq = seq;
    e->uptime_s = (uint32_t)(esp_timer_get_time() / 1000000);
    copy_str(e->kind, sizeof(e->kind), kind);
    copy_str(e->node, sizeof(e->node), node);
    e->host = host;
    copy_str(e->button, sizeof(e->button), button);
    e->ms = ms;
    copy_str(e->result, sizeof(e->result), result);
    xSemaphoreGive(s_lock);
    ESP_LOGI("audit", "#%lu %s node=%s host=%u %s %lu ms -> %s", (unsigned long)seq, e->kind, e->node, host,
             e->button, (unsigned long)ms, e->result);
    return seq;
}

size_t audit_since(uint32_t since, audit_entry_t *out, size_t max)
{
    size_t n = 0;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    uint32_t first = s_seq > AUDIT_DEPTH ? s_seq - AUDIT_DEPTH + 1 : 1;
    if (since + 1 > first) first = since + 1;
    for (uint32_t s = first; s <= s_seq && n < max; s++) {
        out[n++] = s_ring[s % AUDIT_DEPTH];
    }
    xSemaphoreGive(s_lock);
    return n;
}

uint32_t audit_last_seq(void)
{
    return s_seq;
}
