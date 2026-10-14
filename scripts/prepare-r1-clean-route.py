#!/usr/bin/env python3
"""Independent reroute trial without crowded early ground fanout. No release edits."""
import wx,shutil
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(R/'hardware/cad/routing-R1.kicad_pcb'))
critical=set('BUCK_SW BUCK_BST MCU_XN MCU_XP MCU_XP_CR ETH_XI ETH_XO'.split());removed=[];seen=set()
for t in list(b.GetTracks()):
 keep=t.GetNetname() in critical
 if isinstance(t,p.PCB_VIA):keep=t.GetNetname()=='GND_CTRL' and 32.9<=p.ToMM(t.GetPosition().x)<=35.1 and 95.9<=p.ToMM(t.GetPosition().y)<=98.1
 else:
  a=t.GetStart();z=t.GetEnd();key=(t.GetNetCode(),t.GetLayer(),t.GetWidth(),tuple(sorted([(a.x,a.y),(z.x,z.y)])))
  if key in seen:keep=False
  seen.add(key)
 if not keep:b.Remove(t);removed.append(t)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());out=R/'artifacts/local/R1-clean-start.kicad_pcb';p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile((R/'hardware/cad/routing-R1.kicad_pcb').with_suffix(ext),out.with_suffix(ext))
p.ExportSpecctraDSN(b,str(R/'artifacts/local/R1.dsn'));print('Remaining seed copper objects',len(b.GetTracks()))
