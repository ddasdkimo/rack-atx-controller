#!/usr/bin/env python3
"""Native connectivity per net; unlike capped DRC reports, this lists all nets."""
from pathlib import Path
import json,sys,collections
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(R/(sys.argv[1] if len(sys.argv)>1 else 'hardware/cad/routing-R1.kicad_pcb')));b.BuildConnectivity();conn=b.GetConnectivity();nets={}
for f in b.GetFootprints():
 for d in f.Pads():
  if d.GetNetname():nets.setdefault(d.GetNetname(),[]).append(d)
report=[]
for name,pads in sorted(nets.items()):
 connected={x.m_Uuid.AsString() for x in conn.GetConnectedItems(pads[0])};connected.add(pads[0].m_Uuid.AsString());missing=[d.GetParentFootprint().GetReference()+'.'+d.GetNumber() for d in pads if d.m_Uuid.AsString() not in connected]
 report.append(dict(net=name,pads=len(pads),all_pads_connected=not missing,pads_outside_first_cluster=missing))
result=dict(native_unrouted=conn.GetUnconnectedCount(False),complete_nets=sum(x['all_pads_connected'] for x in report),total_nets=len(report),nets=report)
(R/'artifacts/local/r1-connectivity.json').write_text(json.dumps(result,indent=2))
for row in report:
 if row['net'] in ['MCU_XP','MCU_XN','MCU_XP_CR','ETH_XI','ETH_XO','BUCK_SW','BUCK_BST','GND_CTRL','H01_GND']:print(row)
print('Native unrouted',result['native_unrouted'],'complete nets',result['complete_nets'],'/',len(report))
