#!/usr/bin/env python3
"""Read-only native geometry reference for independent Gerber/Excellon/CPL audit.
Run with KiCad's wx/pcbnew Python. No PCB mutation or netlist export.
"""
import argparse, csv, hashlib, json, math
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
r={}
for name,base in [('controller','rack-atx-controller'),('adapter','adapter')]:
 src=ROOT/f'hardware/cad/B2/{base}.kicad_pcb';b=p.LoadBoard(str(src));circles=[];slots=[];parts={}
 for f in b.GetFootprints():
  parts[f.GetReference()]={'x_mm':p.ToMM(f.GetPosition().x),'y_mm':-p.ToMM(f.GetPosition().y),'rotation':f.GetOrientationDegrees()%360,'side':'Bottom' if f.IsFlipped() else 'Top'}
  for d in f.Pads():
   sx,sy=[p.ToMM(v) for v in (d.GetDrillSize().x,d.GetDrillSize().y)]
   if not sx:continue
   x,y=p.ToMM(d.GetPosition().x),-p.ToMM(d.GetPosition().y);pl='NPTH' if d.GetAttribute()==p.PAD_ATTRIB_NPTH else 'PTH'
   if abs(sx-sy)<1e-6:circles.append([x,y,sx,pl])
   else:
    # Native orientation is counterclockwise in the exported Gerber coordinate system.
    ang=math.radians(d.GetOrientationDegrees());dx,dy=(max(sx-sy,0)/2,max(sy-sx,0)/2)
    vx,vy=dx*math.cos(ang)-dy*math.sin(ang),dx*math.sin(ang)+dy*math.cos(ang)
    slots.append({'ref':f.GetReference(),'pin':d.GetNumber(),'ends':[[x-vx,y-vy],[x+vx,y+vy]],'diameter_mm':min(sx,sy),'plating':pl})
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):circles.append([p.ToMM(t.GetPosition().x),-p.ToMM(t.GetPosition().y),p.ToMM(t.GetDrill()),'PTH'])
 r[name]={'pcb_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'round_drills':circles,'slots':slots,'components':parts}
args.output.write_text(json.dumps(r,indent=2)+'\n')
print('Exported native geometry reference for two boards')
