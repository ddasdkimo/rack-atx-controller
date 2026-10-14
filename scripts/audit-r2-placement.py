"""Independent placement / part-size audit of the R.2 board. Run with KiCad Python:
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 scripts/audit-r2-placement.py
Writes hardware/validation/r2-placement-audit.json. Not a manufacturing release check.
"""
import json, math, sys, itertools, collections
import wx
app = wx.App(False)
import pcbnew as p

import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
board = p.LoadBoard(ROOT + '/hardware/cad/B2/rack-atx-controller.kicad_pcb')
circuit = json.load(open(ROOT + '/hardware/circuit.json'))
parts = circuit['parts']
comp_by_ref = {c['ref']: c for c in circuit['components']}

mm = p.ToMM
bb = board.GetBoardEdgesBoundingBox()
print('board edge bbox mm', mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetWidth()), mm(bb.GetHeight()))
bx0, by0, bx1, by1 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetX() + bb.GetWidth()), mm(bb.GetY() + bb.GetHeight())

fps = list(board.GetFootprints())
print('footprints', len(fps))

def crt(fp):
    r = fp.GetCourtyard(p.F_CrtYd if fp.GetLayer() == p.F_Cu else p.B_CrtYd)
    if r.OutlineCount() == 0:
        return None
    b = r.BBox()
    return (mm(b.GetX()), mm(b.GetY()), mm(b.GetX() + b.GetWidth()), mm(b.GetY() + b.GetHeight()))

rows = []
side = collections.Counter()
tht = collections.Counter()
mismatch = []
no_crt = []
for fp in fps:
    ref = fp.GetReference()
    fid = str(fp.GetFPID().GetUniStringLibItemName())
    lib = str(fp.GetFPID().GetLibNickname())
    layer = 'F' if fp.GetLayer() == p.F_Cu else 'B'
    side[layer] += 1
    has_th = any(pd.GetAttribute() == p.PAD_ATTRIB_PTH for pd in fp.Pads())
    tht['THT' if has_th else 'SMD'] += 1
    c = crt(fp)
    if c is None:
        no_crt.append(ref)
    pos = fp.GetPosition()
    rows.append(dict(ref=ref, fp=f'{lib}:{fid}', layer=layer, x=mm(pos.x), y=mm(pos.y), rot=fp.GetOrientationDegrees(), crt=c, tht=has_th))
    comp = comp_by_ref.get(ref)
    if comp and comp['key'] in parts:
        want = parts[comp['key']]['footprint']
        if want and want != f'{lib}:{fid}':
            mismatch.append((ref, want, f'{lib}:{fid}'))
print('side', dict(side), 'mount', dict(tht))
print('footprint != circuit.json assignment:', mismatch[:10], 'count', len(mismatch))
print('no courtyard:', no_crt)

# courtyard gaps between all pairs (same side)
def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy) if (dx > 0 and dy > 0) else max(dx, dy)

overlaps = []
tight = []
for a, b in itertools.combinations([r for r in rows if r['crt']], 2):
    if a['layer'] != b['layer']:
        continue
    g = gap(a['crt'], b['crt'])
    if g <= 0:
        overlaps.append((a['ref'], b['ref'], round(g, 3)))
    elif g < 0.25:
        tight.append((a['ref'], b['ref'], round(g, 3)))
print('courtyard overlaps:', len(overlaps), overlaps[:12])
print('courtyard gap < 0.25 mm:', len(tight), sorted(tight, key=lambda t: t[2])[:15])
# gap histogram for SMD-SMD pairs
gaps = sorted(gap(a['crt'], b['crt']) for a, b in itertools.combinations([r for r in rows if r['crt'] and not r['tht']], 2) if a['layer'] == b['layer'])
print('smallest SMD-SMD courtyard gaps', [round(g, 3) for g in gaps[:8]])

# edge distance
edge = []
for r in rows:
    if not r['crt']:
        continue
    d = min(r['crt'][0] - bx0, r['crt'][1] - by0, bx1 - r['crt'][2], by1 - r['crt'][3])
    edge.append((round(d, 2), r['ref'], r['fp'].split(':')[1][:28]))
edge.sort()
print('closest to edge / overhanging (negative = beyond edge):', edge[:14])

# mounting holes
holes = []
for fp in fps:
    for pd in fp.Pads():
        if pd.GetAttribute() == p.PAD_ATTRIB_NPTH or (pd.GetAttribute() == p.PAD_ATTRIB_PTH and mm(pd.GetDrillSize().x) >= 3.0):
            holes.append((fp.GetReference(), mm(pd.GetPosition().x), mm(pd.GetPosition().y), mm(pd.GetDrillSize().x), mm(pd.GetSize().x)))
print('mounting/large holes:', holes)
# nearest copper-bearing courtyard to each hole
for h in holes:
    best = None
    for r in rows:
        if not r['crt'] or r['ref'] == h[0]:
            continue
        c = r['crt']
        dx = max(c[0] - h[1], h[1] - c[2], 0); dy = max(c[1] - h[2], h[2] - c[3], 0)
        d = math.hypot(dx, dy) - h[4] / 2
        if best is None or d < best[0]:
            best = (round(d, 2), r['ref'])
    print('  hole', h[0], 'nearest courtyard', best)

# connectors: list positions and courtyards
for r in rows:
    if r['ref'].startswith('J') or r['ref'] in ('USB1', 'U2', 'J101') or 'RJ45' in r['fp'] or 'USB' in r['fp'] or 'JST' in r['fp'] or 'WJ500' in r['fp']:
        print('conn', r['ref'], r['fp'].split(':')[1][:36], 'pos', round(r['x'], 2), round(r['y'], 2), 'rot', r['rot'], 'crt', [round(v, 2) for v in r['crt']] if r['crt'] else None)

# host region check: TLP / ESD / JST per host inside design regions, barrier
design = json.load(open(ROOT + '/hardware/design.json'))
regions = design['layout_study']['regions']
def domain_of(ref):
    c = comp_by_ref.get(ref)
    return c['sheet'] if c else None
viol = []
for r in rows:
    d = domain_of(r['ref'])
    if d and d.startswith('host') and r['crt']:
        reg = regions[d]
        hx, hy, hw, hh = reg['host']
        cx, cy, cw, ch = reg['controller']
        c = r['crt']
        in_host = c[0] >= hx - 0.01 and c[2] <= hx + hw + 0.01 and c[1] >= hy - 0.01 and c[3] <= hy + hh + 0.01
        in_ctrl = c[0] >= cx - 0.01 and c[2] <= cx + cw + 0.01 and c[1] >= cy - 0.01 and c[3] <= cy + ch + 0.01
        if not (in_host or in_ctrl):
            viol.append((r['ref'], d, [round(v, 2) for v in c]))
print('host-sheet parts outside their declared region:', len(viol), viol[:10])

# TLP3122A footprint pad geometry
for fp in fps:
    if 'TLP3122A' in str(fp.GetFPID().GetUniStringLibItemName()):
        pads = [(pd.GetNumber(), round(mm(pd.GetPosition().x - fp.GetPosition().x), 3), round(mm(pd.GetPosition().y - fp.GetPosition().y), 3), round(mm(pd.GetSize().x), 2), round(mm(pd.GetSize().y), 2)) for pd in fp.Pads()]
        print('TLP3122A pads (rel, rot %.0f):' % fp.GetOrientationDegrees(), pads, 'crt', [round(v, 2) for v in crt(fp)])
        break
# JST courtyard size
for fp in fps:
    if 'PHD' in str(fp.GetFPID().GetUniStringLibItemName()):
        c = crt(fp); print('JST courtyard size', round(c[2] - c[0], 2), 'x', round(c[3] - c[1], 2), 'ref', fp.GetReference())
        break
summary = dict(revision='R.2', board_mm=[round(bx1 - bx0, 2), round(by1 - by0, 2)], footprints=len(fps), side=dict(side), mount=dict(tht),
               footprint_assignment_mismatches=len(mismatch), courtyard_overlaps=len(overlaps), courtyard_gap_under_0p25mm_pairs=len(tight),
               smallest_courtyard_gap_mm=round(gaps[0], 3) if gaps else None, closest_courtyard_to_edge=edge[:6],
               mounting_holes=[h[0] for h in holes if h[0].startswith('MH')],
               jst_courtyard_mm=[round(c[2] - c[0], 2), round(c[3] - c[1], 2)], jst_pitch_mm=18.0,
               note='Courtyard-based geometry audit only; DRC/ERC/parity run separately with kicad-cli. Not a manufacturing release.')
json.dump(summary, open(ROOT + '/hardware/validation/r2-placement-audit.json', 'w'), indent=1)
print('wrote hardware/validation/r2-placement-audit.json')
