# Change log

## A.2 — 2026-10-13

- Clarify that each host adapter is an unpowered wiring splitter; a custom Y harness can replace it.
- Add real candidate connector parts: Molex 43045-1000, 43025-1000 and 43030-0007, plus Belden 9505 cable.
- Record wire-pair colors, spare conductor, separate shield/drain treatment, and assembly quantities.
- Replace the provisional cavity drawing claim with a signal-allocation table pending manufacturer drawing review.
- Revise the conceptual connector shape to a right-angle shrouded header and enlarge the illustrative board envelope to 280 × 220 mm for connector spacing.
- Publish the discussion model with public access and retain source in GitHub.
- Record JLCPCB / PCBA as the preferred fabrication and component-availability workflow, without claiming verified stock or manufacturing readiness.

## A.1 — 2026-10-13

- Initial 10-host centralized hardware architecture and two-host 3D wiring example.
- Preserve original case POWER/RESET switches and power/HDD LEDs through passive adapter traces.
- Define custom 10-pin controller connector: four signal pairs, one host reference, one unconnected pin.
- Plan high-impedance differential LED sensing with an independently powered isolated domain per host.
- Keep board geometry, component candidates and motherboard headers explicitly at concept status.
- Require synchronized circuit, 3D, connector and wiring updates for future revisions.
