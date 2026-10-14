// HMAC-SHA256 request authentication with per-node monotonic timestamps.
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

typedef enum {
    AUTH_OK = 0,
    AUTH_MISSING_HEADER,
    AUTH_BAD_NODE,
    AUTH_NO_KEY,
    AUTH_BAD_TS,        // not strictly increasing
    AUTH_BAD_NONCE,
    AUTH_BAD_SIG,
} auth_result_t;

void auth_init(void);

// Verify. On success the node's timestamp floor advances; persist=true writes it to NVS now
// (use for state-changing commands); otherwise it is flushed at most every 10 minutes.
auth_result_t auth_verify(const char *node, const char *ts, const char *nonce, const char *sig,
                          const char *method, const char *path, const char *body, size_t body_len,
                          bool persist, int *node_out);

const char *auth_result_str(auth_result_t r);
// Compute hex HMAC (for tests / console self-check).
void auth_hmac_hex(const uint8_t *key, size_t key_len, const char *msg, size_t msg_len, char out_hex[65]);
