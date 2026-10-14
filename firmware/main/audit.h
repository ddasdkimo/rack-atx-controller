// Ring buffer of audit entries, readable through GET /v1/log and the console.
#pragma once
#include <stdint.h>
#include <stddef.h>

#define AUDIT_DEPTH 64

typedef struct {
    uint32_t seq;
    uint32_t uptime_s;
    char kind[16];      // press, lease_grant, lease_deny, lease_release, lease_expire, boot, console
    char node[4];
    uint8_t host;
    char button[8];
    uint32_t ms;
    char result[24];
} audit_entry_t;

void audit_init(void);
uint32_t audit_add(const char *kind, const char *node, uint8_t host, const char *button, uint32_t ms, const char *result);
// Copy entries with seq > since into out (oldest first). Returns count.
size_t audit_since(uint32_t since, audit_entry_t *out, size_t max);
uint32_t audit_last_seq(void);
