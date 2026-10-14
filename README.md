# Rack ATX Controller · B.2 / R.3

十台 Linux 主機共用一塊 POWER／RESET 遠端按鍵控制板。**100×110 mm、兩層的 R.3 佈線版已連通；中央板與轉接板 DRC／未連接均為 0。尚未製造放行。**

[公開佈局](https://rack-atx-controller-ddasdkimo.raidavid.chatgpt.site/layout.html) · [3D／兩台主機接線](https://rack-atx-controller-ddasdkimo.raidavid.chatgpt.site/) · [BOM](https://rack-atx-controller-ddasdkimo.raidavid.chatgpt.site/bom.html)

## 本版變更

- R.3 完成 USB 主對、Ethernet 終端集中、QFN 熱孔／鋼網窗，CC 電阻移近接頭。8 個 Ethernet 零件改為相同額定值的 0402；新增一個 Extended 料號，裝料費每單約多 US$3.07。原電路功能、接頭與 GPIO 不變。

- 移除全部 LED 偵測及十組隔離電源，保留二十個 TLP3122A 雙向隔離接點。原 POWER／RESET 按鈕經被動分接板並聯；原機殼 LED 直接留在主機板上。
- 原理圖／BOM 為 B.2；R.3 原生 PCB 有 300 個電氣元件、4 個固定孔、3,855 段走線與 252 個過孔。較 S.2 的 200×170 mm 面積減少約 68%。
- 修正模擬發現的計時與開機預設電位問題：MC14541B 計數式限時、1 nF C0G、獨立 ARM 閘控，GPIO 改為 4／6／7。
- 兩板 ERC／DRC／未連接均為 0。26×34 mm 被動轉接板為 6 個元件、30 段走線。16 組角落與 9 種狀態的 ngspice 行為模型通過，模型脈寬 11.26–21.46 秒。USB／Ethernet 的原生幾何與回流已由指定 CLI 獨立複查；兩層板沒有工廠控阻保證，尚未完成實板資格驗證，還需工廠 DFM 和實機驗證；目前已有 Gerber／鑽孔／BOM／CPL 審閱包，第二輪獨立離線加工檔複查沒有發現阻擋項；JLC 旋轉角／極性預覽、QFN 工藝與完整報價仍待確認，尚未製造放行。

## 設計檔

- [B.2 KiCad 原理圖與 R.3 PCB](hardware/cad/B2/)
- [主控原理圖 PDF](hardware/release/controller-schematic.pdf)／[被動分接板 PDF](hardware/release/adapter-schematic.pdf)
- [硬體與接線](hardware/HARDWARE.md)／[佈局理由](hardware/LAYOUT-S3.md)／[R.3 佈線檢查與限制](hardware/ROUTING-R3.md)
- [BOM 與成本](hardware/bom/)／[費率假設](hardware/JLCPCB.md)
- [模擬方法與限制](hardware/simulation/README.md)／[B.2 結果](hardware/simulation/results/B2-summary.json)

J01–J10 是自訂 JST PHD 10 pin，**不是主機板通用 F_PANEL 或 Ethernet**。只接 pin 1/2 POWER、3/4 RESET、9 本機按鍵 ESD 參考地；5–8、10 不接。每台 HOST_REF 僅屬該台，與主控及其他主機保持隔離。線束與主機板跳線按實際手冊逐台核對。

## 成本範圍

五片中央板零件 US$162.38，約 US$32.48／片；B.1 同批量 US$224.27，減少約 28%。五片零件＋組裝估算 US$246.93–263.31，**還須加新尺寸裸板、運稅、耗損／MOQ**。不是含運成品價。實際上傳 Gerber 後，五片裸板試算 US$9.30／27.20／82.99，分別為 HASL 蓋油、ENIG 蓋油、ENIG 填孔蓋銅；QFN 工藝均待工廠確認。採一般交期、單面 Economic、不加急。詳見 [成本與範圍](hardware/JLCPCB.md) 及 [加工檔審閱包](hardware/manufacturing/R3-candidate)。

## 重建

```sh
python3 scripts/build.py
python3 scripts/check.py
python3 -m http.server 8766 --directory dist
```

電路與原生 PCB 的完整重建方式見 [CAD 說明](hardware/cad/README.md)。3D 使用固定版本 Three.js，元件本體為簡化外形，但中央板與轉接板尺寸／位置／銅箔來自原生 KiCad；兩台主機為接線示意。網站沒有操作真實主機或上傳私密資訊的功能。

每次硬體變動須同步原理圖、BOM、3D、接線圖與公開網頁，見 [AGENTS.md](AGENTS.md)。B.1／S.2／R.0／R.1 資料與本機走線檢查點保留為歷史，不能繼續當作現行電路。
