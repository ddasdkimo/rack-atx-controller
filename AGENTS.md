# Rack ATX controller maintenance

This public hardware repository is a ten-host controller. Current source of truth: hardware/design.json for architecture,connector mapping and active revisions; scripts/make-schematic.py/hardware/circuit.json for B.2 electrical connectivity; hardware/placement-S3.json for the immutable S.3 baseline; R.3 actual placements are native CAD and routing-R3.json component_overrides. Keep them synchronized.

## Current scope and approval gate

B.2 has POWER/RESET only, no host LED sensing. S.3 is100×110mm,two layers,300electrical components+4M3holes. Latest user instruction authorizes routing after checking placement: 「剩下就是持續完成板子 檢查零件佈局 並跑完線路」. B.2/S.3 baseline checks and R.3 routing geometry review passed; routing is connected on both controller and adapter. Current copper source: hardware/cad/B2/*.kicad_pcb. Placement generators must write B2/placement and never silently overwrite routed masters. Validate with scripts/validate-routing-r3.py and update hardware/ROUTING-R3.md; do not treat zero DRC as USB/Ethernet or manufacturing qualification. Do not resume obsolete B.1/R.1 connectivity. Preserve all historical designs and local checkpoints. No purchase or manufacturing release is authorized.

Original case POWER/RESET buttons connect through a passive parallel adapter; original LEDs stay directly on motherboard and never connect to the adapter/controller. HOST_REF is still required by the retained button TVS topology. Keep each host domain separate from all others and GND_CTRL. Do not invent universal F_PANEL pin numbers. Current customJST pins1/2=POWER,3/4=RESET,9=hostESDreference;5–8/10=NC.

## Required synchronized updates

Every circuit/connector/cable/outline/placement change updates native schematic,BOM,3D/wiring,public pages,hardware notes and CHANGELOG in the same change. Rebuild withscripts/build.py; checkscripts/check.py. Visually inspect overview,controller,both simulatedPCs andwiring atdesktop/mobile. Central3D coordinates come fromS.3; component envelopes and simulatedPCs are not precision mechanical models.

Use scripts/make-schematic.py, nativeKiCad export/ERC, scripts/check-circuit.py, hardware/simulation/run-b2.py and scripts/cost.py. Use KiCad's wx/pcbnew Python for make-layout-s3.py/check-layout-s3.py. Do not run native exports/ERC concurrently against the same project. The archival B.1 simulation/route scripts must not overwrite currentB.2 summaries or manifest.

## Evidence and manufacturing

Prefer actualJLC assembly catalog parts; record exactMPN,C-number,package,classification,assemblymethod,stock/date andsource. LCSC availability alone is not assembly stock. Preserve unknowns; recheck before release. Current footprint candidates have real pads but are not physically/factoryqualified. NoGerber/CPL or acceptedPCBAquote exists. NewS.3 bare-board cost is pending; do not reuse oldS.1/S.2 estimates.

User prefers economical normal lead time,one-sideEconomicPCBA,noexpedite andcheaperavailablefreight. Waiting is not an automatic discount. Separate barePCB,parts,assembly,freight/tax andequipmentcosts.

B.2 behavior study passes16corners+9cases,including an assumed±25%clockstress envelope. It is not a vendor oscillator model,physicalprototypeorcompatibilitytest. Keep these limits visible. Practical original-manufacturer guidance and geometry checks guide placement; nofullIPCcomplianceclaim.

Keep Git/public files free of credentials,workstationpaths,privatehostinventory andrawnetlists. Ignore localbuilds/caches/tooloutputs andpreserve genuinebackups. Publicsite/GitHubupdates areauthorized for this work.

## Firmware (B.2)

firmware/ is an ESP-IDF v5.3 project for the B.2 control-only board. main/board.h is the single place that maps circuit.json signals to GPIOs, the 74HC595 chain order and the press timing limits; keep it in sync when the circuit or GPIO table changes. The protocol (firmware/PROTOCOL.md) makes the controller the sole lease arbiter between monitor nodes A and B; do not add endpoints that act without a lease or bypass the per-host policy. The firmware has been compiled but not run on hardware; say so wherever its status is described.

R.3 uses eight 0402 Ethernet passives and RackATX:ESP32_S3_QFN56_EP4_16Window. The source generator preserves B.2 pin nets. S.3 placement generation reads placement/circuit-baseline.json and must not be used to recreate R.3 placement. R.3 USB launch VBUS crossovers and the C34 pad-launch reference gap were reviewed as prototype limitations; do not silently add main-pair reference crossings.
