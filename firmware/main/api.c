#include "api.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include "esp_log.h"
#include "esp_http_server.h"
#include "esp_timer.h"
#include "cJSON.h"
#include "board.h"
#include "config.h"
#include "auth.h"
#include "lease.h"
#include "command.h"
#include "audit.h"

static const char *TAG = "api";
static httpd_handle_t s_server;

static const char *button_tostr(button_t b) { return b == BUTTON_POWER ? "power" : "reset"; }

#define BODY_MAX 512

static esp_err_t send_json(httpd_req_t *req, int status, cJSON *obj)
{
    const char *st = status == 200 ? "200 OK" : status == 400 ? "400 Bad Request" : status == 401 ? "401 Unauthorized"
                   : status == 403 ? "403 Forbidden" : status == 409 ? "409 Conflict" : "503 Service Unavailable";
    httpd_resp_set_status(req, st);
    httpd_resp_set_type(req, "application/json");
    char *txt = cJSON_PrintUnformatted(obj);
    cJSON_Delete(obj);
    esp_err_t err = httpd_resp_sendstr(req, txt ? txt : "{}");
    free(txt);
    return err;
}

static esp_err_t send_error(httpd_req_t *req, int status, const char *code, const char *detail)
{
    cJSON *o = cJSON_CreateObject();
    cJSON_AddStringToObject(o, "error", code);
    cJSON_AddStringToObject(o, "detail", detail ? detail : "");
    return send_json(req, status, o);
}

static bool get_header(httpd_req_t *req, const char *name, char *buf, size_t n)
{
    size_t len = httpd_req_get_hdr_value_len(req, name);
    if (len == 0 || len >= n) return false;
    return httpd_req_get_hdr_value_str(req, name, buf, n) == ESP_OK;
}

// Read body (<= BODY_MAX), returns length or -1.
static int read_body(httpd_req_t *req, char *buf, size_t n)
{
    if (req->content_len >= n) return -1;
    size_t got = 0;
    while (got < req->content_len) {
        int r = httpd_req_recv(req, buf + got, req->content_len - got);
        if (r <= 0) return -1;
        got += (size_t)r;
    }
    buf[got] = 0;
    return (int)got;
}

// Authenticate; on failure sends 401 and returns false.
static bool authenticate(httpd_req_t *req, const char *method, const char *body, size_t body_len, bool persist, int *node)
{
    char n[4], ts[24], nonce[20], sig[72], path[64];
    if (!get_header(req, "X-Node", n, sizeof(n)) || !get_header(req, "X-Ts", ts, sizeof(ts)) ||
        !get_header(req, "X-Nonce", nonce, sizeof(nonce)) || !get_header(req, "X-Sig", sig, sizeof(sig))) {
        send_error(req, 401, "auth", "missing_header");
        return false;
    }
    // path without query string
    strncpy(path, req->uri, sizeof(path) - 1);
    path[sizeof(path) - 1] = 0;
    char *q = strchr(path, '?');
    if (q) *q = 0;
    auth_result_t r = auth_verify(n, ts, nonce, sig, method, path, body ? body : "", body_len, persist, node);
    if (r != AUTH_OK) {
        send_error(req, 401, "auth", auth_result_str(r));
        return false;
    }
    return true;
}

static esp_err_t h_ping(httpd_req_t *req)
{
    cJSON *o = cJSON_CreateObject();
    cJSON_AddStringToObject(o, "fw", FW_VERSION);
    cJSON_AddNumberToObject(o, "uptime_s", (double)(esp_timer_get_time() / 1000000));
    return send_json(req, 200, o);
}

static esp_err_t h_status(httpd_req_t *req)
{
    int node;
    if (!authenticate(req, "GET", "", 0, false, &node)) return ESP_OK;
    return send_json(req, 200, command_status_json());
}

static esp_err_t h_heartbeat(httpd_req_t *req)
{
    char body[BODY_MAX];
    int len = read_body(req, body, sizeof(body));
    if (len < 0) return send_error(req, 400, "bad_request", "body too large");
    int node;
    if (!authenticate(req, "POST", body, (size_t)len, false, &node)) return ESP_OK;
    lease_heartbeat(node);
    cJSON *o = cJSON_CreateObject();
    cJSON_AddItemToObject(o, "lease", command_lease_json());
    cJSON_AddItemToObject(o, "nodes", command_nodes_json());
    return send_json(req, 200, o);
}

static esp_err_t h_lease_get(httpd_req_t *req)
{
    int node;
    if (!authenticate(req, "GET", "", 0, false, &node)) return ESP_OK;
    return send_json(req, 200, command_lease_json());
}

static esp_err_t h_lease_post(httpd_req_t *req)
{
    char body[BODY_MAX];
    int len = read_body(req, body, sizeof(body));
    if (len < 0) return send_error(req, 400, "bad_request", "body too large");
    int node;
    if (!authenticate(req, "POST", body, (size_t)len, true, &node)) return ESP_OK;
    cJSON *j = cJSON_Parse(body);
    const cJSON *action = j ? cJSON_GetObjectItem(j, "action") : NULL;
    if (!cJSON_IsString(action)) {
        cJSON_Delete(j);
        return send_error(req, 400, "bad_request", "action missing");
    }
    lease_heartbeat(node);   // a lease request is also proof of life
    lease_result_t r;
    if (strcmp(action->valuestring, "acquire") == 0) r = lease_acquire(node);
    else if (strcmp(action->valuestring, "renew") == 0) r = lease_renew(node);
    else if (strcmp(action->valuestring, "release") == 0) r = lease_release(node);
    else { cJSON_Delete(j); return send_error(req, 400, "bad_request", "unknown action"); }
    cJSON_Delete(j);
    cJSON *o = cJSON_CreateObject();
    cJSON_AddBoolToObject(o, "granted", r == LEASE_OK);
    lease_state_t l = lease_get();
    if (l.holder >= 0) {
        cJSON_AddStringToObject(o, "holder", config_node_name(l.holder));
        cJSON_AddNumberToObject(o, "expires_in_s", (double)lease_expires_in_s());
    } else {
        cJSON_AddNullToObject(o, "holder");
        cJSON_AddNullToObject(o, "expires_in_s");
    }
    if (r != LEASE_OK) cJSON_AddStringToObject(o, "reason", lease_result_str(r));
    return send_json(req, 200, o);
}

static esp_err_t h_press(httpd_req_t *req)
{
    char body[BODY_MAX];
    int len = read_body(req, body, sizeof(body));
    if (len < 0) return send_error(req, 400, "bad_request", "body too large");
    int node;
    if (!authenticate(req, "POST", body, (size_t)len, true, &node)) return ESP_OK;
    cJSON *j = cJSON_Parse(body);
    const cJSON *host = j ? cJSON_GetObjectItem(j, "host") : NULL;
    const cJSON *button = j ? cJSON_GetObjectItem(j, "button") : NULL;
    const cJSON *ms = j ? cJSON_GetObjectItem(j, "ms") : NULL;
    if (!cJSON_IsNumber(host) || !cJSON_IsString(button) || !cJSON_IsNumber(ms)) {
        cJSON_Delete(j);
        return send_error(req, 400, "bad_request", "host/button/ms required");
    }
    button_t b;
    if (strcmp(button->valuestring, "power") == 0) b = BUTTON_POWER;
    else if (strcmp(button->valuestring, "reset") == 0) b = BUTTON_RESET;
    else { cJSON_Delete(j); return send_error(req, 400, "bad_request", "button must be power|reset"); }
    double hv = host->valuedouble, mv = ms->valuedouble;
    cJSON_Delete(j);
    if (hv < 1 || hv > HOST_COUNT || mv < PRESS_MIN_MS || mv > PRESS_MAX_MS) {
        return send_error(req, 400, "bad_request", "host 1..10, ms 100..10000");
    }
    lease_heartbeat(node);
    cmd_result_t r = command_press(node, (uint8_t)hv, b, (uint32_t)mv);
    if (r.status != CMD_OK) {
        int st = r.status == CMD_INVALID ? 400 : r.status == CMD_FORBIDDEN ? 403 : r.status == CMD_BUSY ? 409 : 503;
        return send_error(req, st, r.code, "");
    }
    cJSON *o = cJSON_CreateObject();
    cJSON_AddBoolToObject(o, "ok", true);
    cJSON_AddNumberToObject(o, "seq", r.seq);
    cJSON_AddNumberToObject(o, "host", hv);
    cJSON_AddStringToObject(o, "button", button_tostr(b));
    cJSON_AddNumberToObject(o, "ms", mv);
    cJSON_AddNumberToObject(o, "actual_ms", r.actual_ms);
    return send_json(req, 200, o);
}

static esp_err_t h_log(httpd_req_t *req)
{
    int node;
    if (!authenticate(req, "GET", "", 0, false, &node)) return ESP_OK;
    uint32_t since = 0;
    char q[32], v[16];
    if (httpd_req_get_url_query_str(req, q, sizeof(q)) == ESP_OK &&
        httpd_query_key_value(q, "since", v, sizeof(v)) == ESP_OK) {
        since = (uint32_t)strtoul(v, NULL, 10);
    }
    static audit_entry_t tmp[AUDIT_DEPTH];
    size_t n = audit_since(since, tmp, AUDIT_DEPTH);
    cJSON *o = cJSON_CreateObject();
    cJSON *arr = cJSON_CreateArray();
    for (size_t i = 0; i < n; i++) {
        cJSON *e = cJSON_CreateObject();
        cJSON_AddNumberToObject(e, "seq", tmp[i].seq);
        cJSON_AddNumberToObject(e, "uptime_s", tmp[i].uptime_s);
        cJSON_AddStringToObject(e, "kind", tmp[i].kind);
        cJSON_AddStringToObject(e, "node", tmp[i].node);
        cJSON_AddNumberToObject(e, "host", tmp[i].host);
        cJSON_AddStringToObject(e, "button", tmp[i].button);
        cJSON_AddNumberToObject(e, "ms", tmp[i].ms);
        cJSON_AddStringToObject(e, "result", tmp[i].result);
        cJSON_AddItemToArray(arr, e);
    }
    cJSON_AddItemToObject(o, "entries", arr);
    return send_json(req, 200, o);
}

esp_err_t api_start(void)
{
    httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
    cfg.server_port = 80;
    cfg.max_uri_handlers = 8;
    cfg.lru_purge_enable = true;
    cfg.recv_wait_timeout = 5;
    cfg.send_wait_timeout = 15;   // a 10 s press is answered synchronously
    cfg.stack_size = 8192;
    esp_err_t err = httpd_start(&s_server, &cfg);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "httpd_start: %s", esp_err_to_name(err));
        return err;
    }
    const httpd_uri_t routes[] = {
        {.uri = "/v1/ping", .method = HTTP_GET, .handler = h_ping},
        {.uri = "/v1/status", .method = HTTP_GET, .handler = h_status},
        {.uri = "/v1/heartbeat", .method = HTTP_POST, .handler = h_heartbeat},
        {.uri = "/v1/lease", .method = HTTP_GET, .handler = h_lease_get},
        {.uri = "/v1/lease", .method = HTTP_POST, .handler = h_lease_post},
        {.uri = "/v1/press", .method = HTTP_POST, .handler = h_press},
        {.uri = "/v1/log", .method = HTTP_GET, .handler = h_log},
    };
    for (size_t i = 0; i < sizeof(routes) / sizeof(routes[0]); i++) {
        ESP_ERROR_CHECK(httpd_register_uri_handler(s_server, &routes[i]));
    }
    ESP_LOGI(TAG, "listening on :80");
    return ESP_OK;
}
