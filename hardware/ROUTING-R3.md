# R.3 佈線與送樣前檢查

B.2 功能與接腳不變，中央板仍為 100×110 mm、兩層、300 個電氣元件。R.3 有 3,855 段走線、252 個過孔。兩板原生 DRC／未連接均為 0；原理圖 ERC 為 0。尚未完成工廠製程接受、正式送件包及最終複查，不能據此開始生產。

## 本次修正

- CAM 檢視後補上實際絲印 J01–J10、5V 輸入正負、USB/LAN 與背面 BOOT／MCU RST／版本，避免只在網頁顯示通道名稱。所有銅箔保持不變，另跑絲印 DRC。

- USB 主對頂層 0.34 mm，主要中心距 0.50 mm，間隙 0.16 mm；短扇入為 0.15 mm。R8/R9 移到 USB 接頭附近。主線和 MCU 扇出下方保留底層地，接頭存根區有三處 VBUS 短交叉。
- Ethernet 的 RX 49.9 Ω 終端集中，兩電阻相距 1.5 mm；共同端到 C33 約 1.12／1.64 mm。TX 留在頂層，接頭旁 RJ_RD_N 保留一次計畫內換層。
- MCU 裸露焊盤增加九個 0.6/0.3 mm 地孔，十六個圓角 0.75 mm 鋼網窗，名義錫膏面積約 55.39%。獨立 Gerber／Excellon 解析確認孔不與錫膏窗相交。底面蓋油不等於填孔或蓋銅；最終 QFN 工藝仍待工廠確認。
- C21–23 使用 C1525、C33 使用 C15195、R20/R21 使用 C25120、C34/C35 使用 C318580。額定值和電路連接不變；最後一項為 Extended，新增每單 US$3.07 裝料費參考值。
- DRV_04 為低速基極驅動線，約 134.23 mm、兩個過孔，沿左側與下側避開高速主線。移除三段冗餘頂層地線後補妥局部地連接，未增加零件。

## 複查與實際限制

使用者指定 CLI 在 2026-10-15 對固定 SHA `52cde6cbfafc2e72055e5f7ddc29cfab5c54b659c576015373e620836fd09bf4` 的佈線試稿獨立重跑 DRC，核對高速線下方填銅、地孔網路與供電路徑，未發現阻擋原型打樣的佈線問題。這是佈線階段複查，並非最後製造放行。

C34 焊盤轉接處約 0.345 mm 的局部底層參考缺口、RJ45 通孔端點的開口，以及 Type-C 存根區 VBUS 交叉均已明列。原生幾何與填銅投影不能替代 USB／Ethernet 實測。兩層板不在 JLCPCB 控阻服務範圍內。

供電銅路徑以 35 µm 銅、60°C、每個 0.3 mm 孔 2 mΩ、0.65 A 單路保守估算，MCU 最大壓降 0.1081 V；線寬減少 20% 時上界約 0.1352 V。此估算不含回流、元件壓降或負載瞬態，仍需實測。

S.3 原始未佈線基準保留不動；目前的實際位置／封裝以原生 PCB 和 `routing-R3.json` 的 `component_overrides` 為準，3D 以此同步。模型為封裝範圍示意，並非精密機構模型。

## 仍待完成

正式 Gerber／鑽孔、貼片座標與 BOM 一致性檢查、完整 CAM 獨立檢視、JLCPCB 一般 Economic 報價與 QFN 製程確認、固定送件包的最後獨立複查。上電、USB／Ethernet、計時、ESD／EMC、主機相容性與機構裝配均需實板驗證。

主要依據：[Espressif ESP32-S3 PCB 指南](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)、[WIZnet 硬體指南](https://docs.wiznet.io/Design-Guide/hardware_design_guide)、[JLCPCB 能力](https://jlcpcb.com/capabilities/pcb-capabilities)、[JLCPCB 孔處理](https://jlcpcb.com/help/article/pcb-via-covering)。

## 加工檔複查

兩板 Gerber、鑽孔、BOM/CPL 已產生並通過獨立 CAM 與指定 CLI 固定包複查，詳見 `manufacturing/R3-candidate` 及 `validation/r3-manufacturing-peer-review.json`。剩餘製造條件為 JLC 料庫旋轉／極性預覽、QFN 孔與鋼網工藝、Economic 通孔資格和完整報價；這些尚未通過。PCB、Gerber 和 CPL 不得因報告為零而直接放行生產。
