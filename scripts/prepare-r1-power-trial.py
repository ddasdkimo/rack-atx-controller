#!/usr/bin/env python3
"""Rip up long thin main-supply segments, retain short pin neckdowns. Trial only."""
import wx,sys,shutil,math
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/sys.argv[1];b=p.LoadBoard(str(src));removed=[]
pads={}
for f in b.GetFootprints():
 for d in f.Pads():
  if d.GetNetname():pads.setdefault(d.GetNetname(),[]).append((d.GetPosition().x/1e6,d.GetPosition().y/1e6))
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA):continue
 target={'3V3':.8,'5V':.8,'5V_FUSED':1.,'5V_JACK':1.,'PHOTO_5V':.4}.get(t.GetNetname())
 a=t.GetStart();z=t.GetEnd();mid=((a.x+z.x)/2e6,(a.y+z.y)/2e6)
 near=min((math.dist(mid,q) for q in pads.get(t.GetNetname(),[])),default=100)
 if target and p.ToMM(t.GetWidth())<target and (p.ToMM(t.GetLength())>5 or near>4.5):
  b.Remove(t);removed.append(t)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());out=R/'artifacts/local/R1-power-open.kicad_pcb';p.SaveBoard(str(out),b)
for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(src.with_suffix(e),out.with_suffix(e))
p.ExportSpecctraDSN(b,str(R/'artifacts/local/R1-power-open.dsn'))
print('Removed',len(removed),'long thin main-supply segments; native unconnected',b.GetConnectivity().GetUnconnectedCount(False))
