# JLCPCB selection and costs — B.2

All 300 central-board parts use catalog-backed JLC identifiers; 46 unique part numbers. Retained catalog observations are dated2026-10-13; new KT-0603R C2286 (20 per board), KT-0805G C2297 (2 per board), MC14541BDR2G C7292 and CL10C102JB8NNNC C163508 were checked2026-10-14 and available for Economic/Standard assembly. R.3 uses 0402 C1525/C15195/C25120 (Basic) and C318580 (Extended), rechecked2026-10-15. Stock is observed, not reserved. Recheck before fabrication.

[Controller BOM](bom/controller-bom.csv) · [JLC format](bom/controller-jlc-bom.csv) · [Adapter BOM](bom/adapter-bom.csv) · [machine-readable cost model](bom/cost-model.json).

## Actual five-controller quote, 2026-10-15

Final R.3 Gerber, BOM and CPL were uploaded in the authenticated JLC quote flow. Normal Economic, top-side assembly, five 100×110 mm two-layer boards, 1.6 mm / 1 oz / green, ENIG 1 µin, tented vias:

| Item | USD for five boards |
|---|---:|
| Bare PCB, including production-file confirmation | 28.25 |
| 46 component SKUs, including displayed purchase overage | 169.19 |
| Assembly-related fees | 78.37 |
| **Populated controllers, excluding freight/tax** | **275.81** |

PCB plus components is **197.44 USD**; populated-board average is **55.162 USD**. This is a live quotation, not a purchase, accepted factory DFM, complete equipment price or offer to supply loose parts. All 300 references / 46 SKUs were selected. Stock is not reserved. [Quote screenshot](research/jlc-r3-economic-5pcs-20261015.png) · [Structured observation](research/jlc-r3-quote-observations.json) · [Per-SKU purchase quantities and costs](research/jlc-r3-bom-quote.json).

Assembly-related fees: setup8.24, stencil1.55, Extended loading46.35, SMT7.36, placement confirmation0.45, manual setup3.61, manual assembly9.90 and nitrogen0.91 USD. The site lists PCB24hours and assembly2–3days with zero expedite charge. X-ray has no separate line; that does not establish that inspection is included or unnecessary. Freight, tax and DFM-driven process changes remain unknown.

## Placement and process gates

**Not ready for production.** The native CPL reproduces KiCad anchors and rotations; JLC preview exposed connector-anchor and per-MPN rotation mismatches. Supplier-calibrated coordinates are being checked against real pad positions, pin1 and cathodes. Browser preview corrections must be reproduced in an exported file and independently reviewed. The native PCB/copper has not been changed to disguise these mismatches.

[Manufacturing review package](manufacturing/R3-candidate/) contains native Gerber/drill/BOM/CPL and independent CAM checks. Those checks establish native parity, not supplier placement qualification. The existing fixed reviewer snapshot is retained. A final calibrated package needs a fresh review by the same CLI reviewer.

U2 QFN via/paste DFM remains pending: nine exposed-pad vias, bottom tenting and16paste windows require factory confirmation of solder wicking, voiding, stencil and finish. Tenting is not filled/capped. Earlier bare-PCB calculator options were9.30USD(HASL/tented),27.20USD(ENIG/tented) and82.99USD(ENIG/filled-capped); they excluded the later1.05USD production-file confirmation. None is factory-qualified. Earlier five-board parts estimate162.38USD remains only as historical planning data; use the actual169.19USD for this quote.

Twenty TLP3122A preserve bidirectional dry contacts. Ten isolated DC/DC modules and host LED-sensing circuits remain removed. No unverified cheaper substitute is selected. Slower economical shipping is preferred; waiting does not automatically waive fixed fees.

The passive adapters need six connector parts each; price and one-board central-component estimate are in the cost model. Adapter PCBs/labor, harnesses, external PSU, enclosure, firmware and functional commissioning are excluded. JLC catalog parts pricing is a comparison baseline, not an offer to supply loose-component kits. Slower economical shipping is preferred when available; waiting does not automatically waive fixed fees.

Historical online calculator evidence remains in research/ and archive/B1/docs/; it applies only to the specific dimensions/configuration recorded.
