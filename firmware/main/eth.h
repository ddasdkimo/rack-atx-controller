// W5500 on the shared SPI bus. Creates the SPI bus; outputs_init() must run after eth_init().
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include "esp_err.h"

esp_err_t eth_init(void);
bool eth_link_up(void);
bool eth_has_ip(void);
void eth_get_ip(char *buf, size_t n);
