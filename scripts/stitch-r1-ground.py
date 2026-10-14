#!/usr/bin/env python3
"""Add a via only when native connectivity improves, with conservative clearance.
Works on a local trial. Native fill/DRC remain mandatory after this pass.
"""
import sys,math,shutil
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
src=R/(sys.argv[1] if len(sys.argv)>1 else 'artifacts/local/R1-ground-bridged.kicad_pcb')
b=p.LoadBoard(str(src));removed=[];fps={f.GetReference():f for f in b.GetFootprints()}
text=(R/'scripts/start-local-routing.py').read_text();exec(text[text.index('def xy('):text.index('keepouts=[]')])
pads=[d for f in b.GetFootprints() for d in f.Pads()]
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)]
holes=[(xy(d),p.ToMM(max(d.GetDrillSize().x,d.GetDrillSize().y)),.451) for d in pads if d.GetDrillSize().x]+[(xy(t),p.ToMM(t.GetDrill()),.251) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
existing_vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
keepouts=[box(z) for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
planes={}
for z in b.Zones():
 if not z.GetIsRuleArea():planes.setdefault(z.GetNetname(),{})[z.GetLayer()]=z
b.BuildConnectivity();count=b.GetConnectivity().GetUnconnectedCount(False);before=count;added=[]
for n,zs in planes.items():
 if len(sys.argv)>2 and n not in sys.argv[2:]:continue
 if p.F_Cu not in zs or p.B_Cu not in zs:continue
 gp=[d for d in pads if d.GetNetname()==n];candidates=set()
 for d in gp:
  x,y=xy(d)
  for rad in [.8,1,1.5,2,3,4,6,8]:
   for deg in range(0,360,30):
    a=math.radians(deg);candidates.add((round(x+rad*math.cos(a),3),round(y+rad*math.sin(a),3)))
 for q in sorted(candidates):
  pt=p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
  if not all(zs[l].HitTestFilledArea(l,pt) for l in [p.F_Cu,p.B_Cu]):continue
  if any(hits(q,q,k,.31) for k in keepouts):continue
  if any(math.dist(q,h)<.15+dia/2+gap for h,dia,gap in holes):continue
  if any(v.GetNetname()!=n and math.dist(q,xy(v))<.25+p.ToMM(v.GetWidth(p.F_Cu))/2+(1.01 if domain(v.GetNetname())!=domain(n) else .155) for v in existing_vias):continue
  if any(d.GetNetname()!=n and hits(q,q,box(d),.25+(1.01 if d.GetNetname() and domain(d.GetNetname())!=domain(n) else .155)) for d in pads):continue
  if any(t.GetNetname()!=n and point_seg(q,xy(t),(p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)))<.25+p.ToMM(t.GetWidth())/2+(1.01 if domain(t.GetNetname())!=domain(n) else .155) for t in tracks):continue
  v=p.PCB_VIA(b);v.SetPosition(pt);v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(b.FindNet(n).GetNetCode());b.Add(v);b.BuildConnectivity();now=b.GetConnectivity().GetUnconnectedCount(False)
  if now<count:added.append((n,q,count-now));holes.append((q,.3,.251));existing_vias.append(v);count=now
  else:b.Remove(v);removed.append(v)
 print(n,'remaining',count,flush=True)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();out=R/'artifacts/local/R1-stitched.kicad_pcb';p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(src.with_suffix(ext),out.with_suffix(ext))
print('Stitches',added,'unrouted',before,'->',b.GetConnectivity().GetUnconnectedCount(False))
