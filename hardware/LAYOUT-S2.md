# S.2 零件布局審閱

此版供使用者確認元件位置，尚未佈線、尚非可製造版本。B.1 電路與用料不變；尺寸改為 200×170×1.6 mm，兩層仍是待走線驗證的候選。S.1 的 160×110 mm 是舊的純空間塞放研究，不再是目前布局。

## 採用的規範層級（尚非 IPC／IEC 合規簽核）

1. **原廠元件資料優先**：Toshiba／Everlight／HENIPER／Cjiang／Kangnex 的尺寸與焊盤圖，用於補齊本地封裝；Espressif、WIZnet、Diodes 的 layout 指南用於分區、去耦、晶振、接地與電源迴路安排。原廠建議中涉及走線、過孔、覆銅與實機測試的條件尚未完成。
2. **KiCad 封裝庫與預設 DRC**：檢查現有焊盤、courtyard、孔位、禁佈區等幾何關係。庫內封裝不是本案已經通過 IPC 合規審核的證明。預設停用項目與大量未連線仍存在，詳見檢查 JSON。
3. **專案自訂的布局篩選條件**：跨主機／控制電氣域的焊盤包圍盒間距至少 1.0 mm；比較器及多數 IC 的 100 nF 電源腳距離目標 3 mm，密集 W5500 類比電源區目標 4 mm；晶振／串阻／bulk／DC-DC 依用途另設接近程度門檻。精確目標與量測值逐項記錄在 JSON。這些距離是本案工程取捨，用於找出明顯不合理的位置，**不是原廠統一上限、IPC 保證值或高速／電源完整性的充分條件**。

目前沒有宣稱符合某一版 IPC 土地圖／板級設計標準，也未依 IEC 安規絕緣條件完成爬電與電氣間隙認證。1 mm 僅作低電壓功能隔離目標，不能把元件 datasheet 的隔離耐壓直接當成整板額定耐壓。正確狀態是「依原廠資料與自訂條件調整後的布局審閱版」。

## 擺放理由

| 區域 | 安排與理由 |
|---|---|
| 十路主機 | 上下兩排各五路，接頭朝外；約 38 mm 單元節距，保留接線操作空間。單元內比較器、輸入 RC 與回授電阻按同一訊號集中；不再把所有被動元件按尺寸混排。 |
| 主機／控制邊界 | 每路的兩顆 TLP3122A、兩顆 EL357N 與隔離電源跨在同一界線。各自的主機側位於外側，控制側位於中央，避免主機地線穿越其他單元。兩面均設禁止走線、過孔、焊盤與覆銅的隔離帶。 |
| 保護 | 四顆主機端 ESD 靠接頭的內側；USB 保護靠 USB 插座，後續走線必須先經保護再到 MCU。 |
| 感測供電 | 隔離電源輸入電容在控制側；輸出電容與 LDO 在主機側。比較器 100 nF 明確對應供電腳，限制焊盤中心距離。 |
| ESP32／W5500 | 放在中央左側，靠 USB／網路服務接頭；每顆去耦電容對應指定電源腳。晶振、串聯元件與負載電容成組，與右側開關電源分開。此為有線版，沒有 RF 天線。 |
| 輸出暫存 | 三顆 74HC595 分布於中央橫向通道，縮短前往十路驅動的支線；其去耦電容緊貼供電腳。 |
| 主電源 | 5 V 接線端在右側板邊，保險絲與反接保護緊接其後；AP63203、輸入電容、BST 電容、電感及輸出電容集中。實際高 di/dt 迴路仍需佈線審核。 |
| 維修／固定 | 四角 M3 3.2 mm 非鍍通孔；中央留下可走線空間。RESET／BOOT 接頭留在主控區，機殼開孔及實物線束彎曲半徑仍待確認。 |

## 封裝與可重現性

S.1 的 52 個無焊盤佔位已用有焊盤的封裝替換：四個自建封裝位於 `cad/RackATX.pretty`，電感使用 KiCad 的 FNR4018S 封裝。

- Toshiba TLP3122A：11-4M1S，腳號 1／3／4／6；原廠 land-pattern 焊盤 0.8×1.2 mm，兩排中心距 6.3 mm、同排節距 2.54 mm。[原廠封裝](https://toshiba.semicon-storage.com/us/semiconductor/design-development/package/detail.4pin%20SO6.html)。
- Everlight EL357N：原廠 Rev.9 第 7 頁，焊盤 1.5×0.6 mm、內間距 4.85 mm、外跨度 7.85 mm；1=A、2=K、3=E、4=C。[原廠文件](https://www.everlighteurope.com/custom/files/datasheets/DPC-0000014.pdf)。
- HENIPER B0505S-1WR3L：原廠 V3-2020 第 5 頁，11.6×6 mm 外形、2.54 mm 腳距、1.0 mm 孔；1=GND、2=Vin、3=0V、4=Vo。使用 C20622559 所附的 HENIPER 圖面，不套用同名 Mornsun 元件。[選定料號](https://jlcpcb.com/partdetail/C20622559)。焊盤外徑 1.5 mm 為本設計選擇。
- Cjiang FNR4018S：原廠系列第 2 頁，4×4 mm 外形；建議焊盤寬 1.1 mm、長 3.7 mm，兩焊盤內距 1.9 mm。核對 KiCad `L_Changjiang_FNR4018S`。[選定料號](https://jlcpcb.com/partdetail/C167806)。
- Kangnex WJ500V-5.08-2P：原廠圖面 5.08 mm 腳距、1.2 mm 孔、10 mm 深、14 mm 高；兩孔焊盤外徑 2.2 mm 為本設計選擇。[選定料號](https://jlcpcb.com/partdetail/C8465)。

自建封裝是依圖面轉錄的審閱資料，仍需製造前的獨立覆核、鋼網與孔公差審核；不把「已補焊盤」寫成「已實物驗證」。B.1 原理圖的原始 footprint 欄位尚未全部回填，S.2 生成器內含明確的 override，連線則逐腳對照同一份 `circuit.json`。

生成：用 KiCad 10 附帶的 Python 執行 `scripts/make-layout-review.py`，再執行 `scripts/check-layout-review.py`。審核數字在 `layout-review-checks.json`，真正的位置在 `cad/layout-S2-review.kicad_pcb`；俯視圖 `layout-S2-review.svg` 由該 PCB 焊盤座標生成。

## 如何理解檢查

1. 每個電氣元件都必須有焊盤，所有有連線的原理圖腳位都須存在且 PCB net 相同。
2. 元件外形／courtyard 包圍盒不能重疊，關鍵去耦使用指定供電腳的距離檢查。
3. 不同主機、主機與控制側的焊盤包圍盒間距至少 1.0 mm。這是低電壓功能隔離設計規則，不是安規、高壓耐受或爬電距離認證。
4. 尚無走線，因此不能用以上檢查宣稱回流、阻抗、熱、EMI 或整板電氣功能已通過。KiCad 未連線報告必然仍有大量項目。

依據：[Espressif 布局指南](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)、[WIZnet 布局指南](https://docs.wiznet.io/Design-Guide/hardware_design_guide)、[AP63203 原廠評估板指南](https://www.diodes.com/assets/Evaluation-Boards/AP63203-EVB-User-Guide.pdf)。兩層能否在維持接地與隔離的條件下完成，須實際佈線後判定。使用者已授權規範檢查通過後直接佈線；目前檢查尚未完成，見 [規範審查](STANDARDS-AUDIT.md)。

目前幾何 DRC 已加入 JLC 工艺條件並重新開啟通孔／SMT 屬性與 courtyard 檢查；檢查停用項目與未連線項數記錄於 `layout-review-checks.json`。原理圖／PCB 的完整 KiCad parity 尚未執行，不把這個 DRC 結果寫成製造放行。
