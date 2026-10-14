#include "policy.h"
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "esp_timer.h"
#include "board.h"
#include "config.h"

#define HIST 16   // >= max_per_hour we expect to allow

static int64_t s_hist[HOST_COUNT + 1][HIST];   // press times (us), 0 = empty
static SemaphoreHandle_t s_lock;

void policy_init(void)
{
    s_lock = xSemaphoreCreateMutex();
    memset(s_hist, 0, sizeof(s_hist));
}

static uint32_t count_last_hour(uint8_t host, int64_t now, int64_t *latest)
{
    uint32_t n = 0;
    *latest = 0;
    for (int i = 0; i < HIST; i++) {
        int64_t t = s_hist[host][i];
        if (t == 0) continue;
        if (now - t < 3600LL * 1000000) n++;
        if (t > *latest) *latest = t;
    }
    return n;
}

policy_result_t policy_check(uint8_t host)
{
    if (host < 1 || host > HOST_COUNT) return POLICY_BAD_HOST;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    int64_t now = esp_timer_get_time(), latest;
    uint32_t n = count_last_hour(host, now, &latest);
    policy_result_t r = POLICY_OK;
    if (latest != 0 && (now - latest) < (int64_t)g_cfg.cooldown_s * 1000000) r = POLICY_COOLDOWN;
    else if (n >= g_cfg.max_per_hour) r = POLICY_HOURLY_LIMIT;
    xSemaphoreGive(s_lock);
    return r;
}

void policy_record(uint8_t host)
{
    if (host < 1 || host > HOST_COUNT) return;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    int64_t now = esp_timer_get_time();
    int slot = 0;
    int64_t oldest = s_hist[host][0];
    for (int i = 1; i < HIST; i++) {
        if (s_hist[host][i] < oldest) { oldest = s_hist[host][i]; slot = i; }
    }
    s_hist[host][slot] = now;
    xSemaphoreGive(s_lock);
}

uint32_t policy_cooldown_left_s(uint8_t host)
{
    if (host < 1 || host > HOST_COUNT) return 0;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    int64_t now = esp_timer_get_time(), latest;
    count_last_hour(host, now, &latest);
    xSemaphoreGive(s_lock);
    if (latest == 0) return 0;
    int64_t left = (int64_t)g_cfg.cooldown_s * 1000000 - (now - latest);
    return left > 0 ? (uint32_t)(left / 1000000) : 0;
}

uint32_t policy_used_last_hour(uint8_t host)
{
    if (host < 1 || host > HOST_COUNT) return 0;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    int64_t latest;
    uint32_t n = count_last_hour(host, esp_timer_get_time(), &latest);
    xSemaphoreGive(s_lock);
    return n;
}

const char *policy_result_str(policy_result_t r)
{
    switch (r) {
    case POLICY_OK: return "ok";
    case POLICY_COOLDOWN: return "cooldown";
    case POLICY_HOURLY_LIMIT: return "hourly_limit";
    default: return "bad_host";
    }
}
