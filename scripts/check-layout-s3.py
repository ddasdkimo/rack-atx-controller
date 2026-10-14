#!/usr/bin/env python3
"""Audit the unrouted S.3 placement; this is not a manufacturing release check."""
import json,math,html,hashlib,uuid
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
B=p.LoadBoard(str(R/'hardware/cad/B2/placement/rack-atx-controller.kicad_pcb'))
C=json.loads((R/'hardware/cad/B2/placement/circuit-baseline.json').read_text());L=json.loads((R/'hardware/placement-S3.json').read_text())
parts={c['ref']:c for c in C['components'] if c['sheet']!='adapter' and c['key']!='flag'}
assert len(parts)==300
fps={f.GetReference():f for f in B.GetFootprints()}
assert len(fps)==304 and len(B.GetTracks())==0
pads=[];missing=[];proximity=[]
def xy(d):
 q=d.GetPosition();return p.ToMM(q.x),p.ToMM(q.y)
def domain(n):
 if n.startswith('H') and n[1:3].isdigit() and n[3:4]=='_' and not n.endswith(('PLED_N','HDD_N')):return n[:3]
 return 'CTRL'
for ref,c in parts.items():
 f=fps[ref];assert len(list(f.Pads()))>0,ref
 expected_path='/'+ '/'.join(str(uuid.uuid5(uuid.NAMESPACE_URL,'rack-atx/B2/'+key)) for key in ['root','sheet:'+c['sheet'],ref])
 assert f.GetPath().AsString()==expected_path,(ref,'schematic UUID link')
 assert str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())==C['parts'][c['key']]['footprint'],(ref,'historical baseline footprint assignment')
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
pair('C40',1,'U7',2,3,'C0G oscillator capacitor')
for cap,pin in [('C14',2),('C15',3)]:pair(cap,1,'U2',pin,10,'MCU bulk capacitor')
assert all(c['pass'] for c in L['placement_constraints'])
report={'revision':'S.3','electrical_components':300,'mounting_holes':4,'pad_free_placeholders':0,'net_pin_mapping':'all connected schematic pins present with matching PCB nets','tracks':0,'inter_domain_pad_bbox_minimum_mm':round(minimum[0],4),'inter_domain_violations':0,'critical_proximity_checks':L['placement_constraints']+proximity,'manufacturing_ready':False,'user_approval':'routing_authorized','limits':['Straight-line pad proximity is not routed inductance/return-path verification.','1 mm is a low-voltage functional separation design rule, not a mains/safety-isolation rating.','This immutable placement baseline is separate from the routed R.3 board. See routing-R3-checks.json for copper checks.']}
report['pcb_sha256']=hashlib.sha256((R/'hardware/cad/B2/placement/rack-atx-controller.kicad_pcb').read_bytes()).hexdigest()
previous=json.loads((R/'hardware/layout-S3-checks.json').read_text()) if (R/'hardware/layout-S3-checks.json').exists() else {}
if previous.get('pcb_sha256')==report['pcb_sha256'] and 'kicad_drc' in previous:report['kicad_drc']=previous['kicad_drc']
(R/'hardware/layout-S3-checks.json').write_text(json.dumps(report,indent=2)+'\n')
# Exact board-coordinate review drawing; pad centres/extents from the actual KiCad file.
colors={'CTRL':'#73bba1',**{f'H{n:02}':('#eeb868' if n%2 else '#8fbce5') for n in range(1,11)}}
W,H=L['outline_mm'][:2]
out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -7 {W+4} {H+14}"><style>text{{font-family:monospace}} .ref{{font-size:1.05px;fill:#e7f5ee}} .group{{font-size:1.8px;fill:#dceee6}}</style><rect x="-2" y="-7" width="{W+4}" height="{H+14}" fill="#10241e"/><rect width="{W}" height="{H}" rx="1" fill="#153c32" stroke="#5b9b7e" stroke-width=".3"/>']
for i in range(10):
 x=5+(i%5)*18;y=0 if i<5 else H-22
 out.append(f'<rect x="{x}" y="{y}" width="18" height="22" fill="{colors[f"H{i+1:02}"]}" opacity=".08"/><text class="group" x="{x+.5}" y="{15 if i<5 else H-14}">H{i+1:02}</text>')
for z in B.Zones():
 poly=z.Outline();pts=poly.Outline(0);points=' '.join(f'{p.ToMM(pts.CPoint(j).x)},{p.ToMM(pts.CPoint(j).y)}' for j in range(pts.PointCount()))
 out.append(f'<polygon points="{points}" fill="#fa7575" opacity=".5"/>')
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
out.append(f'<text class="group" x="0" y="-3">S.3 / {W} x {H} mm / PLACEMENT ONLY - NO ROUTES</text>')
out.append(f'<text class="group" x="0" y="{H+4}">300 components / 20 isolated POWER + RESET outputs</text></svg>')
(R/'hardware/layout-S3-review.svg').write_text(''.join(out))
print('PASS: matching pin/nets, >=1mm functional isolation, critical pad distances; ZERO routes.')
