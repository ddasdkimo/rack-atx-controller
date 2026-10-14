# Rack ATX Controller

**目前方向：一片控制十台主機，R.0 已開始局部佈線。** B.1 電路搭配 200×170 mm、兩層候選布局，全部 694 個電氣元件已有焊盤；已完成 524 段局部走線，尚未全板連通，不能送製造。[R.0 進度](hardware/ROUTING-R0.md)。[布局理由](hardware/LAYOUT-S2.md) · [公開審閱圖](https://rack-atx-controller-ddasdkimo.raidavid.chatgpt.site/layout.html)。S.1 縮板與 P.0 拆板研究保留為歷史參考。

10 台電腦的機櫃遠端電源控制硬體規劃，保留原機殼 POWER／RESET 按鈕、電源燈與硬碟燈。

**目前版本：B.1 · 原理圖審閱版。** 已有 JLC 選料、完整電路定值、KiCad 原理圖、BOM 與批量成本。ERC／連線及 DC 角落計算已檢查；PCB 已進入 R.0 局部佈線；尚無完成的 PCB、CPL／Gerber 或實機驗證。目前 S.2 依實際焊盤與電路關係重新布局；3D 與俯視審閱頁均由同一份 PCB 位置資料生成。

- 公開討論網頁：[3D 控制板與兩台電腦接線](https://rack-atx-controller-ddasdkimo.raidavid.chatgpt.site)
- [硬體架構與接線](hardware/HARDWARE.md)
- [接頭與設計資料來源](hardware/design.json)
- [JLCPCB 製造與選料方向](hardware/JLCPCB.md)
- [KiCad 原始檔](hardware/cad/) · [主控板原理圖 PDF](hardware/release/controller-schematic.pdf) · [分接板 PDF](hardware/release/adapter-schematic.pdf)
- [完整 BOM 與 JLC 格式](hardware/bom/) · [驗證結果](hardware/validation/checks.json) · [原廠依據](hardware/SOURCES.md)
- [修改紀錄](CHANGELOG.md)

## 3D 圖可以查看什麼

- 完整控制板：10 個主機接頭、20 個隔離按鍵開關、20 路 LED 偵測、10 組隔離供電、MCU、有線網路、I/O 與電源區。
- 兩台虛擬電腦：CPU、記憶體、儲存元件、前面板訊號、直通轉接板、原按鈕及燈號。
- PC-01 接 J01、PC-02 接 J02，其他八路預留。
- 滑鼠旋轉、滾輪／雙指縮放、觀察位置切換、外殼顯示，以及逐組訊號追線。
- 下方接線圖直接呈現原線直通與控制支路；訊號編號表列出全部腳位及實際線芯配色，不冒充原廠插孔位置圖。
- B.1 連接器：JST PHD（S10B-PHDSS(LF)(SN)／PHDR-10VS／SPHD-001T-P0.5）；線材候選：Belden 9505。均為真實型號，但線束需要訂製、壓接及實物驗證。

## 核心原則

原按鈕與 LED 的路徑走轉接板的被動直通銅箔，不依賴控制器供電。POWER／RESET 以常開隔離開關並聯；LED 用有限負載的高阻抗差動偵測與隔離回傳。每台主機的參考地只連到它自己的隔離偵測區。

**J01–J10 是本專案自訂接頭，不是通用的主機板 F_PANEL 針位，也不是 Ethernet。** 主機板端使用分開的標籤插頭，依實際主機板手冊接線。沒有 RESET／HDD LED 的主機可留空該組；雙色或三腳電源燈需要另外適配。

## 本機重建與檢視

需要 Python 3。3D 使用固定版本 Three.js 0.160.1，從 jsDelivr 載入；沒有資料上傳或遠端主機控制功能。

```sh
python3 scripts/build.py
python3 scripts/check.py
python3 -m http.server 8080 --directory docs
```

瀏覽 `http://localhost:8080`。`docs/index.html` 可直接下載開啟，但需要網路載入 Three.js。

`visualization/viewer.template.html` 是互動圖原始碼，`hardware/design.json` 是接頭／數量／版本資料來源。`visualization/standalone-shell.template.html` 是由 Codex visualization exporter 產生的可獨立執行容器；它提供主題、控制項樣式與本機互動狀態保存。`scripts/build.py` 將相同的視覺內容產生至 `docs/` 與部署用 `dist/`。

## 後續維護

使用者已要求：**每次完善電路板時，都要同步更新 3D 與接線圖。** 詳見 [AGENTS.md](AGENTS.md)。電路、腳位、線材、隔離邊界、尺寸或元件位置有改動時，必須同時修改設計資料、圖面、硬體文件與 changelog，重建、驗證後更新公開網頁與此 repository。

## S.1 歷史縮板估價（不適用 S.2）

| 方案（5 片） | 裸板 | 零件 | 工廠全部焊好，含板＋料＋組裝 |
|---|---:|---:|---:|
| 原四層 200×160 | $50.60 | $224.27 | $372.90–392.35 |
| 原尺寸改兩層 200×160 | $21.20 | $224.27 | $343.50–362.95 |
| S.1 兩層縮板候選 160×110 | $14.00 | $224.27 | $336.30–355.75 |
| S.1 四層縮板備案 160×110 | $41.30 | $224.27 | $363.60–383.05 |

先前的兩層 160×110 mm 研究候選，面積減少 45%；四層同尺寸為備案。5 片自己焊接材料共 $238.27，工廠焊好約 $336.30–355.75。**單片零件約 $44.85，$224.27 是 5 片合計。** 裸板為 JLC 網頁尺寸試算，組裝為費率估算，均非已接受的生產報價。未含運稅、耗損／MOQ、工藝追加、分接板、線束、電源、外殼及韌體。

採購偏好：**可以等待，優先一般交期、單面 Economic PCBA、不加急及較便宜物流**。等待本身不保證折扣；物流費待地址與包裹確定。

[完整縮板分析](hardware/COMPACT-STUDY.md) · [KiCad 配置草稿](hardware/cad/compact-S1-placement.kicad_pcb) · [可讀 BOM](https://rack-atx-controller-ddasdkimo.raidavid.chatgpt.site/bom.html) · [成本明細](hardware/JLCPCB.md)

未完成：五類未指派焊盤與其餘候選焊盤審核、PCB layout／DRC／製造檔、實際主機板針位、掉電負載及回灌、timer 公差與故障釋放、線長／EMI、溫升與實機驗證。模型中的線路只表達功能，不構成硬體測試。[hardware/simulation](hardware/simulation/README.md) 的行為級 ngspice 模擬只是審閱輸入：它指出 LED 感測對低側驅動主機板會誤判、timer 角落超出 8–25 s、GPIO43/44 重置上拉削弱互鎖，這些尚未改入電路。
