// Per-host cooldown and hourly limits, enforced by the controller regardless of the caller.
#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef enum { POLICY_OK = 0, POLICY_COOLDOWN, POLICY_HOURLY_LIMIT, POLICY_BAD_HOST } policy_result_t;

void policy_init(void);
policy_result_t policy_check(uint8_t host);
void policy_record(uint8_t host);
uint32_t policy_cooldown_left_s(uint8_t host);
uint32_t policy_used_last_hour(uint8_t host);
const char *policy_result_str(policy_result_t r);
