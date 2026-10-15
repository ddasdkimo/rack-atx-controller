#!/usr/bin/env python3
"""Read-only native-pad/CPL and package integrity check. Run with KiCad Python.

This checks the intended preview convention, not JLC's unpublished library
convention. Passing cannot qualify factory processes or release production.
"""
import argparse
import csv
import hashlib
import json
import math
import zipfile
from pathlib import Path

import wx
app = wx.App(False)
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cpl', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
package = ROOT / 'hardware/manufacturing/R3-candidate'
cal = json.loads((ROOT / 'hardware/research/jlc-r3-cpl-calibration.json').read_text())
manifest = json.loads((package / 'manifest.json').read_text())
assert sha(ROOT / 'hardware/circuit.json') == manifest['circuit_sha256']
file_count = zip_count = 0
for name, base in [('controller', 'rack-atx-controller'), ('adapter', 'adapter')]:
    expected = manifest['boards'][name]
    assert sha(ROOT / f'hardware/cad/B2/{base}.kicad_pcb') == expected['native_pcb_sha256']
    for relative, digest in expected['files'].items():
        assert sha(package / relative) == digest, relative
        file_count += 1
    archive = package / f'{name}-gerbers.zip'
    assert sha(archive) == expected['gerber_zip_sha256']
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert len(names) == len(set(names)), 'Duplicate ZIP member'
        for member in names:
            assert Path(member).name == member, 'Unexpected ZIP path'
            assert z.read(member) == (package / name / member).read_bytes(), member
            zip_count += 1

source = package / 'controller/controller-cpl.csv'
assert sha(source) == cal['native_cpl_sha256']
assert sha(ROOT / 'hardware/cad/B2/rack-atx-controller.kicad_pcb') == cal['board_sha256']

def rows_by_ref(path):
    rows = list(csv.DictReader(path.open()))
    refs = [r['Designator'] for r in rows]
    assert len(refs) == len(set(refs)), 'Duplicate reference'
    return dict(zip(refs, rows))

native, trial = rows_by_ref(source), rows_by_ref(args.cpl)
bom_rows = list(csv.DictReader((package / 'controller/controller-bom.csv').open()))
bom_refs = [ref.strip() for row in bom_rows for ref in row['Designator'].split(',')]
assert len(bom_refs) == len(set(bom_refs)) == len(trial) == 300
assert set(native) == set(trial) == set(bom_refs)
manufacturing_codes = {ref.strip(): row['LCSC Part #'] for row in bom_rows for ref in row['Designator'].split(',')}
bom_rows = list(csv.DictReader((ROOT / 'hardware/bom/controller-jlc-bom.csv').open()))
code_pairs = [(r.strip(), part['LCSC Part #']) for part in bom_rows for r in part['Designator'].split(',')]
assert len(code_pairs) == len(dict(code_pairs)) == 300
codes = dict(code_pairs)
assert set(codes) == set(trial) and len(set(codes.values())) == 46
for row in bom_rows:
    for ref in row['Designator'].split(','):
        assert manufacturing_codes[ref.strip()] == row['LCSC Part #'], 'Manufacturing BOM SKU mismatch'
rules = {r['ref']: r for r in cal['corrections']}
assert len(rules) == len(cal['corrections']) and set(rules) <= set(trial)
board = pcb.LoadBoard(str(ROOT / 'hardware/cad/B2/rack-atx-controller.kicad_pcb'))
footprints = {f.GetReference(): f for f in board.GetFootprints()}
assert set(footprints) == set(trial) | {'MH1', 'MH2', 'MH3', 'MH4'}
connectors = {f'J{i:02d}' for i in range(1, 11)} | {f'J{i}' for i in range(101, 106)}
mm = pcb.ToMM
num = lambda value: float(value.removesuffix('mm'))
results = []
pin1 = {}
for ref, row in trial.items():
    f = footprints[ref]
    pads = [p for p in f.Pads() if p.GetNumber() and p.GetAttribute() != pcb.PAD_ATTRIB_NPTH]
    xs, ys = [mm(p.GetPosition().x) for p in pads], [-mm(p.GetPosition().y) for p in pads]
    center = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2]
    anchor = [mm(f.GetPosition().x), -mm(f.GetPosition().y)]
    expected = center if ref in connectors else anchor
    actual = [num(row['Mid X']), num(row['Mid Y'])]
    error = math.dist(actual, expected)
    assert error < 0.000002, (ref, actual, expected)
    assert math.dist([num(native[ref]['Mid X']), num(native[ref]['Mid Y'])], anchor) < 0.000002
    assert abs(float(native[ref]['Rotation']) - f.GetOrientationDegrees() % 360) < 0.000001
    assert row['Layer'] == native[ref]['Layer'] == 'Top' and not f.IsFlipped()
    rule = rules.get(ref, {'dx_mm': 0, 'dy_mm': 0, 'rotation_delta_deg': 0})
    if ref in rules:
        assert rule['code'] == codes[ref]
    assert math.dist([anchor[0] + rule['dx_mm'], anchor[1] + rule['dy_mm']], expected) < 0.000002
    assert 0 <= float(row['Rotation']) < 360
    assert abs(float(row['Rotation']) - (f.GetOrientationDegrees() + rule['rotation_delta_deg']) % 360) < 0.000001
    results.append({'ref': ref, 'code': codes[ref], 'anchor': 'numbered-pad bbox' if ref in connectors else 'native', 'error_mm': round(error, 9)})
    if ref in {'U4', 'U5', 'U6', 'J102', 'J103'} | {f'D{i}' for i in range(2, 22)}:
        p1 = next(p for p in pads if p.GetNumber() == '1')
        dx, dy = mm(p1.GetPosition().x) - center[0], -mm(p1.GetPosition().y) - center[1]
        pin1[ref] = {'delta_from_pad_bbox_center_mm': [round(dx, 6), round(dy, 6)], 'CPL_rotation_deg': float(row['Rotation'])}

report = {
    'date': '2026-10-15', 'status': 'PASS intended preview geometry and file integrity; NOT FOR PRODUCTION',
    'native_pcb_sha256': cal['board_sha256'], 'trial_cpl_sha256': sha(args.cpl),
    'package_files_verified': file_count, 'zip_members_verified': zip_count,
    'references': len(results), 'unique_SKUs': len(set(codes.values())),
    'connector_centers_checked': len(connectors), 'other_native_anchors_checked': len(results) - len(connectors),
    'maximum_anchor_error_mm': max(r['error_mm'] for r in results),
    'supplemental_pin1_geometry': pin1, 'components': results,
    'limitations': ['Exact J105 supplier mapping and final factory-resolved review remain pending; HXY bounded review has separate evidence.', 'Pad-centre parity does not certify physical assembly, QFN process or signal integrity.'],
    'manufacturing_ready': False,
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(f'PASS: {len(results)} refs, {len(connectors)} independent pad centres, {file_count} package files, {zip_count} ZIP members; factory gates remain.')
