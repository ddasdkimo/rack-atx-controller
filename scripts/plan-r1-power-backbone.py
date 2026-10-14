#!/usr/bin/env python3
"""Lay out a deliberate 1.2 mm supply trunk, rip up conflicting trial signals.
Keeps pads and critical clock/buck copper. Native DRC remains mandatory.
"""
import wx,sys,shutil,math
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/(sys.argv[1] if len(sys.argv)>1 else 'artifacts/local/R1-power-wide.kicad_pcb');b=p.LoadBoard(str(src));removed=[];fps={f.GetReference():f for f in b.GetFootprints()}
text=(R/'scripts/start-local-routing.py').read_text();exec(text[text.index('def xy('):text.index('keepouts=[]')])
net='3V3';front=[(185.5,84),(181.5,84.05),(177,84.05),(175.5,82.55),(175.5,67.5),(174,66),(54,66)];back=[(54,66),(54,103),(52,105),(26.65,105),(26.65,98.5)];branch=[(26.65,98.5),(28,99.05)]
new=[(a,z,l,w) for pts,l,w in [(front,p.F_Cu,1.2),(back,p.B_Cu,1.2),(branch,p.F_Cu,.4)] for a,z in zip(pts,pts[1:])];newvias=[(54,66),(26.65,98.5),(34.3,91.4),(32.3,102.5)]
for pts,l,w in [([(44,105),(44,93),(42.4,91.4),(34.3,91.4)],p.B_Cu,.8), ([(34.3,91.4),(35.5,91.275)],p.F_Cu,.4), ([(32.3,105),(32.3,102.5)],p.B_Cu,.8), ([(32.3,102.5),(33.5,102.225)],p.F_Cu,.4), ([(33.4,100.45),(33.4,100.87),(33.6,101.07),(33.6,101.9),(33.5,102.225)],p.F_Cu,.125)]:
 new.extend((a,z,l,w) for a,z in zip(pts,pts[1:]))
def rectdist(a,z,bb):
 if hits(a,z,bb,0):return 0
 x0,y0,x1,y1=bb
 return min([point_seg(q,a,z) for q in [(x0,y0),(x0,y1),(x1,y0),(x1,y1)]]+[math.hypot(max(x0-q[0],0,q[0]-x1),max(y0-q[1],0,q[1]-y1)) for q in [a,z]])
errors=[]
for f in b.GetFootprints():
 for d in f.Pads():
  if d.GetNetname()==net:continue
  for a,z,l,w in new:
   if d.IsOnLayer(l) and rectdist(a,z,box(d))<w/2+.151:errors.append((f.GetReference()+'.'+d.GetNumber(),'track',a,z))
  for q in newvias:
   if rectdist(q,q,box(d))<.4+.151:errors.append((f.GetReference()+'.'+d.GetNumber(),'via',q))
if errors:raise RuntimeError(errors)
critical=set('BUCK_SW BUCK_BST MCU_XN MCU_XP MCU_XP_CR ETH_XI ETH_XO'.split())
for t in list(b.GetTracks()):
 if t.GetNetname()==net:continue
 if isinstance(t,p.PCB_VIA):
  q=xy(t);rad=p.ToMM(t.GetWidth(p.F_Cu))/2
  conflict=any(point_seg(q,a,z)<rad+w/2+.155 for a,z,l,w in new) or any(math.dist(q,v)<rad+.4+.155 for v in newvias)
  if t.GetNetname()=='GND_CTRL' and 32.9<=q[0]<=35.1 and 95.9<=q[1]<=98.1:assert not conflict,'EPAD via conflict'
 else:
  a=xy(t);z=(t.GetEnd().x/1e6,t.GetEnd().y/1e6);rad=p.ToMM(t.GetWidth())/2
  conflict=any(t.GetLayer()==l and segdist(a,z,u,v)<rad+w/2+.155 for u,v,l,w in new) or any(point_seg(v,a,z)<rad+.4+.155 for v in newvias)
 if conflict:
  assert t.GetNetname() not in critical,('critical conflict',t.GetNetname())
  b.Remove(t);removed.append(t)
def vec(a):return p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]))
for a,z,l,w in new:
 t=p.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(z));t.SetLayer(l);t.SetWidth(p.FromMM(w));t.SetNetCode(b.FindNet(net).GetNetCode());b.Add(t)
for q in newvias:
 v=p.PCB_VIA(b);v.SetPosition(vec(q));v.SetWidth(p.FromMM(.8));v.SetDrill(p.FromMM(.4));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(b.FindNet(net).GetNetCode());b.Add(v)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());out=R/'artifacts/local/R1-power-backbone.kicad_pcb';p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(src.with_suffix(ext),out.with_suffix(ext))
p.ExportSpecctraDSN(b,str(R/'artifacts/local/R1-power-backbone.dsn'));print('Added 1.2 mm trunk; reroute',len(removed),'conflicting copper objects; native',b.GetConnectivity().GetUnconnectedCount(False))
