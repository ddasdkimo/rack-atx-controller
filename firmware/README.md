# B.2 控制器韌體（ESP-IDF）

ESP32-S3FN8 + W5500 的控制器韌體：十台主機各兩個乾接點（POWER、RESET），網路 HTTP API 與 USB 主控台。協定在 [PROTOCOL.md](PROTOCOL.md)。與硬體的對應全部集中在 `main/board.h`，來源是 `hardware/circuit.json` 的 B.2 版本。

**狀態：依 B.2 原理圖撰寫，ESP-IDF v5.3 編譯通過，尚未在實體板上執行。** 腳位、595 鏈結順序、ARM 極性都要在第一片板子上用示波器或 LED 確認。

## 硬體對應

| 訊號 | GPIO | 行為 |
|---|---|---|
| TIMER_ARM | 4 | 高電位：釋放 MC14541B 的 MR 並開啟 Q200 閘極，PHOTO_5V 通電；低電位立即斷電。硬體約 15 秒自動切斷 |
| OUT_OE_N | 6 | 74HC595 輸出致能，低有效；開機先清零再拉低 |
| OUT_LATCH | 7 | 74HC595 RCLK，每次完整 24 位元後脈衝一次 |
| SPI SCK／MOSI／MISO | 39／40／41 | 與 W5500 共用；595 沒有 CS，寫 frame 時鎖住匯流排 |
| ETH_CS_N／RST_N／INT_N | 42／47／48 | W5500 |
| USB_VBUS_SENSE | 33 | 只回報 |

595 鏈：MOSI → U4（DRV_01–08）→ U5（DRV_09–16）→ U6（DRV_17–20）。主機 h 的 POWER 是 DRV_(2h−1)，RESET 是 DRV_(2h)。線上順序 U6、U5、U4，MSB 先送，裝置內 bit0 = QA。

按鍵序列（`outputs_press`）：寫入單一位元並 latch → ARM 高 → 等 100–10000 ms（每秒餵 watchdog）→ ARM 低 → 寫入全零並 latch → ARM 低 50 ms。位元寫入時軌道尚未通電，所以 NPN 導通不會產生 LED 電流。

## 模組

| 檔案 | 職責 |
|---|---|
| `outputs.c` | 595 frame 與 ARM 序列，一次一個動作，失敗時進入安全狀態（OE 高） |
| `eth.c` | W5500、靜態 IP 或 DHCP、連線狀態 |
| `auth.c` | HMAC-SHA256、每節點單調遞增時間戳、NVS 持久化 |
| `lease.c` | 租約、心跳、接手規則 |
| `policy.c` | 每主機冷卻與每小時上限 |
| `command.c` | HTTP 與主控台共用的命令層與狀態 JSON |
| `api.c` | esp_http_server 端點 |
| `console.c` | USB Serial/JTAG 主控台 |
| `config.c` | NVS 設定 |
| `audit.c` | 64 筆稽核環形緩衝 |

## 建置與燒錄

```
. ~/esp/esp-idf/export.sh
cd firmware
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/cu.usbmodem* flash monitor
```

## 首次設定（USB 主控台）

```
config set dhcp 0
config set ip 192.168.10.20
config set mask 255.255.255.0
config set gw 192.168.10.1
config set key_a <64 hex>        # openssl rand -hex 32
config set key_b <64 hex>
config set host_a 1               # 節點 A 是第幾台主機；它不能對自己下命令
config set host_b 2
config save
reboot
```

`tools/atxctl.py` 是只用標準函式庫的參考客戶端，可用來測試簽章與各端點：

```
export ATX_URL=http://192.168.10.20 ATX_NODE=A ATX_KEY=<64 hex>
python3 tools/atxctl.py ping
python3 tools/atxctl.py lease acquire
python3 tools/atxctl.py press 5 reset 200
```

## 上板驗證清單

1. 不接任何主機線，上電後量 PHOTO_5V 應為 0 V，OE_N 先高後低。
2. 主控台 `config set console_ctl 1`，`press 1 power 500`：PHOTO_5V 應在 ARM 高期間為 5 V，J01 pin 1–2 間用三用電表應在 500 ms 內導通，其餘接頭不導通。
3. `press 10 reset 500` 驗證鏈尾（U6 QB）。
4. `press 1 power 10000`：確認 10 秒後釋放；再把 `PRESS_MAX_MS` 暫改 20000 做一次，確認硬體在約 15 秒切斷（測完改回）。
5. 網路：`atxctl.py ping`、`lease acquire`、`press`；重送同一請求應得 401 `bad_ts`。
6. 拔網路線：`status` 的 `link` 應為 false，控制器不得自主動作。
