#!/usr/bin/env python3
"""Prepare an incremental trial, preserving native constraints and exact pads."""
from pathlib import Path
import json,shutil
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(R/'artifacts/local/R1-ground-bridged.kicad_pcb'))
# Turn the two starved connector thermals to the alternate diagonal axes.
for f in b.GetFootprints():
 if f.GetReference() in ['J02','J10']:
  for d in f.Pads():
   if d.GetNumber()=='9':d.SetThermalSpokeAngleDegrees(45)
# Remove exact same-net duplicate segments, never unique connectivity.
seen=set();removed=0
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA):continue
 a=t.GetStart();z=t.GetEnd();key=(t.GetNetCode(),t.GetLayer(),t.GetWidth(),tuple(sorted([(a.x,a.y),(z.x,z.y)])))
 if key in seen:b.Remove(t);removed+=1
 else:seen.add(key)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());out=R/'artifacts/local/R1-next.kicad_pcb';p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile((R/'hardware/cad/routing-R1.kicad_pcb').with_suffix(ext),out.with_suffix(ext))
assert p.ExportSpecctraDSN(b,str(R/'artifacts/local/R1.dsn'))
print('Prepared incremental trial; exact duplicate segments removed:',removed)
