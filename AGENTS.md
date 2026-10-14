# Rack ATX controller maintenance

This is the user's public hardware planning repository for a 10-host rack controller.

## Required synchronized updates

The user explicitly requests that every future circuit or board refinement also update the 3D model and wiring illustration.

- Treat `hardware/design.json` as the source of truth for revisions, host/channel counts, connector pin assignments, functional blocks and candidate quantities.
- When changing a circuit, connector, cable, board outline, component placement or isolation boundary, update the hardware notes, `visualization/viewer.template.html`, generated viewer files and `CHANGELOG.md` in the same change.
- Regenerate with `python3 scripts/build.py`, run `python3 scripts/check.py`, and visually inspect overview, controller, both simulated PCs, and the wiring view at desktop and mobile widths.
- Never present concept geometry as a routed PCB, manufacturable CAD, tested schematic, or a verified motherboard header pinout.
- Do not invent universal F_PANEL pin numbers. The numbered Jxx connector belongs to this custom controller; motherboard signals must be mapped from the actual board manual.
- Preserve original case switches and LEDs through passive straight-through connections; sensing is a limited-load parallel branch. Verify power-off loading and backfeed when designing the real input circuit.
- Keep all ten host signal domains isolated from controller ground and each other. A host's reference wire belongs only to that host's isolated sensing domain.
- Keep Git history public-safe: no credentials, local paths, private host inventory, or SSH keys. Do not publish unrelated workspace files.

## Scope

## Manufacturing preference

The user requests considering JLCPCB PCB fabrication / PCBA and its available parts. Prefer components actually supported by JLCPCB assembly when electrically appropriate. Record manufacturer part number, exact LCSC/JLC part number, package, assembly method, library classification, stock-check date and verification status. An LCSC listing is not proof of JLC assembly stock. Recheck availability before board release. Keep unverified IDs null; never invent part numbers or mark this concept as order-ready. Cable assemblies and motherboard-specific leads require separate sourcing/assembly verification.

## Current release scope

Revision B.1 includes native KiCad schematics, catalog-backed BOM and analytical checks. No routed PCB, Gerbers, CPL, qualified footprints, SPICE run or physical prototype validation exists. Keep this boundary visible. Regenerate circuit/BOM via scripts/make-schematic.py, export both native KiCad netlists and ERC reports, run scripts/check-circuit.py and scripts/cost.py; update the cost summary in hardware/design.json and PDFs with the same circuit revision before rebuilding the viewer. Never publish raw KiCad netlists with absolute workstation paths.

## S.1 placement and purchasing

The user is not in a hurry. Prefer normal lead time, one-side Economic PCBA and economical available shipping; do not assume waiting creates an automatic discount. S.1 adds a spatial study, not a fabrication PCB. Preserve the 5-family/52-envelope limitation and distinguish bounding-box checks from DRC and isolation approval. Sync placement-study.json into design.json when regenerating. Keep the full BOM review page current with cost data; distinguish one controller from five.

## Current architecture decision

The user returned to one integrated controller for ten hosts (B.1 electrical / S.1 placement). P.0 external-ESP32 breakaway research is archived, not selected. Retain its cost evidence and mark prototype-plan.json and design.next_prototype consistently. S.1 has zero routed tracks and still needs qualified footprints, routing and DRC; do not claim two-layer routing success.

## S.2 placement confirmation gate

Current layout: 200x170 mm S.2, two banks of five hosts, all 694 electrical footprints have pads plus four M3 mounting holes. The five previous envelope families are now drawing-transcribed or library footprints; not factory-qualified. Preserve S.1 as historical only. Regenerate with make-layout-review.py and audit with check-layout-review.py in KiCad Python. Sync layout-review-checks.json, layout SVG, design.layout_study, viewer and layout.html. The user now authorizes routing automatically once the standards-based pre-routing audit passes. Unverified or failed checks must not be marked passed to bypass this condition. One-board parts budget is separate; do not apply the old S.1 PCB price to S.2.
