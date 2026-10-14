#include "auth.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "mbedtls/md.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "config.h"

static const char *TAG = "auth";
static uint64_t s_last_ts[NODE_COUNT];
static uint64_t s_stored_ts[NODE_COUNT];
static int64_t s_last_flush_us;
static SemaphoreHandle_t s_lock;

#define FLUSH_INTERVAL_US (10LL * 60 * 1000000)

void auth_init(void)
{
    s_lock = xSemaphoreCreateMutex();
    config_load_ts(s_last_ts);
    memcpy(s_stored_ts, s_last_ts, sizeof(s_last_ts));
    s_last_flush_us = esp_timer_get_time();
}

void auth_hmac_hex(const uint8_t *key, size_t key_len, const char *msg, size_t msg_len, char out_hex[65])
{
    uint8_t mac[32];
    const mbedtls_md_info_t *info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
    mbedtls_md_hmac(info, key, key_len, (const uint8_t *)msg, msg_len, mac);
    for (int i = 0; i < 32; i++) {
        sprintf(out_hex + 2 * i, "%02x", mac[i]);
    }
    out_hex[64] = 0;
}

static bool is_hex(const char *s, size_t n)
{
    if (strlen(s) != n) return false;
    for (size_t i = 0; i < n; i++) {
        if (!isxdigit((unsigned char)s[i])) return false;
    }
    return true;
}

static int ct_compare(const char *a, const char *b, size_t n)
{
    unsigned d = 0;
    for (size_t i = 0; i < n; i++) d |= (unsigned)(tolower((unsigned char)a[i]) ^ tolower((unsigned char)b[i]));
    return d;
}

auth_result_t auth_verify(const char *node, const char *ts, const char *nonce, const char *sig,
                          const char *method, const char *path, const char *body, size_t body_len,
                          bool persist, int *node_out)
{
    if (!node || !ts || !nonce || !sig) return AUTH_MISSING_HEADER;
    int idx = config_node_index(node);
    if (idx < 0) return AUTH_BAD_NODE;
    if (node_out) *node_out = idx;
    if (!g_cfg.key_set[idx]) return AUTH_NO_KEY;
    if (!is_hex(nonce, 16)) return AUTH_BAD_NONCE;
    if (!is_hex(sig, 64)) return AUTH_BAD_SIG;
    char *end;
    unsigned long long tsv = strtoull(ts, &end, 10);
    if (*end != 0 || tsv == 0) return AUTH_BAD_TS;

    // message = node \n ts \n nonce \n METHOD \n PATH \n BODY
    size_t mlen = strlen(node) + strlen(ts) + strlen(nonce) + strlen(method) + strlen(path) + body_len + 5;
    char *msg = malloc(mlen + 1);
    if (!msg) return AUTH_BAD_SIG;
    int n = snprintf(msg, mlen + 1, "%s\n%s\n%s\n%s\n%s\n", node, ts, nonce, method, path);
    memcpy(msg + n, body, body_len);
    char hex[65];
    auth_hmac_hex(g_cfg.key[idx], KEY_LEN, msg, (size_t)n + body_len, hex);
    free(msg);
    if (ct_compare(hex, sig, 64) != 0) {
        ESP_LOGW(TAG, "bad signature from node %s", node);
        return AUTH_BAD_SIG;
    }

    auth_result_t r = AUTH_OK;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    if (tsv <= s_last_ts[idx]) {
        r = AUTH_BAD_TS;
    } else {
        s_last_ts[idx] = tsv;
        int64_t now = esp_timer_get_time();
        if (persist || (now - s_last_flush_us) > FLUSH_INTERVAL_US) {
            if (memcmp(s_stored_ts, s_last_ts, sizeof(s_last_ts)) != 0) {
                if (config_store_ts(s_last_ts) == ESP_OK) {
                    memcpy(s_stored_ts, s_last_ts, sizeof(s_last_ts));
                }
            }
            s_last_flush_us = now;
        }
    }
    xSemaphoreGive(s_lock);
    return r;
}

const char *auth_result_str(auth_result_t r)
{
    switch (r) {
    case AUTH_OK: return "ok";
    case AUTH_MISSING_HEADER: return "missing_header";
    case AUTH_BAD_NODE: return "bad_node";
    case AUTH_NO_KEY: return "no_key";
    case AUTH_BAD_TS: return "bad_ts";
    case AUTH_BAD_NONCE: return "bad_nonce";
    default: return "bad_sig";
    }
}
