#!/usr/bin/env python3
"""B.2 passive adapter: same schematic nets, 26x34 mm, no active electronics."""
from pathlib import Path
import json,uuid,shutil
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];C=json.loads((R/'hardware/circuit.json').read_text());B=p.BOARD();B.SetCopperLayerCount(2);B.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
lib=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints');V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y));uid=lambda k:str(uuid.uuid5(uuid.NAMESPACE_URL,'rack-atx/B2/'+k))
cs=[c for c in C['components'] if c['sheet']=='adapter'];nets={}
for net in sorted({n for c in cs for n in c['nets'].values() if n}):
 n=p.NETINFO_ITEM(B,net);B.Add(n);nets[net]=n
coords={'JA2':(6,19,90),'JA3':(6,26,90),'JA4':(19,19,90),'JA5':(19,26,90),'JA6':(13,31,90)}
for c in cs:
 fid=C['parts'][c['key']]['footprint'];l,name=fid.split(':');f=p.FootprintLoad(str(lib/(l+'.pretty')),name);f.SetReference(c['ref']);f.SetValue(C['parts'][c['key']]['value']);f.SetFPID(p.LIB_ID(l,name));f.Reference().SetVisible(False);f.Value().SetVisible(False)
 sp=p.KIID_PATH()
 for k in ['adapter-root',c['ref']]:sp.push_back(p.KIID(uid(k)))
 # Schematic instance is checked against native export; root path below is fixed from source.
 f.SetPath(sp)
 if c['ref']=='JA1':
  f.SetOrientationDegrees(180);f.SetPosition(V(0,0));bb=f.GetBoundingBox(False,False);x=13-p.ToMM(bb.GetX())-p.ToMM(bb.GetWidth())/2;y=1-p.ToMM(bb.GetY());f.SetPosition(V(x,y))
 else:
  x,y,a=coords[c['ref']];f.SetOrientationDegrees(a);f.SetPosition(V(x,y))
 for d in f.Pads():
  n=c['nets'].get(d.GetNumber())
  if n:d.SetNet(nets[n])
 B.Add(f)
for a,b in [((0,0),(26,0)),((26,0),(26,34)),((26,34),(0,34)),((0,34),(0,0))]:
 s=p.PCB_SHAPE(B);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(V(*a));s.SetEnd(V(*b));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));B.Add(s)
for label,x,y in [('MB PWR',6,16),('CASE PWR',19,16),('MB RST',6,23),('CASE RST',19,23),('GND  NC',13,28.5),('ATX B2',13,13.5)]:
 t=p.PCB_TEXT(B);t.SetText(label);t.SetPosition(V(x,y));t.SetTextSize(V(1,1));t.SetTextThickness(p.FromMM(.15));t.SetLayer(p.F_SilkS);B.Add(t)
B.BuildConnectivity();out=R/'hardware/cad/B2/placement/adapter.kicad_pcb';p.SaveBoard(str(out),B);p.ExportSpecctraDSN(B,str(R/'artifacts/local/B2-adapter.dsn'))
# Same conservative fabrication geometry rules; no host-to-controller boundary on this passive board.
pro=json.loads((R/'hardware/cad/B2/rack-atx-controller.kicad_pro').read_text());pro['net_settings']['netclass_patterns']=[];(R/'hardware/cad/B2/placement/adapter.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
print('Adapter',len(cs),'components',B.GetConnectivity().GetUnconnectedCount(False),'unrouted')
