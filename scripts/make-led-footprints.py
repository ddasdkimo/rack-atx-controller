#!/usr/bin/env python3
"""KiCad LED lands unchanged; move horizontal silk to Fab to leave readable label space."""
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];lib=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/LED_SMD.pretty')
for name in ['LED_0603_1608Metric','LED_0805_2012Metric']:
 f=p.FootprintLoad(str(lib),name);f.SetFPID(p.LIB_ID('RackATX',name+'_CathodeSilk'))
 for g in f.GraphicalItems():
  if g.GetLayer()==p.F_SilkS:
   if g.GetStart().x!=g.GetEnd().x:g.SetLayer(p.F_Fab)
   else:g.SetWidth(p.FromMM(.15))
 p.PCB_IO_KICAD_SEXPR().FootprintSave(str(R/'hardware/cad/RackATX.pretty'),f)
