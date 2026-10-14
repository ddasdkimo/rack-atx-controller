#!/usr/bin/env python3
"""Export the routed passive adapter for the two-host viewer and native 2D review."""
import wx,json,html,hashlib
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/'hardware/cad/B2/adapter.kicad_pcb';b=p.LoadBoard(str(src))
def xy(v):return [round(p.ToMM(v.x),4),round(p.ToMM(v.y),4)]
components=[];segments=[]
for f in b.GetFootprints():
 bb=f.GetBoundingBox(False,False)
 components.append(dict(ref=f.GetReference(),at=xy(f.GetPosition()),rotation=f.GetOrientationDegrees(),bbox_mm=[p.ToMM(v) for v in (bb.GetX(),bb.GetY(),bb.GetWidth(),bb.GetHeight())],pads=[dict(pin=d.GetNumber(),at=xy(d.GetPosition()),size_mm=xy(d.GetSize()),net=d.GetNetname()) for d in f.Pads()]))
for t in b.GetTracks():
 assert not isinstance(t,p.PCB_VIA)
 segments.append(dict(a=xy(t.GetStart()),b=xy(t.GetEnd()),layer=b.GetLayerName(t.GetLayer()),width_mm=p.ToMM(t.GetWidth()),net=t.GetNetname()))
a=dict(outline_mm=[26,34,1.6],components=components,segments=segments,pcb_sha256=hashlib.sha256(src.read_bytes()).hexdigest())
d=json.loads((R/'hardware/design.json').read_text());d['adapter_geometry']=a
(R/'hardware/design.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -4 28 40"><rect x="-1" y="-4" width="28" height="40" fill="#10241e"/><rect width="26" height="34" fill="#153c32" stroke="#5b9b7e" stroke-width=".2"/><text x="0" y="-1.5" fill="#eee" font-family="monospace" font-size="1.2">B.2 adapter / 26 x 34 mm</text>']
for s in segments:
 a,z=s['a'],s['b'];col='#ff9999' if s['layer']=='F.Cu' else '#75adff'
 svg.append(f'<path d="M{a[0]},{a[1]} L{z[0]},{z[1]}" fill="none" stroke="{col}" stroke-width="{s["width_mm"]}"><title>{html.escape(s["net"])} / {s["layer"]}</title></path>')
for c in components:
 x,y,w,h=c['bbox_mm'];svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#9bb7aa" stroke-width=".1"/><text x="{x}" y="{y-.4}" fill="#eee" font-family="monospace" font-size=".9">{c["ref"]}</text>')
 for pad in c['pads']:
  x,y=pad['at'];svg.append(f'<circle cx="{x}" cy="{y}" r=".8" fill="#ddbc75"/><circle cx="{x}" cy="{y}" r=".35" fill="#10241e"/><text x="{x+.8}" y="{y+.3}" fill="#fff" font-family="monospace" font-size=".8">{pad["pin"]}</text>')
svg.append('</svg>');(R/'hardware/adapter-B2.svg').write_text(''.join(svg))
print('Adapter 3D geometry and SVG exported:',len(components),'components,',len(segments),'segments.')
