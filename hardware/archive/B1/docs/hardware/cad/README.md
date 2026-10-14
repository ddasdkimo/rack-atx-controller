> **目前已進入 R.0 局部佈線，尚未全板連通。** S.2 為保留的布局基準；以下舊版「待確認／未佈線」敘述屬歷史狀態。

# KiCad schematic review — B.1

> 目前布局為 S.2（200×170 mm），待使用者確認，尚未佈線。以下 S.1 尺寸／費用／52 個佔位敘述為歷史紀錄；S.2 已補焊盤，詳見 [布局審閱](../LAYOUT-S2.md)。舊尺寸報價不適用於 S.2。

Open `rack-atx-controller.kicad_pro` with KiCad 10, then its root schematic. The controller has a root index and 38 child sheets; the ten host channels have distinct references and isolated net names. Open `adapter.kicad_pro` separately for the identical passive adapter built ten times. Do not include adapter parts in the central-board placement file.

Native symbols and global net labels are electrically connected. `Rack.kicad_sym` and `sym-lib-table` are included; the schematic caches its symbols too. These are functional pin blocks, not simulated device models. PDF copies are under `../release/`.

`../../scripts/make-schematic.py` generates the CAD, `../circuit.json` and both BOM formats. Edit that source when changing connections or values, regenerate and review the diff. Change `../design.json`, notes and the 3D template for the same revision. The generator currently uses the standard macOS KiCad 10 symbol library to read ESP32 pin definitions; other systems should adjust that library path.

Five land-pattern families deliberately have no footprint assigned: TLP3122A, EL357N, B0505S-1WR3L, FNR4018 inductor and WJ500V input terminal. All other assigned footprints are candidates that still need dimensional/polarity review. Empty footprints are a layout release gate, not missing electrical connections. S.1 now adds `compact-S1-placement.kicad_pcb`: a 160×110 mm, 2-layer spatial packing study. It has 694 placements, including 52 pad-free envelopes for those five families. All assigned footprints remain candidates. There are no routed tracks, ground planes, mounting-hole design, Gerbers, DRC sign-off or CPL. Do not fabricate this file. Reference/net mapping on existing candidate pads is only a visual aid; missing envelopes do not represent electrical connectivity. View F.Fab/F.Courtyard and User.Drawings; crossed envelopes are intentionally incomplete.

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

The public 3D uses the same placement JSON (rotated 90° for cable visibility), with bounding boxes rather than qualified component models. See [compact study](../COMPACT-STUDY.md). Regenerate with the bundled KiCad Python and `scripts/make-placement-study.py`, then sync the derived study into `hardware/design.json` before rebuilding. The packing algorithm checks bounding-box overlap and outline only, not routing feasibility.
