#!/usr/bin/env python3
"""Validate the selected native R.1 and publish a path-free, hash-bound report.
Run in KiCad Python. Does not claim full schematic parity or production release.
"""
import wx,json,hashlib,subprocess,collections
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];path=R/'hardware/cad/routing-R1.kicad_pcb';sha=hashlib.sha256(path.read_bytes()).hexdigest();out=R/'artifacts/local/r1-final-drc.json'
cli=Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
subprocess.run([str(cli),'pcb','drc','--format','json','--severity-all','-o',str(out),str(path)],check=True,capture_output=True)
assert hashlib.sha256(path.read_bytes()).hexdigest()==sha,'PCB changed during DRC'
j=json.loads(out.read_text());b=p.LoadBoard(str(path));b.BuildConnectivity();native=b.GetConnectivity().GetUnconnectedCount(False);fps={f.GetReference():f for f in b.GetFootprints()};circuit=json.loads((R/'hardware/circuit.json').read_text());pins=0
for c in circuit['components']:
 if c['sheet']=='adapter' or c['key']=='flag':continue
 f=fps[c['ref']]
 for num,net in c['nets'].items():
  actual=[d.GetNetname() for d in f.Pads() if d.GetNumber()==num]
  assert actual and all(n==(net or '') for n in actual),(c['ref'],num,net,actual)
  pins+=1
power=json.loads((R/'artifacts/local/r1-power-path-audit.json').read_text());assert power['pcb_sha256']==sha,'Rerun the power audit on the selected PCB'
mcu=[x for x in power['paths'] if x['target'].startswith('U2.')];assert len(mcu)==6 and all(x['drop_v'] is not None and x['drop_v']<.12 for x in mcu),'MCU supply-path budget failed'
summary=dict(revision='R.1',pcb_sha256=sha,kicad_version=j['kicad_version'],native_unrouted=native,drc_violations=len(j['violations']),drc_types=dict(collections.Counter(v['type'] for v in j['violations'])),ignored_checks=j['ignored_checks'],pins_checked=pins,electrical_components=694,full_schematic_parity=False,power=power,manufacturing_ready=False,limits=['Copper-only DC estimate; not an assembled-board measurement','High-speed signal integrity, assembly DFM and prototype qualification remain separate'])
assert native==0,('Unrouted connections remain',native)
assert not j['violations'],summary['drc_types']
(R/'hardware/validation/routing-R1-checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print('PASS: native connectivity, DRC, schematic pin nets and conservative MCU supply copper budget; NOT a manufacturing release.')
