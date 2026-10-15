# JLCPCB selection and costs — B.2

All 300 central-board parts use catalog-backed JLC identifiers; 46 unique part numbers. Retained catalog observations are dated2026-10-13; new KT-0603R C2286 (20 per board), KT-0805G C2297 (2 per board), MC14541BDR2G C7292 and CL10C102JB8NNNC C163508 were checked2026-10-14 and available for Economic/Standard assembly. R.3 uses 0402 C1525/C15195/C25120 (Basic) and C318580 (Extended), rechecked2026-10-15. Stock is observed, not reserved. Recheck before fabrication.

[Controller BOM](bom/controller-bom.csv) · [JLC format](bom/controller-jlc-bom.csv) · [Adapter BOM](bom/adapter-bom.csv) · [machine-readable cost model](bom/cost-model.json).

## Actual five-controller quote, 2026-10-15

Final R.3 Gerber, BOM and CPL were uploaded in the authenticated JLC quote flow. Normal Economic, top-side assembly, five 100×110 mm two-layer boards, 1.6 mm / 1 oz / green, ENIG 1 µin, tented vias:

| Item | USD for five boards |
|---|---:|
| Bare PCB, including production-file confirmation | 28.25 |
| 46 component SKUs, including displayed purchase overage | 168.86 |
| Assembly-related fees | 78.37 |
| **Populated controllers, excluding freight/tax** | **275.48** |

PCB plus components is **197.11 USD**; populated-board average is **55.096 USD**. This is a live quotation, not a purchase, accepted factory DFM, complete equipment price or offer to supply loose parts. All 300 references / 46 SKUs were selected. Stock is not reserved. [Previous quote screenshot (historical)](research/jlc-r3-economic-5pcs-20261015.png) · [Structured observation](research/jlc-r3-quote-observations.json) · [Per-SKU purchase quantities and costs](research/jlc-r3-bom-quote.json).

Assembly-related fees: setup8.24, stencil1.55, Extended loading46.35, SMT7.36, placement confirmation0.45, manual setup3.61, manual assembly9.90 and nitrogen0.91 USD. The site lists PCB24hours and assembly2–3days with zero expedite charge. No unlisted charges are added to this displayed quote. Freight and tax are outside it. If the factory requires a technical process change, obtain its explanation and revised quotation before updating the cost.

## Placement and process gates

**Not ready for production.** The native CPL reproduces KiCad anchors and rotations; JLC preview exposed connector-anchor and per-MPN rotation mismatches. Trial4 corrections have been reproduced and independently reviewed: all300 references,46SKUs and15 connector pad-centres agree. Supplemental U4–U6/J102/J103 previews are complete. HXY C5451656 replaces C2841440. Trial5 adds20rotations(+180degrees) with full models, D2/D12 pin1 closeups and all20numeric checks. J105 full pin/anchor mapping remains a factory gate. See [release checklist](RELEASE-CHECKLIST.md). The native PCB/copper has not been changed to disguise these mismatches.

[Manufacturing review package](manufacturing/R3-candidate/) contains native Gerber/drill/BOM/CPL and independent CAM checks. Those checks establish native parity, not supplier placement qualification. The existing fixed reviewer snapshot is retained. A final calibrated package needs a fresh review by the same CLI reviewer.

U2 QFN via/paste DFM remains pending: nine exposed-pad vias, bottom tenting and16paste windows require factory confirmation of solder wicking, voiding, stencil and finish. Tenting is not filled/capped. Earlier bare-PCB calculator options were9.30USD(HASL/tented),27.20USD(ENIG/tented) and82.99USD(ENIG/filled-capped); they excluded the later1.05USD production-file confirmation. None is factory-qualified. Earlier five-board parts estimate162.38USD remains only as historical planning data; use the actual168.86USD for this quote.

Twenty TLP3122A preserve bidirectional dry contacts. Ten isolated DC/DC modules and host LED-sensing circuits remain removed. No unverified cheaper substitute is selected. Slower economical shipping is preferred; waiting does not automatically waive fixed fees.

The passive adapters need six connector parts each; price and one-board central-component estimate are in the cost model. Adapter PCBs/labor, harnesses, external PSU, enclosure, firmware and functional commissioning are excluded. JLC catalog parts pricing is a comparison baseline, not an offer to supply loose-component kits. Slower economical shipping is preferred when available; waiting does not automatically waive fixed fees.

Historical online calculator evidence remains in research/ and archive/B1/docs/; it applies only to the specific dimensions/configuration recorded.

## HXY button protection qualification, 2026-10-15

D2–D21 now use **HXY PESD5V0S2BT / C5451656**, a bidirectional dual TVS with common pin3. Exact HXY document: max1µA at5V, VBR6–8V, clamp8V@1A/9V@11A, typical20pF. SOT23 pad geometry is unchanged. The higher leakage than the former TECHPUBLIC part was checked rather than assumed interchangeable.

The accepted prototype interface is an active-low POWER/RESET input at3–5V with pull-up ≤47kΩ, one button terminal and HOST_REF connected to the same verified host ground. A/B may be exchanged. Assuming VIH=0.7VDD/VIL=0.3VDD,1µA TVS+1µA relay off leakage adds0.052V drop at26kΩ. Adding1µA host allowance gives0.141V drop at47kΩ. A10µA TVS sensitivity study retains at least0.336V open margin in this envelope. [60-case ngspice analysis](validation/hxy-button-leakage.json) and [repeatable checker](simulation/check-button-leakage.py).

These are bounded DC assumptions, not actual motherboard qualification. HXY does not guarantee a hot-temperature leakage curve; verify actual idle voltage, pull-up/thresholds and warm operation before deployment. Exploratory100kΩ stress cases can fail and are not accepted. ESD robustness still requires physical testing.

Trial5 uses a per-MPN+180° supplier rotation for all20TVS. Full-board models are present; D2 and D12 closeups verify both orientation classes; all20numeric transforms are checked against nativepads. [Preview evidence](validation/hxy-cpl-preview-checks.json) · [supplier CPL candidate](manufacturing/R3-candidate/controller-cpl-jlc-trial5.csv). This is not a universal KiCad/JLC angle rule.

JLC selected104TVS for100installed, $3.2136. All46SKUs remain selected. The refreshed five-controller total is275.48USD, versus275.81USD previously; the0.33USD net reduction also includes small price changes elsewhere.50assembledadapters remain63.10USD and SF combined freight12.21USD, total350.79USD before importtax/clearance and equipment/harnesses.

The same designated CLI independently completed the HXY/Trial5 bounded review with no new blockers; [review summary](validation/hxy-peer-review.json). The old TVS placeholder gate is closed. Final factory-resolved review remains required. The 5V boundary is strict: rails above5V are outside the specified leakage envelope, not automatically covered by the10x sensitivity assumption.
