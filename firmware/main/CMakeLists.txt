idf_component_register(
    SRCS "app_main.c" "outputs.c" "config.c" "audit.c" "lease.c" "auth.c" "policy.c"
         "command.c" "eth.c" "api.c" "console.c"
    INCLUDE_DIRS "."
    REQUIRES driver esp_eth esp_netif esp_event esp_http_server nvs_flash json mbedtls
             esp_timer console esp_hw_support
)
