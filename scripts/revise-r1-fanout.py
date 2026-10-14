#!/usr/bin/env python3
"""Route-driven refinement, preserved as a separate trial for native DRC."""
import wx,json,shutil
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/'artifacts/local/R1-repaired.kicad_pcb';b=p.LoadBoard(str(src));removed=[]
for ext in ['.kicad_pcb','.kicad_pro','.kicad_dru']:shutil.copyfile(src.with_suffix(ext),(R/'artifacts/local/R1-before-fanout.kicad_pcb').with_suffix(ext))
md=set('ETH_RXN ETH_RXP ETH_TXN ETH_TXP RJ_RD_N RJ_RD_P'.split());usb=set('USB_DM USB_DP USB_DM_MCU USB_DP_MCU'.split());critical=set('BUCK_SW BUCK_BST MCU_XN MCU_XP MCU_XP_CR ETH_XI ETH_XO'.split())
for t in list(b.GetTracks()):
 delete=t.GetNetname() in md|usb
 if not isinstance(t,p.PCB_VIA):
  a=t.GetStart();z=t.GetEnd();x0=min(a.x,z.x)/1e6;x1=max(a.x,z.x)/1e6;y0=min(a.y,z.y)/1e6;y1=max(a.y,z.y)/1e6
  if t.GetLayer()==p.F_Cu and x1>=22.3 and x0<=34 and y1>=69 and y0<=83 and t.GetNetname() not in critical:delete=True
 else:
  q=t.GetPosition();x,y=q.x/1e6,q.y/1e6
  if 20<x<50 and 85<y<109 and not (t.GetNetname()=='GND_CTRL' and 32.9<=x<=35.1 and 95.9<=y<=98.1):t.SetWidth(p.FromMM(.5))
 if delete:b.Remove(t);removed.append(t)
for f in b.GetFootprints():
 if f.GetReference() in ['R10','R11']:f.SetOrientationDegrees(f.GetOrientationDegrees()+180)
 if f.GetReference() in ['J%02d'%i for i in range(1,11)]:
  for pad in f.Pads():
   if pad.GetNumber()=='9':pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
out=R/'artifacts/local/R1-fanout.kicad_pcb';b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(out),b)
pro=json.loads(src.with_suffix('.kicad_pro').read_text());pro['board']['design_settings']['rules'].update(min_hole_clearance=.2,min_hole_to_hole=.25)
out.with_suffix('.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
rules=src.with_suffix('.kicad_dru').read_text()
rules+='''\n# JLCPCB 2026-10-14: vias differ from component holes. Conservative 0.25 mm via-hole spacing.
(rule "Component drill spacing" (condition "A.Type == 'Pad' || B.Type == 'Pad'") (constraint hole_to_hole (min 0.45mm)))
(rule "Component hole to copper" (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'") (constraint hole_clearance (min 0.28mm)))
'''
out.with_suffix('.kicad_dru').write_text(rules)
print('Removed',len(removed),'objects for USB / MDI rerouting; existing power rails retained.')
