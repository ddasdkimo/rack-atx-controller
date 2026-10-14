#!/usr/bin/env python3
"""Export exact copper and disconnected native pad clusters for local repair trials."""
import wx,json,sys
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(R/(sys.argv[1] if len(sys.argv)>1 else 'artifacts/local/R1-general.kicad_pcb')));b.BuildConnectivity();conn=b.GetConnectivity()
def xy(v):return [p.ToMM(v.x),p.ToMM(v.y)]
def layers(x):return [i for i,l in enumerate([p.F_Cu,p.B_Cu]) if x.IsOnLayer(l)]
ps=[];ts=[];vs=[];ks=[];nets={}
for f in b.GetFootprints():
 for d in f.Pads():
  bb=d.GetBoundingBox();size=d.GetSize();row=dict(ref=f.GetReference()+'.'+d.GetNumber(),net=d.GetNetname(),at=xy(d.GetPosition()),box=[p.ToMM(t) for t in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()]],layers=layers(d),drill=p.ToMM(max(d.GetDrillSize().x,d.GetDrillSize().y)),fp=xy(f.GetPosition()),escape=f.GetReference() in ['U2','U3'])
  ps.append(row)
  if d.GetNetname():nets.setdefault(d.GetNetname(),[]).append(d)
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):vs.append(dict(net=t.GetNetname(),at=xy(t.GetPosition()),diameter=p.ToMM(t.GetWidth(p.F_Cu)),drill=p.ToMM(t.GetDrill())))
 else:ts.append(dict(net=t.GetNetname(),a=xy(t.GetStart()),b=xy(t.GetEnd()),layer=0 if t.GetLayer()==p.F_Cu else 1,width=p.ToMM(t.GetWidth())))
for z in b.Zones():
 if z.GetIsRuleArea() and z.GetDoNotAllowTracks():
  bb=z.GetBoundingBox();ks.append([p.ToMM(t) for t in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()]])
work=[]
for n,pads in nets.items():
 seen=set();groups=[]
 for pad in pads:
  if pad.m_Uuid.AsString() in seen:continue
  items=list(conn.GetConnectedItems(pad))+[pad];seen.update(x.m_Uuid.AsString() for x in items);pts=[]
  for x in items:
   if isinstance(x,p.PAD):
    row=next(a for a in ps if a['ref']==x.GetParentFootprint().GetReference()+'.'+x.GetNumber() and a['at']==xy(x.GetPosition()));pts.append(row)
   elif isinstance(x,p.PCB_VIA):pts.append(dict(at=xy(x.GetPosition()),layers=[0,1],escape=False))
   elif isinstance(x,p.PCB_TRACK):
    for v in [x.GetStart(),x.GetEnd()]:pts.append(dict(at=xy(v),layers=layers(x),escape=False))
  groups.append(pts)
 if len(groups)>1:work.append(dict(net=n,groups=groups))
(R/'artifacts/local/r1-route-work.json').write_text(json.dumps(dict(pads=ps,tracks=ts,vias=vs,keepouts=ks,work=work)))
print('Exported',len(work),'disconnected nets')
