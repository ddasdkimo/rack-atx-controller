# 控制器通訊協定 v1（B.2 硬體）

控制器只有一個 RJ45（W5500）與一個 USB-C（ESP32-S3 內建 USB Serial/JTAG）。網路通道走 HTTP/1.1 + JSON；USB 通道是行文字命令，給實體接線的管理機或維修用。兩個通道共用同一套命令處理與保護規則。

## 1. 角色與原則

- 節點 `A`（主監控）與 `B`（副監控）是十台主機中的兩台，各有一把 32 位元組的共享密鑰與自己的主機編號。
- 控制器是唯一仲裁者：**只有持有租約的節點能下硬體命令**。任何時刻最多一個持有者。
- 一次只執行一個硬體動作；動作同步執行，HTTP 回應在動作完成後才送出。
- 控制器不知道主機開關狀態（B.2 沒有 LED 感測），所有狀態判斷由節點負責。
- 控制器網路斷線時不會自主動作。

## 2. 認證

每個需要認證的請求帶四個標頭：

| 標頭 | 內容 |
|---|---|
| `X-Node` | `A` 或 `B` |
| `X-Ts` | 送出時間，Unix 秒。同一節點必須**嚴格遞增** |
| `X-Nonce` | 16 個十六進位字元，隨機 |
| `X-Sig` | `HMAC-SHA256(key, X-Node + "\n" + X-Ts + "\n" + X-Nonce + "\n" + METHOD + "\n" + PATH + "\n" + BODY)` 的 64 個十六進位小寫字元 |

- `PATH` 不含查詢字串；`BODY` 是原始位元組，GET 時為空字串。
- 控制器記住每個節點最後看到的 `X-Ts`，較小或相同一律拒絕（401）。命令類請求成功後會把該值寫進 NVS，重開機後仍有效；心跳類最多每 10 分鐘寫一次。
- 控制器沒有 RTC，不檢查 `X-Ts` 與真實時間的差距，只檢查單調遞增。節點自己的時鐘倒退會造成 401，此時用較大的值重送即可。
- 密鑰經 USB 主控台設定（`config set key_a <64hex>`），不經網路。

未認證的只有 `GET /v1/ping`。

## 3. HTTP 端點

所有回應都是 JSON。錯誤格式：`{"error":"<code>","detail":"<text>"}`。

| 狀態碼 | 意義 |
|---|---|
| 400 | 參數錯誤 |
| 401 | 認證失敗或重放 |
| 403 | 沒有租約、目標是自己、或策略（冷卻、次數上限）拒絕 |
| 409 | 控制器正在執行另一個動作 |
| 503 | 硬體未就緒（初始化失敗、OE 保持高） |

### GET /v1/ping

無認證。回 `{"fw":"b2-0.1.0","uptime_s":123}`。節點用它判斷控制器是否在線。

### GET /v1/status

```json
{
  "fw": "b2-0.1.0", "uptime_s": 1234, "link": true, "ip": "192.168.10.20",
  "hw": {"arm": false, "oe_enabled": true, "busy": false, "usb_vbus": true},
  "lease": {"holder": "A", "expires_in_s": 41},
  "nodes": {"A": {"host": 1, "last_heartbeat_s": 7}, "B": {"host": 2, "last_heartbeat_s": 9}},
  "policy": {"cooldown_s": 60, "max_per_hour": 6, "takeover_s": 180, "lease_ttl_s": 60},
  "last_command": {"seq": 17, "node": "A", "host": 5, "button": "reset", "ms": 200, "result": "ok", "age_s": 300},
  "hosts": [{"host": 1, "cooldown_left_s": 0, "used_last_hour": 0}, ...]
}
```

`last_heartbeat_s` 是距上次心跳的秒數，從未收到為 `null`。

### POST /v1/heartbeat

Body：`{"node":"A"}`。回 status 的精簡版 `{"lease":{...},"nodes":{...}}`。建議每 20 秒一次。

### POST /v1/lease

Body：`{"node":"A","action":"acquire"|"renew"|"release"}`。

回：`{"granted":true,"holder":"A","expires_in_s":60}` 或 `{"granted":false,"holder":"B","expires_in_s":33,"reason":"held_by_other"}`。

規則：

1. `acquire`：沒有持有者或租約已過期 → 核發，TTL 為 `lease_ttl_s`。
2. 持有者是另一節點且未過期 → 拒絕，`reason: held_by_other`。
3. 持有者是另一節點、租約已過期、但對方最後一次心跳距今小於 `takeover_s` → 拒絕，`reason: holder_recently_alive`。這條把「只是監控程式忘了續約」與「主機真的失聯」分開。
4. `renew` 只接受目前持有者。`release` 只接受目前持有者，立即清空。
5. 核發與釋放都寫入稽核紀錄。

### POST /v1/press

Body：`{"node":"A","host":5,"button":"power"|"reset","ms":200}`。

- `host` 1–10，`ms` 100–10000。長按強制關機就是 `button:"power"` 加 `ms:5000`。
- 必須是租約持有者；`host` 不能是該節點自己的主機（403 `self_target`）。
- 策略：同一主機兩次動作間隔 ≥ `cooldown_s`；一小時內 ≤ `max_per_hour` 次。
- 執行中另一個請求回 409。
- 成功回 `{"ok":true,"seq":18,"host":5,"button":"power","ms":5000,"actual_ms":5003}`。

硬體序列固定為：寫入單一位元並 latch → ARM 拉高（PHOTO_5V 通電，光繼電器閉合）→ 等 `ms` → ARM 拉低 → 寫入全零並 latch → ARM 低保持 50 ms。MC14541B 在約 15 秒後無論如何切斷軌道，韌體上限 10 秒在它之內。

### GET /v1/log?since=<seq>

回最近最多 64 筆稽核紀錄，`seq` 大於 `since` 的部分：

```json
{"entries":[{"seq":18,"uptime_s":1300,"kind":"press","node":"A","host":5,"button":"power","ms":5000,"result":"ok"}, ...]}
```

`kind` 有 `press`、`lease_grant`、`lease_deny`、`lease_release`、`lease_expire`、`boot`、`console`。

## 4. USB 主控台

115200 8N1 的行命令，提示符 `atx> `。沒有認證，因為需要實體接線；硬體命令預設關閉，要 `config set console_ctl 1`。

```
status
press <host> <power|reset> <ms>      需要 console_ctl=1；不需租約，但套用冷卻與次數策略
lease                                顯示租約
lease clear                          強制清空租約（維修用，寫入稽核）
config show
config set <key> <value>
config save
reboot
```

設定鍵：`dhcp`(0/1)、`ip`、`mask`、`gw`、`key_a`、`key_b`（64 hex）、`host_a`、`host_b`（1–10，0 = 無）、`cooldown_s`、`max_per_hour`、`takeover_s`、`lease_ttl_s`、`console_ctl`。

## 5. 節點端建議流程

1. 兩節點每 20 秒 `POST /v1/heartbeat`。A 每 20 秒 `POST /v1/lease` `renew`（第一次 `acquire`）。
2. B 平時只觀察。連續 `takeover_s` 秒到不了 A 時送 `acquire`；被拒就繼續等，核發後才下命令。
3. 對一台主機的硬體重啟序列（由節點組合，控制器不提供組合命令）：`reset` 200 ms → 等 2–3 分鐘 → 仍不通則 `power` 5000 ms → 等 10 秒 → `power` 200 ms → 等 3 分鐘 → 仍不通則停手告警。
4. 任何 401 先檢查時間是否倒退；任何 403 `held_by_other` 表示另一節點正在主導，不要搶。
