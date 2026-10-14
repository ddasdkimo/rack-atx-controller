#!/usr/bin/env python3
"""Remove DRC-identified dangling ends from a local trial, preserving connectivity."""
from pathlib import Path
import wx,json,sys,shutil
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/sys.argv[1];drc=json.loads((R/sys.argv[2]).read_text());b=p.LoadBoard(str(src));b.BuildConnectivity();before=b.GetConnectivity().GetUnconnectedCount(False)
kinds={'track_dangling'}
if '--remove-unused-vias' in sys.argv:
 assert before==0,'Finish connectivity before removing unused via anchors'
 kinds.add('via_dangling')
uuids={i['uuid'] for v in drc['violations'] if v['type'] in kinds for i in v['items']}
removed=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in uuids:b.Remove(t);removed.append(t)
for f in b.GetFootprints():
 if f.GetReference() in ['J02','J10']:
  for pad in f.Pads():
   if pad.GetNumber()=='9':
    pad.SetThermalSpokeAngleDegrees(0)
    if f.GetReference()=='J02':pad.SetThermalGap(p.FromMM(.2))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();now=b.GetConnectivity().GetUnconnectedCount(False)
assert now<=before,('Cleanup worsened connectivity',before,now)
out=R/'artifacts/local/R1-clean.kicad_pcb';p.SaveBoard(str(out),b)
if src!=out:
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(src.with_suffix(ext),out.with_suffix(ext))
print('Removed',len(uuids),'dangling objects; native unrouted',now)
