#!/usr/bin/env python3
"""Check native header lands and outward mating access against the JST PHD drawing."""
import wx,json,math,hashlib,argparse
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--board',type=Path,default=R/'hardware/cad/B2/rack-atx-controller.kicad_pcb')
ap.add_argument('--output',type=Path,default=R/'hardware/validation/jst-phd-audit.json')
a=ap.parse_args();b=p.LoadBoard(str(a.board));rows=[]
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref not in {f'J{i:02}' for i in range(1,11)}:continue
 ds={d.GetNumber():d for d in f.Pads()};assert len(ds)==10
 cx,cy=p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y);rad=math.radians(f.GetOrientationDegrees())
 for i in range(1,11):
  d=ds[str(i)];dx=p.ToMM(d.GetPosition().x)-cx;dy=p.ToMM(d.GetPosition().y)-cy
  q=(dx*math.cos(rad)-dy*math.sin(rad),dx*math.sin(rad)+dy*math.cos(rad))
  assert math.dist(q,(((i-1)//2)*2,((i-1)%2)*2))<1e-5
  assert abs(p.ToMM(d.GetDrillSize().x)-.75)<1e-6
  expected={1:'PWR_A',2:'PWR_B',3:'RST_A',4:'RST_B',9:'GND'}
  assert d.GetNetname()==('H'+ref[1:]+'_'+expected[i] if i in expected else '')
 fab=[g for g in f.GraphicalItems() if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.F_Fab]
 points=[(p.ToMM(q.x),p.ToMM(q.y)) for g in fab for q in (g.GetStart(),g.GetEnd())]
 x0,x1=min(q[0] for q in points),max(q[0] for q in points);y0,y1=min(q[1] for q in points),max(q[1] for q in points)
 assert abs(x1-x0-11.9)<1e-5 and abs(y1-y0-9.5)<1e-5
 top=int(ref[1:])<=5;assert f.GetOrientationDegrees()==(180 if top else 0)
 rows.append(dict(ref=ref,body_bbox_mm=[x0,y0,x1,y1],hole_mm=.75,mating_direction='toward y=0 edge' if top else 'toward y=110 edge',front_face_inset_mm=round(y0 if top else 110-y1,3)))
assert len(rows)==10
for row in rows:
 for other in b.GetFootprints():
  if other.GetReference()==row['ref']:continue
  bb=other.GetBoundingBox(False,False);x0,y0,x1,y1=row['body_bbox_mm'];oy0=p.ToMM(bb.GetTop());oy1=p.ToMM(bb.GetBottom());ox0=p.ToMM(bb.GetLeft());ox1=p.ToMM(bb.GetRight())
  in_front=oy1<y0 if row['mating_direction'].startswith('toward y=0') else oy0>y1
  assert not (in_front and ox0<x1 and ox1>x0), (row['ref'],other.GetReference(),'mating path blocked on board')
centres=sorted((r['body_bbox_mm'][0]+r['body_bbox_mm'][2])/2 for r in rows if r['ref']<'J06')
report=dict(checked_at='2026-10-15',status='pass nominal native land geometry and outward PCB access',board_sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),source='https://www.jst-mfg.com/product/pdf/eng/ePHD.pdf',source_pages=[1,3],part='S10B-PHDSS(LF)(SN)',mounting_surface_view=True,pitch_mm=2,span_A_mm=8,body_width_B_mm=11.9,manufacturer_hole_reference_mm=[.7,.8],native_hole_mm=.75,header_spacing_mm=min(z-u for u,z in zip(centres,centres[1:])),body_side_gap_mm=min(z-u for u,z in zip(centres,centres[1:]))-11.9,headers=sorted(rows,key=lambda r:r['ref']),limitations=['Source drawings were visually inspected; nominal geometry is not PCB hole-tolerance qualification.','No enclosure or cable bend-radius model exists. Outward PCB access does not certify enclosure opening, wire strain relief or finger clearance.','Confirm mating PHDR-10VS housing and selected wire/contact combination on prototype.'])
a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(rows),'headers; body side gap',report['body_side_gap_mm'])
