#!/usr/bin/env python3
"""Audit the unrouted S.2 placement; this is not a manufacturing release check."""
import json,math,html
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
B=p.LoadBoard(str(R/'hardware/cad/layout-S2-review.kicad_pcb'))
C=json.loads((R/'hardware/circuit.json').read_text());L=json.loads((R/'hardware/placement-study.json').read_text())
parts={c['ref']:c for c in C['components'] if c['sheet']!='adapter' and c['key']!='flag'}
assert len(parts)==694
fps={f.GetReference():f for f in B.GetFootprints()}
assert len(fps)==698 and len(B.GetTracks())==0
pads=[];missing=[];proximity=[]
def xy(d):
 q=d.GetPosition();return p.ToMM(q.x),p.ToMM(q.y)
def domain(n):
 if n.startswith('H') and n[1:3].isdigit() and n[3:4]=='_' and not n.endswith(('PLED_N','HDD_N')):return n[:3]
 return 'CTRL'
for ref,c in parts.items():
 f=fps[ref];assert len(list(f.Pads()))>0,ref
 for pin,net in c['nets'].items():
  if not net:continue
  candidates=[d for d in f.Pads() if d.GetNumber()==pin];assert candidates,(ref,pin)
  assert all(d.GetNetname()==net for d in candidates),(ref,pin,net)
 for d in f.Pads():
  if not d.GetNetname():continue
  q=d.GetBoundingBox();box=[p.ToMM(v) for v in (q.GetX(),q.GetY(),q.GetWidth(),q.GetHeight())]
  pads.append((ref,d.GetNumber(),domain(d.GetNetname()),box))
minimum=(1e9,None);bad=[]
for i,a in enumerate(pads):
 for b in pads[i+1:]:
  if a[2]==b[2]:continue
  x,y,w,h=a[3];xx,yy,ww,hh=b[3]
  gap=math.hypot(max(0,x-xx-ww,xx-x-w),max(0,y-yy-hh,yy-y-h))
  if gap<minimum[0]:minimum=(gap,[a[:3],b[:3]])
  if gap<1-1e-5:bad.append([round(gap,4),a[:3],b[:3]])
print('Inter-domain minimum pad bounding-box gap:',minimum,'violations:',bad[:10])
assert not bad,'Domain separation failed'
# Supplementary placement relationships (pin distance; actual routed loops remain unverified).
def pair(a,ap,b,bp,limit,label):
 da=next(d for d in fps[a].Pads() if d.GetNumber()==str(ap));db=next(d for d in fps[b].Pads() if d.GetNumber()==str(bp));d=math.dist(xy(da),xy(db));proximity.append(dict(label=label,a=a,b=b,distance_mm=round(d,3),limit_mm=limit,passed=d<=limit));assert d<=limit,(label,d,limit)
for n in range(10):
 host=[c for c in parts.values() if c['sheet'].startswith(f'host{n+1:02}')]
 cmp=next(c for c in host if c['key']=='cmp');cap=next(c for c in host if c['key']=='C100n');pair(cap['ref'],1,cmp['ref'],8,3,'Comparator decoupling')
for cap in ['C43','C44','C45']:pair(cap,1,'U7',6,8,'Timer RC cluster')
for cap,pin in [('C14',2),('C15',3)]:pair(cap,1,'U2',pin,10,'MCU bulk capacitor')
assert all(c['pass'] for c in L['placement_constraints'])
report={'revision':'S.2','electrical_components':694,'mounting_holes':4,'pad_free_placeholders':0,'net_pin_mapping':'all connected schematic pins present with matching PCB nets','tracks':0,'inter_domain_pad_bbox_minimum_mm':round(minimum[0],4),'inter_domain_violations':0,'critical_proximity_checks':L['placement_constraints']+proximity,'manufacturing_ready':False,'user_approval':'pending','limits':['Straight-line pad proximity is not routed inductance/return-path verification.','1 mm is a low-voltage functional separation design rule, not a mains/safety-isolation rating.','Copper pours, thermal vias, signal integrity, assembly DFM and physical prototype tests remain pending.']}
(R/'hardware/layout-review-checks.json').write_text(json.dumps(report,indent=2)+'\n')
# Exact board-coordinate review drawing; pad centres/extents from the actual KiCad file.
colors={'CTRL':'#73bba1',**{f'H{n:02}':('#eeb868' if n%2 else '#8fbce5') for n in range(1,11)}}
out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -8 204 186"><style>text{font-family:monospace} .ref{font-size:1.25px;fill:#e7f5ee} .group{font-size:2.7px;fill:#dceee6}</style><rect width="200" height="170" rx="1" fill="#153c32" stroke="#5b9b7e" stroke-width=".3"/>']
for i in range(10):
 x=5+(i%5)*38;y=0 if i<5 else 122.5
 out.append(f'<rect x="{x}" y="{y}" width="38" height="47.5" fill="{colors[f"H{i+1:02}"]}" opacity=".08"/><text class="group" x="{x+1}" y="{7 if i<5 else 164}">H{i+1:02}</text>')
for y in [47.5,121.5]:out.append(f'<rect x="5" y="{y}" width="190" height="1" fill="#fa7575" opacity=".65"/>')
for ref,f in fps.items():
 if ref.startswith('MH'):
  x,y=xy(f);out.append(f'<circle cx="{x}" cy="{y}" r="1.6" fill="#ecf3ee"/><circle cx="{x}" cy="{y}" r="3.2" fill="none" stroke="#9ab3a8" stroke-width=".2"/>');continue
 rec=next(c for c in L['components'] if c['ref']==ref);x,y,w,h=[rec[k] for k in ('x','y','w','h')]
 out.append(f'<g><title>{html.escape(ref+" "+f.GetValue()+" | "+rec["footprint"])}</title><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#10251f" stroke="#749589" stroke-width=".12"/>')
 for d in f.Pads():
  bb=d.GetBoundingBox();a,b,ww,hh=[p.ToMM(v) for v in (bb.GetX(),bb.GetY(),bb.GetWidth(),bb.GetHeight())];col=colors[domain(d.GetNetname())]
  out.append(f'<rect x="{a}" y="{b}" width="{ww}" height="{hh}" fill="{col}"><title>{html.escape(ref+"."+d.GetNumber()+" "+d.GetNetname())}</title></rect>')
 if ref[0] in 'UJYLF':out.append(f'<text class="ref" x="{x+w/2}" y="{y+h/2+.5}" text-anchor="middle">{ref}</text>')
 out.append('</g>')
for x,y,label in [(22,64,'LAN / W5500'),(23,110,'USB / ESP32'),(77,95,'OUTPUT LATCHES'),(157,110,'PULSE TIMER'),(171,64,'5V / 3V3 POWER')]:out.append(f'<text class="group" x="{x}" y="{y}">{label}</text>')
out.append('<text class="group" x="0" y="-3">S.2 / 200 x 170 mm / PLACEMENT REVIEW - NO ROUTES</text></svg>')
(R/'hardware/layout-S2-review.svg').write_text(''.join(out))
print('PASS: pin/net mapping, nonempty footprints, functional domain pad gaps and critical pad distances; no routing.')
