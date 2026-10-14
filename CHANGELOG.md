# Change log

## 回到十路整合板 — 2026-10-14

- 依使用者決定，以一片控制十台主機的 B.1／S.1 為目前方向，P.0 拆板研究暫停並保留。
- 主頁、BOM 與研究頁同步標示：S.1 尚未佈線（0 條走線），兩層配置不是製造完成版。

## P.0 試作方向 — 2026-10-14

- 依使用者新策略，下一輪用現成 ESP32；只驗證控制器與被動轉接板，暫不做 LED 感測及自製網路主控。
- 評估一片雙主機控制模組與兩片轉接板以郵票孔混拼，跨分板處不接任何銅線；保留 TLP3122A。
- 新增拼板／分板後立體架構示意及 JLC Economic／混拼費用說明。這是可行性規劃，沒有 P.0 生產檔或正式 BOM。
- B.1／S.1 的原理圖、BOM 和配置留作比較基準，不冒充新試作版本。
- 新增 P.0 二／五片拼板成本模型；100×100 mm、兩種設計、5 片裸板網頁試算 $14.26。五片零件估 $36.91，SMT 代貼／通孔自焊 $83.11，全焊 $94.40–103.61，運稅等另計。

## S.1 配置研究（B.1 電路不變）— 2026-10-14

- 新增 KiCad 160×110 mm、兩層配置草稿與 694 個佔位；五類 52 個外框不含焊盤，沒有製造／DRC 放行。
- 同步公開 3D、兩台 PC 線束起點、尺寸及文件；主機端訊號分配不變。
- 實際 JLC 網頁比較原尺寸／縮板、兩／四層。候選 5 片裸板 $14；零件 $224.27；全焊好估 $336.30–355.75，不含運稅等追加。
- 記錄一般交期、Economic、不加急與可等較便宜物流的採購偏好。
- 新增可讀 BOM 成本檢視，將單片與五片總價分清楚。
- 補充 TLP3122A 替代方案與 B0505S 隔離電源用途；列為待驗證的成本研究，未更換 B.1 原理圖或有效 BOM。


## B.1 價目表更新 — 2026-10-14

- 將價格拆成「裸 PCB＋零件，自己組裝」及「工廠全部焊好的主控板」，並列整批製作合計與平均每片。
- 加入 JLC 公開估價器的 5 片四層 PCB $50.60 紀錄；2 片成板方案全額承擔 5 片裸板費並留 3 片空板。
- 列出代工費明細；運費、稅金、耗損／MOQ 和工藝追加保留待報價，不當成零費用或已含在到手總價。
- 同步成本模型、公開 3D 討論網頁與文件；硬體電路、BOM 料號及機構配置不變。

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
