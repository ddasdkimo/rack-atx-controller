# JLCPCB 選料與成本 — B.1

2026-10-13 逐項讀取 **JLCPCB 自身代貼庫**，48 種實際上板料號皆顯示 Economic and Standard 且有庫存；已記錄確切 MPN、C 編號、封裝、分類、組裝方式、查詢時間與階梯單價。[完整主板 BOM](bom/controller-bom.csv)有 694 個元件；[分接板 BOM](bom/adapter-bom.csv)每板 10 個元件。庫存是當時觀察值，不是保留庫存或下單承諾。

[controller-jlc-bom.csv](bom/controller-jlc-bom.csv) 和 [adapter-jlc-bom.csv](bom/adapter-jlc-bom.csv) 使用 JLC 的四欄格式。目前可作選料／詢價基礎；**沒有對應 CPL、佈線及 Gerber，不能當整套生產資料**。Footprint 欄有候選庫名稱或供應商封裝名，最後下單需以經審核的 PCB footprint/CPL 重匯。

## 主控板成本試算

USD；相同主控板每片支援十台。價格按整批需求量套用觀察到的階梯價；耗損／MOQ 未加，未使用優惠券。組裝先估單面 Economic，1731 SMT 焊點、160 通孔焊點／片。USB shield 的四個焊腳、RJ45 兩個 shield 焊腳計入估算。

| 批量 | 整批零件 | 整批零件＋組裝小計 | 每片零件＋組裝 |
|---|---:|---:|---:|
| 2 片原型 | $97.58 | $174.51–196.42 | $87.26–98.21 |
| 5 片小批量 | $224.27 | $322.30–341.75 | $64.46–68.35 |

**不是成品總價或工廠報價。** 未含主板／分接板 PCB、工藝邊／拼板、耗損料／MOQ、額外工序、運費與稅、機殼、外接電源、壓接線束及主機板轉接線。十片免供電分接板的連接器零件合計約 **$6.40**，另加裸板與手焊。線材及端子的採購／壓接費可能比小板高，不應忽略。

只有一個機櫃時，先做 2 片測試／備份較省總支出。5 片單價較低，但要多花約 $145，且未驗證設計不宜為攤費一次多買。

## 收費怎麼影響這版設計

計价採用 [JLC 官方費率頁](https://jlcpcb.com/help/article/pcb-assembly-price)（2026-09-09 更新），不是「打板 $2」促銷。Economic 起始 $8.18、鋼網 $1.53；SMT 每焊點 $0.0016，手焊每單 $3.58＋每點 $0.0164；普通 Extended 上料每料號 $3.07。另列 $0.45 placement confirmation。QFN 等隱藏焊點需 X-ray，本批量模型按 1–3 個需照射元件／板計算，依元件總數的費階計價。

本版有 **27 種 Basic、16 種 SMT Extended、5 種通孔 Extended**。上料費低值只計 SMT，保守高值連通孔料也計，最終依購物車判定。Preferred Extended 是否免上料須查當時分類，本版沒有假設任一普通 Extended 免收。價格上下限仍未涵蓋所有額外製程。

Standard 另有較高 setup／stencil、所有料號的 feeder loading、治具等。Handling fee 是使兩方案價差達規定額度的補差機制，**不能把頁面顯示的最低差額一律再加一次**。B.1 選料目前全支持 Economic；板形與工藝是否仍符合須在 PCB 定版後核對。

具體取捨：

- ESP32-S3FN8 裸 QFN C2913196 可走 Economic；查到的 WROOM 模組 C2913198 僅 Standard。保留 USB 燒錄、內建 flash，省模組限制；代價是要自行做好 QFN、晶振與電源佈線，並計入 X-ray。禁用 RF。
- 用 3 顆 Basic 74HC595D C5947＋直接 GPIO 取代三顆 MCP23S17；本板需要的是鎖存按鍵輸出及即時 LED 回報。
- 板間選 JST PHD C161672。原本 Molex THT 型號未取得 JLC 選料依據，查到的另一個 Molex SMT 型號庫存只有 5 個且單價高，不足一套。
- 0603 電阻／電容盡量共用 Basic 值；1 µF 改用 C15849 Basic。390 kΩ 偵測偏置與 W5500 12.4 kΩ 仍保留精確所需值。少量上料費要和增加元件／焊點／面積一起比較。
- 保留十路隔離供電與光隔離；它們是避免控制板把十台信號地接在一起的功能需求。
- 分接板只有通孔接頭，建議裸板手焊，省另一筆 PCBA setup；但主控板的通孔接頭／隔離電源仍請 JLC 組裝。JLC 料庫標示 Wave Soldering 不等於整條線束代工。
- 外部改穩壓 5 V，取消不必要的 12→5 V 轉換。板外形由 280×220 縮為 200×160 mm 的配置目標。舊面積本來就未超過 650 cm²，不能宣稱這次省掉大板附加費；真正 PCB 費用待佈線報價。

## 最後才能下單的資料

完成並核對 PCB 後，從同一版產生 Gerber、鑽孔、工廠 BOM、CPL、方向／極性與組裝說明。核對焊盤形狀、腳號、元件實際尺寸、板面、CPL 單位與旋轉角，尤其 Toshiba 1/3/4/6 腳及 USB/RJ shield。不要把本網站簡化 3D 的位置轉成 CPL。

JLC 的零件庫供代貼使用，不表示可以把膠殼／壓接端子或備用散件和 PCBA 一起寄出。機外線束另詢正規通路／線束廠，未含在本表。這次未上傳訂單、買料或付款。

可重算檔：[cost-model.json](bom/cost-model.json)、[batch-parts-cost.csv](bom/batch-parts-cost.csv)、[scripts/cost.py](../scripts/cost.py)。原始公開庫資料在 [research/](research/)；簽名下載 URL 與帳戶資訊不入庫。下一次下單前必須重新查庫存與代貼分類。
