#!/usr/bin/env python3
"""Build the inline viewer and portable public page from the hardware manifest."""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--inline-output', type=Path)
args = parser.parse_args()
design = json.loads((ROOT / 'hardware/design.json').read_text())
template = (ROOT / 'visualization/viewer.template.html').read_text()
assert template.count('__DESIGN_JSON__') == 1
fragment = template.replace('__DESIGN_JSON__', json.dumps(design, ensure_ascii=False, separators=(",",":")).replace('<', '\\u003c'))
out = ROOT / 'visualization/rack-atx-3d.html'
out.write_text(fragment)
shell = (ROOT / 'visualization/standalone-shell.template.html').read_text()
marker = html.escape('<div id="rack-fragment-insertion"></div>', quote=True)
assert shell.count(marker) == 1
page = shell.replace(marker, html.escape(fragment, quote=True))
for directory in ('docs', 'dist'):
    target = ROOT / directory
    target.mkdir(exist_ok=True)
    (target / 'index.html').write_text(page)
if args.inline_output:
    args.inline_output.parent.mkdir(parents=True, exist_ok=True)
    args.inline_output.write_text(fragment)
print(f'Built revision {design["revision"]}: inline viewer + docs/index.html + dist/index.html')

bom_data={'total':next(b for b in design['costs']['batches'] if b['boards']==5)['parts_total_usd'],'rows':design['bom_review'],'costs':design['costs'],'revision':design['revision']}
bom_page=(ROOT/'visualization/bom.template.html').read_text().replace('__BOM_JSON__',json.dumps(bom_data,ensure_ascii=False).replace('<','\\u003c'))
for directory in ('docs','dist'):
 (ROOT/directory/'bom.html').write_text(bom_page)

prototype=json.loads((ROOT/'hardware/prototype-plan.json').read_text())
assert prototype==design['next_prototype']
prototype_cost=json.loads((ROOT/'hardware/prototype-cost.json').read_text())
prototype_page=(ROOT/'visualization/prototype.template.html').read_text().replace('__PROTO_JSON__',json.dumps(prototype,ensure_ascii=False).replace('<','\\u003c')).replace('__P0_COST_JSON__',json.dumps(prototype_cost,ensure_ascii=False).replace('<','\\u003c'))
for directory in ('docs','dist'):
 (ROOT/directory/'prototype.html').write_text(prototype_page)

layout_svg=(ROOT/'hardware/routing-R3.svg').read_text()
audit=json.loads((ROOT/'hardware/layout-S3-checks.json').read_text())
audit['routing']=json.loads((ROOT/'hardware/validation/routing-R3-checks.json').read_text())
layout_page=(ROOT/'visualization/layout.template.html').read_text().replace('__LAYOUT_SVG__',layout_svg).replace('__AUDIT_JSON__',json.dumps(audit,ensure_ascii=False).replace('<','\\u003c'))
for directory in ('docs','dist'):
 (ROOT/directory/'layout.html').write_text(layout_page)
 (ROOT/directory/'routing-R3.svg').write_text(layout_svg)
 (ROOT/directory/'layout-S3-review.svg').write_text((ROOT/'hardware/layout-S3-review.svg').read_text())
 (ROOT/directory/'adapter-B2.svg').write_text((ROOT/'hardware/adapter-B2.svg').read_text())

for directory in ('docs','dist'):
 (ROOT/directory/'indicator-layout-R2.svg').write_text((ROOT/'hardware/indicator-layout-R2.svg').read_text())
