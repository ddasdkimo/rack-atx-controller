#!/usr/bin/env python3
"""Give starved SMD ground pads explicit wired connections instead of a weak pour spoke."""
import wx,json,shutil
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/'artifacts/local/R1-repaired.kicad_pcb';b=p.LoadBoard(str(src));rep=json.loads((R/'artifacts/local/r1-fanout-repaired-drc.json').read_text());ids={x['uuid'] for v in rep['violations'] if v['type']=='starved_thermal' for x in v['items']};changed=[]
for f in b.GetFootprints():
 for d in f.Pads():
  if d.m_Uuid.AsString() in ids and d.GetAttribute()==p.PAD_ATTRIB_SMD:d.SetLocalZoneConnection(p.ZONE_CONNECTION_NONE);changed.append(f.GetReference()+'.'+d.GetNumber())
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());out=R/'artifacts/local/R1-global-base.kicad_pcb';p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(src.with_suffix(ext),out.with_suffix(ext))
print('Explicit ground routing required:',changed)
