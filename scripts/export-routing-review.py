#!/usr/bin/env python3
"""Verify and publish R.0 copper geometry from the saved KiCad board."""
import json,hashlib,html,collections
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
source=p.LoadBoard(str(R/'hardware/cad/layout-S2-review.kicad_pcb'))
path=R/'hardware/cad/routing-R0.kicad_pcb';b=p.LoadBoard(str(path))
def signature(board):
 return sorted((f.GetReference(),f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),tuple(sorted((d.GetNumber(),d.GetNetname(),d.GetPosition().x,d.GetPosition().y) for d in f.Pads()))) for f in board.GetFootprints())
assert signature(source)==signature(b),'Routing must not silently move footprints or change pad nets'
r=json.loads((R/'hardware/routing-R0.json').read_text());assert r['pcb_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
drc=json.loads((R/'artifacts/local/r0-drc.json').read_text());assert drc['violations']==[],drc['violations']
segments=[]
for t in b.GetTracks():
 assert not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu
 a,z=t.GetStart(),t.GetEnd();segments.append(dict(a=[p.ToMM(a.x),p.ToMM(a.y)],b=[p.ToMM(z.x),p.ToMM(z.y)],net=t.GetNetname(),width_mm=p.ToMM(t.GetWidth())))
key=lambda a,z,n,w:(tuple(round(v,4) for v in a),tuple(round(v,4) for v in z),n,round(w,6))
expected=collections.Counter(key(a,z,route['net'],route['width_mm']) for route in r['routes'] for a,z in zip(route['points'],route['points'][1:]))
assert expected==collections.Counter(key(t['a'],t['b'],t['net'],t['width_mm']) for t in segments)
r['segments']=segments;r['drc']={'violations':0,'unconnected_items_reported':len(drc['unconnected_items']),'full_schematic_parity':False,'note':'Unconnected report count is not a percentage of routing completion.'};r['placement_unchanged']=True
r['total_track_length_mm']=round(sum(t.GetLength()/1e6 for t in b.GetTracks()),3)
(R/'hardware/routing-R0.json').write_text(json.dumps(r,indent=2)+'\n')
svg=(R/'hardware/layout-S2-review.svg').read_text();tracks='<g id="routed-copper" fill="none" stroke="#ff8e8e" stroke-linecap="round">'
for t in segments:
 a,z=t['a'],t['b'];tracks+=f'<path d="M{a[0]},{a[1]} L{z[0]},{z[1]}" stroke-width="{t["width_mm"]}"><title>{html.escape(t["net"])} / F.Cu</title></path>'
tracks+='</g>'
svg=svg.replace('</svg>',tracks+'</svg>').replace('S.2 / 200 x 170 mm / PLACEMENT REVIEW - NO ROUTES','R.0 / 200 x 170 mm / LOCAL ROUTING ONLY - INCOMPLETE')
(R/'hardware/routing-R0.svg').write_text(svg)
print('Verified:',len(segments),'actual F.Cu tracks;',r['total_track_length_mm'],'mm; unchanged placements/nets; DRC 0; incomplete connectivity')
