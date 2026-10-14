# JLCPCB selection and costs — B.2

All 300 central-board parts use catalog-backed JLC identifiers; 43 unique part numbers. Retained catalog observations are dated2026-10-13; new KT-0603R C2286 (20 per board), KT-0805G C2297 (2 per board), MC14541BDR2G C7292 and CL10C102JB8NNNC C163508 were checked2026-10-14 and available for Economic/Standard assembly. Stock is observed, not reserved. Recheck before fabrication.

[Controller BOM](bom/controller-bom.csv) · [JLC format](bom/controller-jlc-bom.csv) · [Adapter BOM](bom/adapter-bom.csv) · [machine-readable cost model](bom/cost-model.json).

| Central boards populated | Parts only USD | Parts plus assembly USD, excluding bare PCB |
|---|---:|---:|
| 2 | 69.80 | 136.42–155.26 |
| 5 | 162.53 | 244.01–260.39 |

S.3 100×110mm two-layer bare PCB cost is **pending a new quote**. Materials total=bare PCB+parts; fully soldered manufacturing total=bare PCB+parts+assembly; delivered total additionally includes freight/tax/attrition/MOQ/process extras. Unknown amounts are not zero. Historical S.1 US$14 for160×110mm must not be reused for S.3. No accepted Gerber/CPL quote or order exists.

Fee assumptions follow [JLC's official assembly price page](https://jlcpcb.com/help/article/pcb-assembly-price), updated2026-09-09, checked2026-10-14: one-side Economic, normal lead time, no expedite or coupons. Fixed setup/stencil/confirmation/manual setup total13.74USD; Extended loading3.07USD/type; SMT0.0016/joint; manual0.0164/joint. X-ray and through-hole Extended loading treatment are modeled as ranges pending supplier classification. Extra pre-reflow, fixtures and process changes are excluded. Model contains exact joint/SKU counts and all assumptions.

Five-board parts save61.74USD (27.5%) versus B.1's224.27USD. The MC14541B uses a single new C0G value and existing Basic resistors to limit new feeder types. Twenty TLP3122A remain to preserve bidirectional dry contacts. Ten DC/DC modules and their LED-sensing circuitry are removed. Connector type remains stable; no unverified cheaper substitute is marked selected.

The passive adapters need six connector parts each; price and one-board central-component estimate are in the cost model. Adapter PCBs/labor, harnesses, external PSU, enclosure, firmware and functional commissioning are excluded. JLC catalog parts pricing is a comparison baseline, not an offer to supply loose-component kits. Slower economical shipping is preferred when available; waiting does not automatically waive fixed fees.

Historical online calculator evidence remains in research/ and archive/B1/docs/; it applies only to the specific dimensions/configuration recorded.
