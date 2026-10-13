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
print('PASS: manifest, 10 connector pins, two hosts, revision, generated viewer and public page agree.')
