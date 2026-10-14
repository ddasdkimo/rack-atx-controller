# Active CAD: B.2 schematic / R.2 routing

Open `B2/rack-atx-controller.kicad_pro` for the controller schematic; `B2/adapter.kicad_pro` for the six-component passive adapter; `B2/rack-atx-controller.kicad_pcb` in PCB Editor for the 100×110 mm routed candidate. Routing was authorized by the user. No Gerber or CPL exists.

The B.2 controller contains 300 electrical components; the placement adds four M3 holes. The controller has 2,754 track segments and 185 vias; the 26×34 mm adapter has 30 segments and no vias. Both boards have zero native unconnected items and configured DRC violations. The web 3D uses native placement, copper and adapter coordinates with simplified component envelopes. USB/Ethernet qualification, factory DFM and physical tests remain; see ../ROUTING-R2.md. Generators write into B2/placement to preserve the routed master.

```sh
python3 scripts/make-schematic.py
kicad-cli sch export netlist --format kicadxml -o artifacts/local/controller.xml hardware/cad/B2/rack-atx-controller.kicad_sch
kicad-cli sch export netlist --format kicadxml -o artifacts/local/adapter.xml hardware/cad/B2/adapter.kicad_sch
kicad-cli sch erc --format json -o artifacts/local/erc.json hardware/cad/B2/rack-atx-controller.kicad_sch
kicad-cli sch erc --format json -o artifacts/local/adapter-erc.json hardware/cad/B2/adapter.kicad_sch
python3 scripts/check-circuit.py
python3 hardware/simulation/run-b2.py
python3 scripts/cost.py
kicad-cli sch export pdf -o hardware/release/controller-schematic.pdf hardware/cad/B2/rack-atx-controller.kicad_sch
kicad-cli sch export pdf -o hardware/release/adapter-schematic.pdf hardware/cad/B2/adapter.kicad_sch
```

Run from the repository root. Use KiCad's bundled Python (wx + pcbnew) for `scripts/make-layout-s3.py` and `scripts/check-layout-s3.py`, then `kicad-cli pcb drc --format json -o artifacts/local/s3-drc.json hardware/cad/B2/rack-atx-controller.kicad_pcb`. Export/ ERC operations on the same project must run sequentially. Source library paths in generators currently target macOS KiCad; adapt paths on other platforms.

BOM, schematic and PCB candidate footprints agree; custom TLP3122A and input-terminal land patterns live in `RackATX.pretty`, referenced relative to B2. Manufacturer/physical DFM qualification is still required. Raw CLI netlists stay ignored because they include workstation paths. Never publish them. Historical CAD in this directory and archive/B1 is retained, not the current revision.
