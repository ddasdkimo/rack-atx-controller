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
assert pins[-1]['signal'] == 'NC'
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
assert len(fragment.encode()) < 1_000_000
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

layout=json.loads((root / "hardware/placement-study.json").read_text())
assert d["layout_study"]==layout
assert layout["outline_mm"]==d["controller_outline_mm"]
assert len(layout["components"])==694 and layout["unqualified_envelope_count"]==0
assert {x["ref"] for x in layout["components"]}=={x["ref"] for x in c["components"] if x["sheet"]!="adapter" and x["key"]!="flag"}
assert len(d["bom_review"])==cost["unique_part_numbers"]
assert round(sum(x["batch_total_usd"] for x in d["bom_review"]),2)==cost["batches"][1]["parts_total_usd"]
assert (root / "docs/bom.html").read_text()==(root / "dist/bom.html").read_text()
print("PASS: S.2 placement, BOM totals and public BOM page agree.")
prototype=json.loads((root/'hardware/prototype-plan.json').read_text())
assert d['next_prototype']==prototype
assert prototype['manufacturing_ready'] is False and prototype['photorelays_per_panel']==4
assert prototype['different_designs']==2 and prototype['subboards_per_panel']==3
assert (root/'docs/prototype.html').read_text()==(root/'dist/prototype.html').read_text()
print('PASS: P.0 planning manifest and public illustration agree; manufacturing remains unapproved.')

audit=json.loads((root/"hardware/layout-review-checks.json").read_text())
assert all(x.get("pass",x.get("passed",False)) for x in audit["critical_proximity_checks"])
assert audit["tracks"]==0 and audit["inter_domain_violations"]==0
assert (root/"docs/layout.html").read_text()==(root/"dist/layout.html").read_text()

# Copper geometry provenance: the public/3D model must match the audited native R.0 export.
route=json.loads((root/'hardware/routing-R0.json').read_text())
assert route['track_segments']==len(route['segments'])>0 and route['drc']['violations']==0
assert d['routing_study']['segments']==route['segments']
assert (root/'docs/routing-R0.svg').read_text()==(root/'hardware/routing-R0.svg').read_text()
assert route['manufacturing_ready'] is False and route['status']=='partial_local_routing'
print('PASS: R.0 partial copper geometry, public view and 3D agree; manufacturing remains unapproved.')
