# R.2 routing review — B.2 control-only circuit

中央板 100×110×1.6 mm、雙面銅、300 個電氣元件＋4 個 M3 孔；2,754 段銅線、185 過孔、22 個接地覆銅區（主控與十個獨立 HOST_REF，各雙面）。主機端被動轉接板 26×34 mm，6 個接頭、30 段走線、0 過孔。兩板原生 DRC、未連接均為 0。

[中央板實際銅箔](routing-R2.svg) · [轉接板](adapter-B2.svg) · [原生 CAD](cad/B2/) · [雜湊綁定檢查](validation/routing-R2-checks.json)

## 檢查範圍

- S.3 47 項電源／晶振／去耦距離檢查通過。原生 PCB 所有定義腳位（含 NC）、封裝、符號 UUID 與 circuit.json 一致；後者另與 KiCad XML 匯出逐腳核對，兩板 ERC 0。
- 一般線寬／間距最小 0.15 mm，過孔 0.6 mm／鑽孔 0.3 mm，按 1 oz 銅設計。這符合查得的 [JLCPCB 1/2 層基本能力](https://jlcpcb.com/capabilities/pcb-capabilities)（2026-10-14 查閱），不是工廠對本檔案的接單認可。不可直接改成 2 oz 而沿用此設定。
- 每台主機與其他電氣域維持 1 mm 低壓功能分隔規則，雙面隔離帶禁止銅箔／過孔／焊盤。這不是市電或安全隔離額定值。
- MCU／W5500 晶振與 buck 開關／bootstrap 關鍵線已固定在正面、無過孔；其餘網路完成後加入主控與各 HOST_REF 的雙面覆銅。未使用 via-in-pad 製程。
- 銅箔供電單一路徑估算採 35 µm 銅、60°C、每過孔 2 mΩ。MCU 各供電腳以保守 0.65 A 套用單一路徑，最大名義壓降 0.1074 V；線寬減 20% 的上界約 0.1343 V，低於本次 0.15 V 銅箔審閱預算。未含元件、地回路、供電瞬變或溫升，不能代替整板電源量測。
- DRC 不使用個別違規排除。KiCad 預設未啟用的五項檢查（例如 missing courtyard、via endpoint centering、tuning profiles、footprint filters/type）原樣列於 JSON，沒有將「DRC 0」當作全部製程與電氣性能驗證。
- LED 自訂封裝沿用 KiCad 標準銅箔尺寸，只將影響 1 mm 操作標籤的外框線移到 Fab，保留陰極絲印。元件本體及封裝仍須樣品／工廠覆核。

## 送廠前仍須處理

USB／Ethernet 目前是已連通的走線候選，尚未完成差動配對、參考地連續性與指定疊構阻抗資格驗證。報告中的整個 net 長度包含分支，不能拿來當差動 skew。不能僅憑 DRC 0 宣稱 USB 90Ω 或 Ethernet 100Ω 達標。

還需工廠 DFM（含 QFN stencil／散熱焊盤、THT 手焊／波峰焊覆銅接法）、實際振盪器與限時、供電負載／溫度、ESD／EMC、線束及主機相容性驗證。目前沒有製造放行、Gerber／CPL 或已接受的 PCBA 報價。

## 重建與來源

S.3 未佈線基準保存在 cad/B2/placement，不覆蓋已佈線主檔。關鍵走線由 route-critical-b2.py 固定，Freerouting 完成一般網路，再用 repair-b2-routes.py 補齊剩餘連線、finish-b2-board.py 整理絲印與覆銅。最終 native PCB 是保存的編輯來源，不要求重跑自動路由產生位元相同檔案。

驗證及展示依序執行 check-layout-s3.py、audit-r1-power-paths.py（指定 B.2 路徑與 b2 輸出）、validate-routing-b2.py、export-routing-b2.py、export-adapter-b2.py、build.py、check.py。原生 Python 腳本使用 KiCad 自帶 Python；原理圖／模擬流程見 cad/README.md。
