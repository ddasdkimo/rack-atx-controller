#!/usr/bin/env python3
"""Reproduce supplier-preview CPL corrections; this does not release production."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source = ROOT/'hardware/manufacturing/R3-candidate/controller/controller-cpl.csv'
board = ROOT/'hardware/cad/B2/rack-atx-controller.kicad_pcb'
cal = json.loads((ROOT/'hardware/research/jlc-r3-cpl-calibration.json').read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(source) == cal['native_cpl_sha256'], 'Native CPL changed; recalibration required'
assert sha(board) == cal['board_sha256'], 'PCB changed; recalibration required'
assert args.output.resolve() != source.resolve(), 'Never overwrite the native CPL'
rows = list(csv.DictReader(source.open()))
refs = {row['Designator'] for row in rows}
assert len(rows) == len(refs) == 300
bom = json.loads((ROOT/'hardware/research/jlc-r3-bom-quote.json').read_text())
codes = {ref:part['code'] for part in bom['parts'] for ref in part['designators']}
assert refs == set(codes)
corrections = {rule['ref']:rule for rule in cal['corrections']}
assert len(corrections) == len(cal['corrections']) and set(corrections) <= refs
for row in rows:
    rule = corrections.get(row['Designator'])
    if rule is None:
        continue
    assert codes[row['Designator']] == rule['code'], 'Part number changed'
    for column, delta in [('Mid X', 'dx_mm'), ('Mid Y', 'dy_mm')]:
        row[column] = f"{float(row[column][:-2]) + rule[delta]:.6f}mm"
    row['Rotation'] = str((float(row['Rotation']) + rule['rotation_delta_deg']) % 360)
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open('w', newline='') as out:
    writer = csv.DictWriter(out, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(f"Preview only: {len(rows)} components, {len(corrections)} corrections; {sha(args.output)}")
print('NOT FOR PRODUCTION: supplier placement, factory DFM and final review remain required.')
