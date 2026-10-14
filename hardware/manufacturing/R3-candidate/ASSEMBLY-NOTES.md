# R.3 engineering review package — NOT FOR PRODUCTION

This package is for quotation and independent engineering review. Factory DFM, component orientation preview and the final release review are pending. No purchase or production is authorized.

## Contents and reference

Controller: 100×110 mm, two layers, 1.6 mm FR4, 1 oz outer copper, green mask, white silk, 300 electrical parts. Adapter: 26×34 mm, two layers, six through-hole connector parts; ten adapters serve one controller. ZIPs contain Gerber copper/mask/silk/top-paste/outline and separate plated/nonplated Excellon drills. Native CAD is under `hardware/cad/B2`; SHA256 identities and file checksums are in `manifest.json`.

`cam-audit.json` independently parses Gerber/Excellon using Gerbonara: outlines close, all 380 controller round holes and four plated USB slots match native CAD, all 20 adapter holes match, and BOM/CPL references and coordinates match. Maximum drill rounding is 0.000708 mm. Front/back CAM SVGs were visually inspected; the QFN detail comes from actual CAM data.

CPL uses mm, native absolute board origin, X right and Y up (negative values on this board), all Top. Rotation is native KiCad degrees modulo 360. **These are not certified JLC library rotations.** Confirm every polarized/directional part in the supplier preview. No guessed blanket rotation offsets have been applied. Through-hole parts are included for assembly quotation; confirm Economic manual/wave assembly eligibility and charges. Adapter has no paste openings because every component is through-hole.

## Mandatory orientation checks

| Part | Electrical/physical correspondence | Evidence and remaining check |
|---|---|---|
| D101–D120 KT-0603R C2286; D201/D202 KT-0805G C2297 | KiCad pad 1 = K/negative, pad 2 = A/positive. **KENTO drawing numbers these terminals 2 = K, 1 = A.** Place the green cathode mark over CAD pad 1. Do not align by the numeric label alone. | KENTO original drawings in JLC catalog, p.2, visually inspected 2026-10-15. Native 0603 pads 0.875×0.95 mm with 0.70 mm inner gap; 0805 pads 0.975×1.40 mm with 0.90 mm gap. KiCad lands are intentionally not exact copies of the manufacturer's illustrative recommendation. Verify factory LED preview. |
| Q1/Q4 AO3401A C15127 | G1/S2/D3; gate-side index mark; SOT-23 | AOS original December2023 Rev3.1 drawing p.1; native pins match. Factory rotation pending. |
| MMBT3904 C20526 | B1/E2/C3 | Jiangsu Changjing original Rev2.1 p.1; native SOT-23 pin map matches. |
| U1 AP63203WU-7 C780769 | FB1/EN2/VIN3/GND4/SW5/BST6 | Diodes original November2024 Rev3-2 p.1; native TSOT-23-6 pins match. |
| D1 PRTR5V0U2X C12333 | GND1/I/O2/I/O3/VCC4 | Nexperia 1Apr2023 Rev4 p.2; native SOT-143 map matches. Larger pad1 is GND. |
| Host PESD5V0S2BT C2841440 | Bidirectional channels pins1/2, common pin3 = that host's reference only | TECHPUBLIC original circuit p.1 visually verified. Never connect different host references or GND_CTRL together. |
| J105 HR911105A C12074 | Green A9/K10; yellow **K11/A12**. Native pin11 ETH_ACT_N, pin12 RJ_LED_Y_A. | HANRUN original schematic p.1 and component-side mechanical drawing p.3; 0.89 signal,1.02 LED,1.63 shield and3.25 locating holes match. |
| Twenty TLP3122A | A1/K3, bilateral contact4/6 | Toshiba original SO6 land pattern checked in pre-release audit; 0.8×1.2 pads,2.54 pitch,6.3 opposing centres. |
| J01–J10 S10B-PHDSS | Outward mating direction; custom harness pins1/2POWER,3/4RESET,9HOST_REF;5–8/10NC | JST PHD original drawing and all ten instances checked; see `hardware/validation/jst-phd-audit.json`. |
| U2/U3, U4–U8, Y1/Y2, USB J104 | Check package index, pin1 and connector mating direction against native assembly view and original part drawing | Native schematic/PCB parity passes; supplier-specific preview still required for the entire BOM, not just the rows above. |

Catalog original documents: [red LED](https://jlcpcb.com/partdetail/Hubei_KENTOElec-KT0603R/C2286), [green LED](https://jlcpcb.com/partdetail/Hubei_KENTOElec-KT0805G/C2297), [AOS](https://www.aosmd.com/pdfs/datasheet/AO3401A.pdf). Other source identities are retained in `hardware/circuit.json` and the BOM. These checks are nominal drawing/geometry checks, not evidence of received-part fit or factory acceptance.

## QFN process request for factory DFM

U2 has a 4×4 mm exposed pad, nine plated 0.30 mm holes with 0.60 mm copper pads on a1mm grid, and16rounded0.75×0.75 mm stencil windows with nominal55.39% coverage. CAM confirms no paste-window/drill overlap; conservative square-window gap is0.027mm. The actual holes remain inside the exposed copper pad. Bottom mask has no openings under EPAD; **tented is not filled/capped**.

Request a manufacturable, cost-conscious process using normal lead time: first evaluate the current bottom-tented process and ENIG against a qualified HASL option. Ask whether epoxy-filled/capped vias are mandatory, whether tenting can survive assembly, and how solder wicking/voiding and inspection are controlled. Proposed stencil thickness around0.10mm requires factory confirmation, including window webs and escape-pad apertures. Do not substitute ordinary ink-plugging where JLC excludes one-sided/via-in-pad holes. Any DFM-driven copper/paste/finish change requires re-export and re-review.

The two-layer USB/MDI geometry was independently reviewed for prototype use. It is not a guaranteed controlled-impedance stackup. USB/Ethernet interoperability, 3.3V transient margin, timer limits, cold boot, failure-state output release, LED visibility and all ten host connections require prototype testing before deployment.
