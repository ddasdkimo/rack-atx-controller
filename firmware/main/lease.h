// Lease arbitration and heartbeat tracking. The controller is the only arbiter.
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "config.h"

typedef enum {
    LEASE_OK = 0,
    LEASE_HELD_BY_OTHER,
    LEASE_HOLDER_RECENTLY_ALIVE,
    LEASE_NOT_HOLDER,
    LEASE_BAD_NODE,
} lease_result_t;

typedef struct {
    int holder;              // node index or -1
    int prev_holder;         // node whose lease expired most recently, -1 after a voluntary release
    int64_t expires_us;      // esp_timer time; valid when holder >= 0
    int64_t last_heartbeat_us[NODE_COUNT];   // 0 = never
} lease_state_t;

void lease_init(void);
void lease_heartbeat(int node);
lease_result_t lease_acquire(int node);
lease_result_t lease_renew(int node);
lease_result_t lease_release(int node);
void lease_force_clear(const char *who);     // console maintenance
bool lease_is_holder(int node);              // also expires stale leases
lease_state_t lease_get(void);
const char *lease_result_str(lease_result_t r);
int64_t lease_expires_in_s(void);            // -1 if none
int64_t lease_heartbeat_age_s(int node);     // -1 if never
