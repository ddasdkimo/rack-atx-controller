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

Revision A is an architecture and wiring visualization, not fabrication output. There are no validated schematics, Gerbers, production footprints or electrical simulations yet. Keep that status visible until the relevant validation has actually been completed.
