# 2026-10-15 R.3 加工檔與實際裸板試算

- 主板補上 J01～J10、5V 正負與 USB/LAN 絲印；銅箔及電氣接法不變，DRC／未連接重檢為 0。3D 與布局圖同步呈現。
- 產生兩板 Gerber／分開 PTH/NPTH 鑽孔／BOM／CPL；獨立 CAM 解析核對 380 圓孔、4 USB 槽孔、轉接板 20 孔，以及 300／6 顆零件座標。
- 建立加工檔雜湊與貼片方向備註，特別註明 KENTO LED 原廠腳號與 KiCad K/A 編號不同，工廠預覽必須按正負極確認。
- 實際上傳 Gerber 後，JLC 五片裸板試算為 US$9.30（HASL 蓋油）、27.20（ENIG 蓋油）、82.99（ENIG 填孔蓋銅）；三種工藝均尚未取得本板 QFN DFM 接受。完整 PCBA 報價仍待服務條款確認及料件預覽。
- 指定 CLI 完成第二輪固定包複查：81 個檔案雜湊、加工層、孔位、BOM/CPL、極性及絲印一致，未找到離線阻擋項。固定審閱副本漏帶的自訂封裝庫已補齊，原始 Git 倉庫本來就有；補庫後一般 ERC／DRC 都為 0。
- 審閱包不代表製造放行，尚未下單或付款。

# 2026-10-15 R.3 佈線修正與同步

- 保留 B.2 POWER/RESET 電氣接法與 100×110 mm 兩層外框；實際走線 3,855 段、252 個 via、22 個地銅區，主板及轉接板 DRC／原生未連接皆為 0。
- USB 主幹改正面成對走線；重排 Ethernet 終端與去耦，八個零件改 0402。MCU 裸焊盤加入九個地孔、16 個避孔錫膏窗。
- 同一位 CLI 複查者獨立核對固定版本，確認目前沒有阻擋打樣的佈線幾何問題。局部接頭扇出跨線及 C34 焊盤起點參考面缺口列為已審閱的試作限制；此結果不等於板廠 DFM 或實板驗證。
- 原理圖、BOM、native PCB、3D 與公開視圖同步為 R.3，S.3 舊配置與 R.2 走線保留。五片主板零件估 US$162.38；PCB、運稅、耗損及製程追加仍待正式報價。
- 保留製造阻擋項：QFN 孔處理／鋼網工藝、完整 CAM/CPL 檢查、JLCPCB Economic 報價與最終固定送件包複查。未下單，未宣告可量產。

# 2026-10-15 送件前工程檢查接續

- 對照 JST 原廠 PHD 圖面核對全部十個 S10B-PHDSS：2 mm 孔距、8 mm 孔列跨度、0.75 mm 孔徑、腳號與 net 對應相符；插接朝板外，11.9 mm 本體寬度下相鄰淨距 6.1 mm。此為 PCB 名目幾何與插接方向檢查，機箱開孔、線束彎折及實際插拔仍待確認。

- 新增可重跑的獨立 CAM 解析：局部 QFN 試稿的 16 個錫膏窗與九個 0.3 mm 鑽孔不相交，保守方窗邊界最小間隙 0.027 mm；附輸出雜湊與實際 CAM 疊圖。同一位 CLI 複查者以另一套解析方式確認。頂層 EP 露孔、底層蓋油仍不能當作填孔，吸錫／空洞與製程待板廠確認。
- USB／MDI 局部試稿正補低速訊號，尚未取代正式 R.2。RX 終端共同端縮短並獲中途複查確認；新增四個 JLC 候選料號的庫存與價格快照，其中 C318580 為 Extended，報價須計額外上料費。

- 新增 QFN 製程稽核：正式 R.2 的 U2 中央 4×4 mm 焊盤內沒有接地導通孔，且 3V3、SPI_MOSI、USB_VBUS_SENSE 底層走線穿過其下方。列為修版阻擋項；局部試版加入九孔與避孔錫膏窗，尚未併入正式板。
- 確認 JLCPCB 公開的控阻服務從四層開始；兩層方案的 USB／MDI 阻抗目標不能寫成板廠保證。表面處理、鋼網厚度與 QFN 孔處理須納入正式報價及 DFM。
- 高速區中途複查建議保留 R.2 核心位置，採局部重排與重新配對；整區平移的 S.4 試稿雖無 courtyard 重疊，仍因終端、去耦與計時器高阻節點距離變差而未採用。
- 已收到 CLI 初審交接；初審不是製造放行。後續固定送件候選仍須由同一位複查者獨立檢查。
- 對照 Toshiba 原廠 4pin SO6 land-pattern 圖並逐一量測原生 PCB 的 20 個 TLP3122A footprint：0.8×1.2 mm 焊盤、2.54 mm 節距、6.3 mm 列中心距相符，附可重跑的 pre-release-audit.py 與來源。
- 明確列出未結案項：ETH_TXP/TXN 各有兩個訊號 via，RJ_RD_P/N 各有一個，USB 亦尚待差分對、參考面及阻抗確認。局部試改未通過檢查，不取代現行 R.2。
- 計時器 ±25% 仍是模擬假設；原廠不同測試條件的個別變化率不能直接當作完整組合條件的保證範圍。
- 原理圖、BOM、正式 PCB 與公開 3D 沒有改版；製造檔、正式報價與最終複查仍待完成。

# 2026-10-15 R.2 獨立複核

- 以 kicad-cli 獨立重跑 R.2 DRC（0 違規、0 未連線）、B.2 ERC（0）與原理圖一致性（只有 LCSC 欄位未同步、NC 腳位與四個固定孔，無電氣差異）；重跑 run-b2.py 得到相同的 11.26–21.46 s。
- 核對 MC14541B datasheet 真值表：Q/Q̄ Select=1 為「重置後輸出初始為高」，與 B.2 接法及模擬模型一致；振盪器規格 ±2% 溫度／±20% 供電／±3% 製程，模擬的 ±25% 假設可涵蓋。
- 新增 scripts/audit-r2-placement.py 與 hardware/validation/r2-placement-audit.json：304 個 footprint 全在正面、封裝指派與 circuit.json 一致、courtyard 無重疊、最小 courtyard 間距 0.23 mm（45 對）、十個 JST 接頭 18 mm 節距留 5 mm 間隔、固定孔到最近零件 courtyard 4 mm 以上。TLP3122A 自訂焊盤尚未與 Toshiba 建議 land pattern 圖面逐一比對。

# 2026-10-14 — B.2 circuit / S.3 placement / R.2 routed prototype candidate

- Added an annotated status-LED position map from native placement, explicitly showing the mirrored lower bank; no electrical or PCB position changes.

- Removed host LED sensing and isolated supplies; retained 20 POWER/RESET photorelays and independent host-local button ESD references. Original buttons connect in parallel; original LEDs remain on the motherboard.
- Added 20 red drive-state LEDs, green 3V3/EN LEDs and labeled per-host PWR/RST positions. Existing RJ45 LINK/ACT remains. LEDs indicate drive state, not physical contact or host power feedback.
- Fixed timer/startup behavior: MC14541B, C0G counted timeout, independent ARM gate, GPIO4/6/7 and external defaults. Native XML/ERC verifies 300 controller parts/956 pins and 6 adapter parts/20 pins. ERC zero on both.
- User authorized completing routing after placement checks. 47 placement-distance checks passed. R.2 controller: 100×110 mm, 2 layers, 2,754 segments, 185 vias, 22 ground zones. Passive adapter: 26×34 mm, 30 segments, no vias. Both native connectivity and configured DRC report zero.
- Crystal and buck critical routes use F.Cu without vias. Committed rule profile: 0.15 mm minimum track/clearance, 0.6/0.3 mm vias, 1 mm host-domain functional separation, 1 mm silk text/0.15 mm strokes. Custom LED footprints preserve KiCad copper lands and adjust only silk/fab artwork.
- Re-ran B.2 behavioral simulation: 16 corners plus 9 cases pass, including indicator loads. 11.26–21.46 s is an assumed model stress range, not a measured or vendor-guaranteed range.
- Updated native schematics/PDFs/BOM, 3D actual copper and passive adapter geometry, indicator demonstration, public routing view and documentation. Five-board parts US$162.53; new bare PCB quote remains unknown.
- No manufacturing release: USB/Ethernet pair/return/impedance review, factory DFM and physical testing remain. S.3 unrouted baseline and older revisions/checkpoints preserved; generators now write placement baselines instead of overwriting routed boards.

## 2026-10-14 — Control-only direction; routing stopped

- User stopped B.1 / R.1 routing and selected ten POWER plus ten RESET outputs without host LED sensing. RESET already exists in B.1; original case buttons and lights remain usable. Saved PCB checkpoints are preserved.
- Added `hardware/control-only-plan.json`: a conservative component-only projection keeps existing connectors and button ESD protection, removing 440 of 694 parts. Five-controller parts estimate falls from US$224.27 to US$162.07 using the 2026-10-13 catalog; no new PCB or assembled-board quote is claimed.
- Reviewed the CLI SPICE study and independently reproduced four representative B.1 cases. LED low-side-drive misread is confirmed in the assumed model; timer tolerance and GPIO reset pull-up findings remain open. This is not hardware validation.
- Control-only schematic/BOM, revised native PCB, 3D and public-site replacement remain pending. Existing B.1 artifacts are unchanged.

# 2026-10-14 B.1 行為級 SPICE 模擬

- 新增 hardware/simulation：ngspice 47 行為模型（LM393、TLC555、TLP3122A、EL357N、假設的主機板 LED 驅動）與六個網表；結果寫入 results/ 與 validation/checks.json 的 spice_simulation。電路、BOM、配置、3D 與接線圖不變。
- 發現 LED 感測對低側開汲極驅動的主機板一律讀成常亮（熄滅差動 1.7 V／無機殼 LED 4.9 V），只有高側驅動正確；what-if 上拉可修但未採用。
- TLC555 脈寬角落 6.75–25.7 s 超出 8–25 s 目標（X5R 電容 5 V 偏壓假設）；GPIO43/44 重置弱上拉使 555 RESET 約 2.28 V，建議換腳位。TLP3122A 驅動與回灌無問題。
- scripts/check-circuit.py 重新產生 checks.json 時保留 spice_simulation。

# 2026-10-14 B.1 / R.0 局部走線

- 依使用者要求改採實務布局審閱，IPC 全面合規不再阻擋試佈線。
- 實際 KiCad PCB 新增 524 段 F.Cu 局部走線；幾何 DRC 0 違規，仍未全板連通。
- 原位置、BOM 與主機接線不變；同步 3D、俯視圖及公開進度。

# 2026-10-14 規範檢查

- 選定 IPC-2221C 檢查架構；完整正文未取得，不宣稱全面合規。
- 修正 11 個通孔封裝誤標 SMT；加入 JLC 幾何 DRC 與組裝間距篩選。位置、電路與 3D 幾何不變。
- 記錄條件式佈線授權；目前尚有未驗證項，保持未佈線。

# Change log

## S.2 電氣布局審閱 — 2026-10-14

- 保留 B.1 十路電路，改為 200×170 mm 兩排各五路；放棄把 S.1 空間塞放當作電氣布局。
- 按原廠圖面補齊 52 個佔位的焊盤，新增本地 footprint library；按指定腳位安排去耦、隔離邊界、接头與時鐘。
- 加入四角固定孔與雙面隔離禁佈區、腳位/net/域間距/元件接近程度檢查，俯視圖由 PCB 實際座標生成。
- 同步 3D、公開布局審閱頁及 GitHub。等待使用者確認，不進入佈線；兩層走線可行性及製造仍待確認。
- 單片零件預算 $49.84；JLC 官方原型代貼最低 2 片。S.2 新尺寸裸板待重估，舊 S.1 報價只作歷史比較。

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
