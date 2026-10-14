#!/usr/bin/env python3
"""Import a routing trial into a separate board; never auto-approve the candidate."""
import shutil,sys
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];source=R/(sys.argv[2] if len(sys.argv)>2 else 'hardware/cad/routing-R1.kicad_pcb');b=p.LoadBoard(str(source))
def sig():return sorted((f.GetReference(),f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),tuple(sorted((d.GetNumber(),d.GetNetname()) for d in f.Pads()))) for f in b.GetFootprints())
seed=[t.Duplicate() for t in b.GetTracks()]
s=sig();assert p.ImportSpecctraSES(b,str(R/(sys.argv[1] if len(sys.argv)>1 else 'artifacts/local/R1-stable.ses')));
for old,new in zip(s,sig()):
 if old!=new:print('DIFF',old[:4],new[:4], 'nets equal',old[4]==new[4])
assert all(a[0]==z[0] and abs(a[1]-z[1])<=100 and abs(a[2]-z[2])<=100 and abs((a[3]-z[3])%360)<.001 and a[4]==z[4] for a,z in zip(s,sig())),'Router changed beyond DSN coordinate quantization'
# Restore the exact source coordinates after <=0.1 um DSN quantization.
fps={f.GetReference():f for f in b.GetFootprints()}
for ref,x,y,angle,_ in s:
 fps[ref].SetPosition(p.VECTOR2I(x,y));fps[ref].SetOrientationDegrees(angle)
# Some DSN normalizations drop overlapping protected segments. Restore the
# missing BUCK_SW seed branch by geometry, avoiding exact duplicates; native DRC checks
# any interaction with newly routed copper before adoption.
def key(t):
 if isinstance(t,p.PCB_VIA):return ('via',t.GetNetname(),round(t.GetPosition().x/100),round(t.GetPosition().y/100))
 ends=sorted([(round(t.GetStart().x/100),round(t.GetStart().y/100)),(round(t.GetEnd().x/100),round(t.GetEnd().y/100))])
 return (t.GetNetname(),t.GetLayer(),t.GetWidth(),tuple(ends))
seen={key(t) for t in b.GetTracks()};restored=0
for t in seed:
 if t.GetNetname()!='BUCK_SW' or isinstance(t,p.PCB_VIA):continue
 if key(t) not in seen:
  if isinstance(t,p.PCB_VIA):t.SetPosition(p.VECTOR2I(round(t.GetPosition().x/100)*100,round(t.GetPosition().y/100)*100))
  else:
   t.SetStart(p.VECTOR2I(round(t.GetStart().x/100)*100,round(t.GetStart().y/100)*100));t.SetEnd(p.VECTOR2I(round(t.GetEnd().x/100)*100,round(t.GetEnd().y/100)*100))
  b.Add(t);seen.add(key(t));restored+=1
print('Restored protected seed segments:',restored)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
out=R/'artifacts/local/R1-general.kicad_pcb';p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(source.with_suffix(ext),out.with_suffix(ext))
print('Candidate',len(b.GetTracks()),'copper objects;',b.GetConnectivity().GetUnconnectedCount(False),'native unrouted')
