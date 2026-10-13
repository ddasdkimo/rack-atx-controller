# KiCad schematic review — B.1

Open `rack-atx-controller.kicad_pro` with KiCad 10, then its root schematic. The controller has a root index and 38 child sheets; the ten host channels have distinct references and isolated net names. Open `adapter.kicad_pro` separately for the identical passive adapter built ten times. Do not include adapter parts in the central-board placement file.

Native symbols and global net labels are electrically connected. `Rack.kicad_sym` and `sym-lib-table` are included; the schematic caches its symbols too. These are functional pin blocks, not simulated device models. PDF copies are under `../release/`.

`../../scripts/make-schematic.py` generates the CAD, `../circuit.json` and both BOM formats. Edit that source when changing connections or values, regenerate and review the diff. Change `../design.json`, notes and the 3D template for the same revision. The generator currently uses the standard macOS KiCad 10 symbol library to read ESP32 pin definitions; other systems should adjust that library path.

Five land-pattern families deliberately have no footprint assigned: TLP3122A, EL357N, B0505S-1WR3L, FNR4018 inductor and WJ500V input terminal. All other assigned footprints are candidates that still need dimensional/polarity review. Empty footprints are a layout release gate, not missing electrical connections. There is no `.kicad_pcb`, Gerber, DRC report or CPL in this release.

Reproduce checks with KiCad 10 CLI (replace `kicad-cli` with its installed absolute path if necessary):

```sh
python3 scripts/make-schematic.py
kicad-cli sch export netlist --format kicadxml -o artifacts/local/controller.xml hardware/cad/rack-atx-controller.kicad_sch
kicad-cli sch export netlist --format kicadxml -o artifacts/local/adapter.xml hardware/cad/adapter.kicad_sch
kicad-cli sch erc --format json -o artifacts/local/erc.json hardware/cad/rack-atx-controller.kicad_sch
kicad-cli sch erc --format json -o artifacts/local/adapter-erc.json hardware/cad/adapter.kicad_sch
python3 scripts/check-circuit.py
python3 scripts/cost.py
kicad-cli sch export pdf -o hardware/release/controller-schematic.pdf hardware/cad/rack-atx-controller.kicad_sch
kicad-cli sch export pdf -o hardware/release/adapter-schematic.pdf hardware/cad/adapter.kicad_sch
```

Execute from the repository root. Local raw netlists/reports are ignored because KiCad embeds absolute source paths. The public validation summary contains no local paths. ERC is run with normal rules, without suppressions; native netlist checks separately test intended pin mapping, connector NCs and isolation boundaries. Passing these checks does not establish motherboard compatibility or manufacturability.
