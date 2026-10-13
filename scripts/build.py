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
fragment = template.replace('__DESIGN_JSON__', json.dumps(design, ensure_ascii=False, indent=2).replace('<', '\\u003c'))
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
