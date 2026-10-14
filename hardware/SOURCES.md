# B.2 additions — checked 2026-10-14

- [onsemi MC14541B Rev.16](https://www.onsemi.com/pdf/datasheet/mc14541b-d.pdf): pin functions, manual reset at 5 V, RC equation, single-transition counter and output polarity.
- [MC14541BDR2G JLC C7292](https://jlcpcb.com/partdetail/C7292): Economic/Standard, Extended, observed stock4597, single-unit0.3017USD. Exact tiers/time in research/C7292.json.
- [Samsung C0G CL10C102JB8NNNC JLC C163508](https://jlcpcb.com/partdetail/C163508): 0603,1nF,±5%,50V,Extended,observedstock483260. Catalog snapshot in research/C163508.json.
- [Espressif ESP32-S3 datasheet](https://documentation.espressif.com/esp32_s3_datasheet_en.pdf): reset GPIO defaults and glitch notes inform GPIO4/6/7 selection.
- [JLC assembly fees](https://jlcpcb.com/help/article/pcb-assembly-price): current fee schedule, checked again2026-10-14. Cost-model assumptions remain estimates.

Other research records are historical candidates, not necessarily selected. Current selections are exclusively in hardware/circuit.json and BOM.

---

# 選料與接腳核對來源

查閱日 2026-10-13；B.1 文件完成 2026-10-14。`research/C*.json` 是公開 JLC catalog 欄位的觀察紀錄，含當時庫存及價格；不包含登入資訊或原廠 PDF 的簽名下載連結。供應商 datasheet 保留連結，未將整份第三方文件重新散布。

| 電路 | 主要依據／需注意的差異 |
|---|---|
| ESP32-S3FN8 | [Espressif schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html)、[chip datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)。內建 Quad flash，不使用 GPIO26–32；VDD_SPI 接去耦；GPIO45 選 3.3 V；RF 關閉；USB 33 Ω。 |
| W5500 | [官方資料](https://docs.wiznet.io/Product/Chip/Ethernet/W5500)、[RJ45 reference schematic](https://docs.wiznet.io/assets/files/w5500_sch_v110_use_mag_-dfff8bbb103d13be4f25cd2b2f8b950d.pdf)。EXRES1 12.4 kΩ、TOCAP 4.7 µF、1V2O 10 nF、RX 串 6.8 nF；PMODE 全高自動協商。 |
| HR911105A | [JLC C12074 的 HanRun datasheet](https://jlcpcb.com/partdetail/C12074)。1 TD+、2 TD−、3 RD+、4 TCT、5 RCT、6 RD−、7 NC、8 shield-network GND、9/10 green A/K、11/12 yellow K/A；KiCad SH 對應兩個外殼腳。此腳位不同於 WIZnet 圖上的另一款插座。 |
| TLP3122A | [Toshiba product](https://toshiba.semicon-storage.com/ap-en/semiconductor/product/isolators-solid-state-relays/photorelay-mosfet-output/detail.TLP3122A.html)、[datasheet](https://toshiba.semicon-storage.com/info/TLP3122A_datasheet_en_20230525.pdf?did=60353&prodName=TLP3122A)。4-pin SO6，腳位 **1/3/4/6**；IF 建議 ≥5 mA。 |
| EL357N(B)(TA)-G | [Everlight](https://www.everlighteurope.com/product-details?category=Opto-Coupler&id=708&name=EL357N%28B%29%28TA%29-G)、[2025 datasheet](https://www.everlighteurope.com/custom/files/datasheets/DPC-0000014.pdf)。1A、2K、3E、4C；B 級 CTR 測試條件不能直接當低 IF／低溫保證。 |
| LM393DR | [TI LM393 datasheet](https://www.ti.com/lit/ds/symlink/lm393.pdf)。正輸入電壓與供電無關的輸入額定、共模上限、offset／bias 及 output sink 條件。 |
| TLC555CDR | [TI TLC555 datasheet](https://www.ti.com/lit/ds/symlink/tlc555.pdf)。CMOS RESET 漏電與門檻；pin1GND、2TRIG、3OUT、4RESET、5CONT、6THRES、7DISCH、8VDD。 |
| B0505S-1WR3L | [JLC C20622559 的 HENIPER datasheet](https://jlcpcb.com/partdetail/C20622559)。1 GND in、2 Vin、3 GND isolated、4 Vout；4.5–5.5 V 輸入，非穩壓輸出；1500 **VDC**。 |
| HT7533-1 | [JLC C14289 的 Holtek datasheet](https://jlcpcb.com/partdetail/C14289)。SOT89 **1 GND、2 VIN、3 VOUT**，不可套別家 SOT89 穩壓器腳位。 |
| AP63203WU-7 | [Diodes AP63200/AP63201/AP63203/AP63205 datasheet](https://jlcpcb.com/partdetail/C780769)。1FB、2EN、3VIN、4GND、5SW、6BST，依固定 3.3 V 版本接線。 |
| PESD5V0S2BT | [JLC C2841440 的 TECH PUBLIC datasheet](https://jlcpcb.com/partdetail/C2841440)。本料号雙向 TVS：1/2 I/O、3 common。同名不同廠牌替代需要重新查。 |
| PRTR5V0U2X,215 | [Nexperia datasheet](https://assets.nexperia.com/documents/data-sheet/PRTR5V0U2X.pdf)。**1GND、2IO1、3IO2、4VCC**。 |
| 74HC595D,118 | [Nexperia datasheet](https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf)。本版是 HC 3.3 V，非 HCT；MR 只清 shift register，必須明確 latch 全零，OE 預設上拉。 |
| USB-C | [C165948 HRO TYPE-C-31-M-12](https://jlcpcb.com/partdetail/C165948)。CC1/CC2 各 5.1 kΩ，16 個信號接點＋4 個 SH 焊腳；原理圖 SH 名稱與標準 KiCad footprint 對齊。 |
| 輸入端子 | [C8465 WJ500V-5.08-2P](https://jlcpcb.com/partdetail/C8465)。5.08 mm、供應商電流額定高於本板需求；不用原先僅 1 A 的 DC-005 候選。 |
| JST 線束 | [JST PHD 原廠系列圖](https://www.jst-mfg.com/product/pdf/eng/ePHD.pdf)。S10B-PHDSS／PHDR-10VS／SPHD-001T-P0.5 配對；端子 26–22 AWG、絕緣外徑 1.0–1.5 mm。 |
| Belden 線材 | [9505 product](https://www.belden.com/products/cable/electronic-wire-cable/multi-pair-cable/9505)、[技術資料](https://catalog.belden.com/techdata/EN/9505_techdata.pdf)。五對 24 AWG，外徑7.34 mm，單芯絕緣約1.1 mm。 |

JLC：[費率](https://jlcpcb.com/help/article/pcb-assembly-price)、[FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs)、[BOM 格式](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly)、[KiCad 匯出](https://jlcpcb.com/help/article/how-to-generate-bom-and-centroid-files-from-kicad-8)。所有未列於上表的被動元件，精確品牌／規格／C 編號見完整 BOM 與對應 catalog 記錄。

B.2 local indicators: [JLC C2286 / KT-0603R](https://jlcpcb.com/partdetail/C2286) and [JLC C2297 / KT-0805G](https://jlcpcb.com/partdetail/C2297), checked2026-10-14. Basic SMT for Economic/Standard; 20 red +2 green per controller. Existing RJ45 LINK/ACT remain. LED behavioral voltage drops are analysis assumptions, not vendor SPICE models.

## R.2 manufacturing geometry, 2026-10-14

[JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities): reviewed 1/2-layer 1 oz track/space, through-via and silk limits. R.2 uses 0.15 mm track/space, 0.6/0.3 mm vias, 1 mm silk text and 0.15 mm strokes. This is a geometry comparison, not factory DFM acceptance or controlled-impedance qualification. LED cathode-silk footprints preserve KiCad library copper lands; artwork changes are generated in scripts/make-led-footprints.py.
