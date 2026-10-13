# JLCPCB 製造與選料方向

使用者指定將 JLCPCB 納入 PCB 打板與 PCBA 規劃，並優先考慮其可用元件。這是後續設計原則，尚未詢價、下單或上傳製造檔。

## 選料紀錄

每個真正上板的元件，定版前需記錄：

- 製造商與完整料號、電氣規格、封裝。
- JLCPCB／LCSC 的精確 C 編號及產品連結。
- PCBA 支援方式、Basic／Extended／其他供料分類、查庫存日期。
- 代貼、另行手焊或不裝（DNP）方式。
- 規格相容的備選料，而不是只比對腳數或名稱。

目前 `hardware/design.json` 的接頭、端子和 Belden 線材為實際型號候選；它們的 JLC 可代貼狀態尚未核實。其他電路方塊也不是完整製造 BOM。未知的 LCSC 編號保持空值，不填猜測值。尤其線端膠殼、端子壓接、整條線束與機殼加工不應視為一般 SMT 貼片自動涵蓋。

## 交付工廠的資料

完成原理圖與 PCB 後，從同一 CAD 版本產生 Gerber／鑽孔檔、BOM、CPL（貼片位置與角度）、組裝說明。BOM 的 Designator 必須和 CPL 一致，並檢查料號、封裝、元件方向、板面、單位及 DNP 設定。不能從本專案的 3D 功能示意圖反推貼片座標。

原型宜先验证單路隔離開關、LED 保留亮度與掉電負載，再複製成 10 路。第一版 PCB 製程與層數會在原理圖及實際供料確認後決定；目前 280 × 220 mm 只是 3D 討論外形，不是已報價尺寸。

## 官方參考（2026-10-13 查閱）

- [JLCPCB 香港網站](https://jlcpcb.com/hk)
- [BOM 檔案規範](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly)
- [KiCad 8 匯出 BOM 與 CPL，含 LCSC PN](https://jlcpcb.com/help/article/how-to-generate-bom-and-centroid-files-from-kicad-8)
- [BOM／CPL 一致性建議](https://jlcpcb.com/help/article/advice-for-bom-and-cpl-files-preparation)
