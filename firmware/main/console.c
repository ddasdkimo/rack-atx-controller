#include "console.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "esp_console.h"
#include "esp_log.h"
#include "esp_system.h"
#include "cJSON.h"
#include "board.h"
#include "config.h"
#include "command.h"
#include "lease.h"
#include "audit.h"

static int cmd_status(int argc, char **argv)
{
    cJSON *o = command_status_json();
    char *txt = cJSON_Print(o);
    printf("%s\n", txt ? txt : "{}");
    free(txt);
    cJSON_Delete(o);
    return 0;
}

static int cmd_press(int argc, char **argv)
{
    if (argc != 4) {
        printf("usage: press <host 1-10> <power|reset> <ms 100-10000>\n");
        return 1;
    }
    int host = atoi(argv[1]);
    button_t b;
    if (strcmp(argv[2], "power") == 0) b = BUTTON_POWER;
    else if (strcmp(argv[2], "reset") == 0) b = BUTTON_RESET;
    else { printf("button must be power|reset\n"); return 1; }
    long ms = atol(argv[3]);
    if (host < 1 || host > HOST_COUNT || ms < PRESS_MIN_MS || ms > PRESS_MAX_MS) {
        printf("out of range\n");
        return 1;
    }
    audit_add("console", "console", (uint8_t)host, argv[2], (uint32_t)ms, "request");
    cmd_result_t r = command_press(-1, (uint8_t)host, b, (uint32_t)ms);
    printf("%s seq=%lu actual_ms=%lu\n", r.code, (unsigned long)r.seq, (unsigned long)r.actual_ms);
    return r.status == CMD_OK ? 0 : 1;
}

static int cmd_lease(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "clear") == 0) {
        lease_force_clear("console");
        printf("lease cleared\n");
        return 0;
    }
    cJSON *o = command_lease_json();
    char *txt = cJSON_PrintUnformatted(o);
    printf("%s\n", txt ? txt : "{}");
    free(txt);
    cJSON_Delete(o);
    return 0;
}

static int cmd_config(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "show") == 0) {
        config_print();
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "save") == 0) {
        esp_err_t e = config_save();
        printf("%s\n", e == ESP_OK ? "saved" : esp_err_to_name(e));
        return e == ESP_OK ? 0 : 1;
    }
    if (argc == 4 && strcmp(argv[1], "set") == 0) {
        esp_err_t e = config_set(argv[2], argv[3]);
        printf("%s\n", e == ESP_OK ? "ok (run 'config save')" : e == ESP_ERR_NOT_FOUND ? "unknown key" : "invalid value");
        return e == ESP_OK ? 0 : 1;
    }
    printf("usage: config show | config set <key> <value> | config save\n");
    return 1;
}

static int cmd_log(int argc, char **argv)
{
    static audit_entry_t tmp[AUDIT_DEPTH];
    size_t n = audit_since(0, tmp, AUDIT_DEPTH);
    for (size_t i = 0; i < n; i++) {
        printf("#%lu t=%lus %s node=%s host=%u %s %lu ms -> %s\n", (unsigned long)tmp[i].seq, (unsigned long)tmp[i].uptime_s,
               tmp[i].kind, tmp[i].node, tmp[i].host, tmp[i].button, (unsigned long)tmp[i].ms, tmp[i].result);
    }
    return 0;
}

static int cmd_reboot(int argc, char **argv)
{
    printf("rebooting\n");
    fflush(stdout);
    esp_restart();
    return 0;
}

esp_err_t console_start(void)
{
    esp_console_repl_t *repl = NULL;
    esp_console_repl_config_t repl_cfg = ESP_CONSOLE_REPL_CONFIG_DEFAULT();
    repl_cfg.prompt = "atx> ";
    repl_cfg.max_cmdline_length = 160;
    esp_console_dev_usb_serial_jtag_config_t hw_cfg = ESP_CONSOLE_DEV_USB_SERIAL_JTAG_CONFIG_DEFAULT();
    esp_err_t err = esp_console_new_repl_usb_serial_jtag(&hw_cfg, &repl_cfg, &repl);
    if (err != ESP_OK) return err;

    const esp_console_cmd_t cmds[] = {
        {.command = "status", .help = "print status JSON", .func = cmd_status},
        {.command = "press", .help = "press <host> <power|reset> <ms>  (needs console_ctl=1)", .func = cmd_press},
        {.command = "lease", .help = "lease | lease clear", .func = cmd_lease},
        {.command = "config", .help = "config show | set <key> <value> | save", .func = cmd_config},
        {.command = "log", .help = "print audit ring", .func = cmd_log},
        {.command = "reboot", .help = "restart", .func = cmd_reboot},
    };
    for (size_t i = 0; i < sizeof(cmds) / sizeof(cmds[0]); i++) {
        ESP_ERROR_CHECK(esp_console_cmd_register(&cmds[i]));
    }
    esp_console_register_help_command();
    return esp_console_start_repl(repl);
}
