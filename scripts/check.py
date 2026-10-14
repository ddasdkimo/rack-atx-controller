#!/usr/bin/env python3
"""Check cross-document connector and revision integrity, not electrical validity."""
import html
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
d = json.loads((root / 'hardware/design.json').read_text())
pins = d['connector']['pins']
assert [p['pin'] for p in pins] == list(range(1, 11))
assert len({p['signal'] for p in pins}) == 10
assert pins[-1]['signal'] == 'NC10'
assert pins[-2]['signal'] == 'HOST_REF'
assert d['host_count'] == 10
assert d['constraints']['manufacturing_ready'] is False
assert d['constraints']['original_paths_need_controller_power'] is False
assert len(d['hosts']) == 2 and [h['port'] for h in d['hosts']] == [1, 2]
for f in d['functions']:
    assert f['pair'] == [p['pin'] for p in pins if p['group'] == f['id']]
fragment = (root / 'visualization/rack-atx-3d.html').read_text()
embedded = re.search(r'<script type="application/json" data-design>(.*?)</script>', fragment, re.S)
assert embedded and json.loads(embedded.group(1)) == d
assert len(fragment.encode()) < 2_000_000
assert '__DESIGN_JSON__' not in fragment
page = (root / 'docs/index.html').read_text()
assert html.escape(fragment, quote=True) in page
assert page == (root / 'dist/index.html').read_text()
for path in (root / 'README.md', root / 'CHANGELOG.md'):
    assert d['revision'] in path.read_text(), str(path)
c=json.loads((root / 'hardware/circuit.json').read_text())
cost=json.loads((root / 'hardware/bom/cost-model.json').read_text())
assert d['costs']==cost and c['revision']==d['revision']==cost['revision']
for item in d['electronics']:
    keys=[k for k,p in c['parts'].items() if p['code']==item['code']]
    assert len(keys)==1 and item['qty']==sum(x['key']==keys[0] and x['sheet']!='adapter' for x in c['components'])
print('PASS: manifest, 10 connector pins, two hosts, revision, generated viewer and public page agree.')

layout=json.loads((root / "hardware/placement-S3.json").read_text())
assert d["layout_study"]==layout
assert layout["outline_mm"]==d["controller_outline_mm"]
assert len(layout["components"])==300 and layout["unqualified_envelope_count"]==0
assert {x["ref"] for x in layout["components"]}=={x["ref"] for x in c["components"] if x["sheet"]!="adapter" and x["key"]!="flag"}
assert len(d["bom_review"])==cost["unique_part_numbers"]
assert round(sum(x["batch_total_usd"] for x in d["bom_review"]),2)==cost["batches"][1]["parts_total_usd"]
assert (root / "docs/bom.html").read_text()==(root / "dist/bom.html").read_text()
print("PASS: S.3 placement, BOM totals and public BOM page agree.")
prototype=json.loads((root/'hardware/prototype-plan.json').read_text())
assert d['next_prototype']==prototype
assert prototype['manufacturing_ready'] is False and prototype['photorelays_per_panel']==4
assert prototype['different_designs']==2 and prototype['subboards_per_panel']==3
assert (root/'docs/prototype.html').read_text()==(root/'dist/prototype.html').read_text()
print('PASS: P.0 planning manifest and public illustration agree; manufacturing remains unapproved.')

audit=json.loads((root/"hardware/layout-S3-checks.json").read_text())
assert all(x.get("pass",x.get("passed",False)) for x in audit["critical_proximity_checks"])
assert audit["tracks"]==0 and audit["inter_domain_violations"]==0
assert (root/"docs/layout.html").read_text()==(root/"dist/layout.html").read_text()

# Latest user instruction authorized finishing routing after placement checks.
assert d['revision']=='B.2' and layout['revision']=='S.3'
assert {f['id'] for f in d['functions']}=={'power','reset','reference'}
assert all(p['group']=='unused' for p in pins if p['pin'] in [5,6,7,8,10])
assert not any(x['key'] in ['iso','ldo','cmp','opto'] for x in c['components'])
assert d['constraints']['remote_led_sensing'] is False
assert d['constraints']['routing_requires_user_layout_approval'] is False
assert layout['user_approval']==audit['user_approval']=='routing_authorized'
route=d['routing_study']
assert route['track_segments']==len(route['segments'])
assert route['vias']==len(route['via_geometry'])
assert route['ground_zones']==11 and route['native_unrouted']==0
checks=json.loads((root/'hardware/validation/routing-R3-checks.json').read_text())
assert route['revision']=='R.3' and route['track_segments']==checks['controller']['track_segments'] and route['vias']==checks['controller']['vias']
assert all(checks[n]['native_unrouted']==checks[n]['drc_violations']==0 for n in ['controller','adapter'])
assert checks['controller']['pcb_sha256']==route['pcb_sha256']
assert d['adapter_geometry']['pcb_sha256']==checks['adapter']['pcb_sha256']
assert (root/'docs/layout-S3-review.svg').read_text()==(root/'hardware/layout-S3-review.svg').read_text()
import hashlib
sim=json.loads((root/'hardware/simulation/results/B2-summary.json').read_text())
assert sim['circuit_sha256']==hashlib.sha256((root/'hardware/circuit.json').read_bytes()).hexdigest()
assert sim['pass'] and len(sim['corners'])==16 and len(sim['cases'])==9
assert sim['oscillator_bound_is_model_assumption'] and not sim['hardware_correlated']
assert audit['pcb_sha256']==hashlib.sha256((root/'hardware/cad/B2/placement/rack-atx-controller.kicad_pcb').read_bytes()).hexdigest()
assert route['pcb_sha256']==hashlib.sha256((root/'hardware/cad/B2/rack-atx-controller.kicad_pcb').read_bytes()).hexdigest()
assert checks['adapter']['pcb_sha256']==hashlib.sha256((root/'hardware/cad/B2/adapter.kicad_pcb').read_bytes()).hexdigest()
assert cost['pcb_fabrication_estimate']['total_usd'] is None
assert all(b['assembled_total_range_usd'] is None for b in cost['batches'])
print('PASS: B.2 simulation hash, S.3 baseline + R.3 routed native hashes, no LED sensing, both boards DRC/unrouted zero; qualified PCB process price remains unselected; observed options are separate.')
