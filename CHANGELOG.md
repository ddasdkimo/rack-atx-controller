# Change log

## B.1 — 2026-10-14

- 完成 10 路主控與免供電分接板 KiCad 原理圖，39+1 頁 PDF；主控 694 個元件、48 種料號，逐項核對 JLC 經濟型代貼及當時庫存。
- 改 ESP32-S3FN8 裸晶＋W5500、有線網路；3×74HC595、20×TLP3122A、20×EL357N、10×LM393、10×隔離供電＋LDO。
- 加入 CMOS TLC555 共用光驅動限時、預設禁能、電源防反接／PPTC、USB 與主機信號 ESD、LED 差動分壓／濾波／遲滯；已定值。
- 接頭改 JST PHD C161672，線束改相配膠殼／端子；外接電源為 5 V 2 A 螺絲端子。配置目標 200×160 mm，仍未佈線。
- 輸出主控／分接板完整 BOM、JLC 四欄 BOM、2／5 片成本試算與來源；分接板建議手焊以節省開單費。
- KiCad ERC 零違規；1915 個實體腳位連線核對、隔離界面檢查及含公差的 LED 門檻分析。尚未實機／SPICE 驗證，五類 footprint 待建立／審核。
- 同步公開網站、3D 控制板、兩台虛擬電腦與接線圖；網頁新增選料、成本及原理圖／BOM 入口。


## A.2 — 2026-10-13

- Clarify that each host adapter is an unpowered wiring splitter; a custom Y harness can replace it.
- Add real candidate connector parts: Molex 43045-1000, 43025-1000 and 43030-0007, plus Belden 9505 cable.
- Record wire-pair colors, spare conductor, separate shield/drain treatment, and assembly quantities.
- Replace the provisional cavity drawing claim with a signal-allocation table pending manufacturer drawing review.
- Revise the conceptual connector shape to a right-angle shrouded header and enlarge the illustrative board envelope to 280 × 220 mm for connector spacing.
- Publish the discussion model with public access and retain source in GitHub.
- Record JLCPCB / PCBA as the preferred fabrication and component-availability workflow, without claiming verified stock or manufacturing readiness.

## A.1 — 2026-10-13

- Initial 10-host centralized hardware architecture and two-host 3D wiring example.
- Preserve original case POWER/RESET switches and power/HDD LEDs through passive adapter traces.
- Define custom 10-pin controller connector: four signal pairs, one host reference, one unconnected pin.
- Plan high-impedance differential LED sensing with an independently powered isolated domain per host.
- Keep board geometry, component candidates and motherboard headers explicitly at concept status.
- Require synchronized circuit, 3D, connector and wiring updates for future revisions.
