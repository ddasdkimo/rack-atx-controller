# JLCPCB selection and costs — B.2

All 300 central-board parts use catalog-backed JLC identifiers; 46 unique part numbers. Retained catalog observations are dated2026-10-13; new KT-0603R C2286 (20 per board), KT-0805G C2297 (2 per board), MC14541BDR2G C7292 and CL10C102JB8NNNC C163508 were checked2026-10-14 and available for Economic/Standard assembly. R.3 uses 0402 C1525/C15195/C25120 (Basic) and C318580 (Extended), rechecked2026-10-15. Stock is observed, not reserved. Recheck before fabrication.

[Controller BOM](bom/controller-bom.csv) · [JLC format](bom/controller-jlc-bom.csv) · [Adapter BOM](bom/adapter-bom.csv) · [machine-readable cost model](bom/cost-model.json).

| Central boards populated | Parts only USD | Parts plus assembly USD, excluding bare PCB |
|---|---:|---:|
| 2 | 69.74 | 139.44–158.28 |
| 5 | 162.38 | 246.93–263.31 |

R.3 100×110 mm Gerber was uploaded to the JLCPCB calculator on2026-10-15. Five bare PCBs, two layers/1.6mm/1oz/green/TG135, normal lead time, produced the following **unaccepted process options**:

| Five-board process | Bare PCB USD | PCB + parts USD | Fully soldered planning total USD, excluding freight/tax/extras |
|---|---:|---:|---:|
| HASL with lead + bottom-tented vias | 9.30 | 171.68 | 256.23–272.61 |
| ENIG1µin + bottom-tented vias | 27.20 | 189.58 | 274.13–290.51 |
| ENIG + epoxy-filled/capped vias | 82.99 | 245.37 | 329.92–346.30 |

The bare PCB column is an observed calculator result; the other columns add the component/assembly model above, **not a completed PCBA quotation**. QFN via/paste DFM determines which option is usable. Filled/capped adds52.35 plus3.44 horizontal plating relative to ENIG/tented. Delivery destination, freight, tax, attrition/MOQ and process extras remain unknown. No expedited service or coupon was used. The upload predates18silkscreen labels; copper/drill geometry is unchanged, but final ZIP must be re-uploaded for acceptance. [Structured observation](research/jlc-r3-quote-observations.json).

[Manufacturing review package](manufacturing/R3-candidate/) now includes Gerber/drill/BOM/CPL and independent CAM checks. JLC's full PCBA quote flow is waiting for user confirmation of Assembly Service terms; no order or DFM acceptance exists. Historical S.1 prices must not be reused.

Fee assumptions follow [JLC's official assembly price page](https://jlcpcb.com/help/article/pcb-assembly-price), updated2026-09-09, checked2026-10-14: one-side Economic, normal lead time, no expedite or coupons. Fixed setup/stencil/confirmation/manual setup total13.74USD; Extended loading3.07USD/type; SMT0.0016/joint; manual0.0164/joint. X-ray and through-hole Extended loading treatment are modeled as ranges pending supplier classification. Extra pre-reflow, fixtures and process changes are excluded. Model contains exact joint/SKU counts and all assumptions.

Five-board parts save61.89USD (27.6%) versus B.1's224.27USD. The MC14541B uses a single new C0G value and existing Basic resistors to limit new feeder types. Twenty TLP3122A remain to preserve bidirectional dry contacts. Ten DC/DC modules and their LED-sensing circuitry are removed. Connector type remains stable; no unverified cheaper substitute is marked selected.

The passive adapters need six connector parts each; price and one-board central-component estimate are in the cost model. Adapter PCBs/labor, harnesses, external PSU, enclosure, firmware and functional commissioning are excluded. JLC catalog parts pricing is a comparison baseline, not an offer to supply loose-component kits. Slower economical shipping is preferred when available; waiting does not automatically waive fixed fees.

Historical online calculator evidence remains in research/ and archive/B1/docs/; it applies only to the specific dimensions/configuration recorded.
