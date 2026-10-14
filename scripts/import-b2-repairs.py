#!/usr/bin/env python3
"""Import conservative route candidates into a local board for native DRC."""
import wx,json,shutil,sys
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/(sys.argv[1] if len(sys.argv)>1 else 'artifacts/local/B2-routed.kicad_pcb');b=p.LoadBoard(str(src));rep=json.loads((R/'artifacts/local/b2-repair-routes.json').read_text())
for r in rep['routes']:
 for u,v in zip(r['points'],r['points'][1:]):
  if u[0]!=v[0]:
   at=p.VECTOR2I(p.FromMM(u[1]),p.FromMM(u[2]))
   existing=[x for x in b.GetTracks() if isinstance(x,p.PCB_VIA) and x.GetNetname()==r['net']]+[x for f in b.GetFootprints() for x in f.Pads() if x.GetDrillSize().x and x.GetNetname()==r['net']]
   if any((x.GetPosition()-at).EuclideanNorm()<1000 for x in existing):continue
   via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(p.FromMM(u[1]),p.FromMM(u[2])));via.SetWidth(p.FromMM(.5));via.SetDrill(p.FromMM(.3));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(b.FindNet(r['net']).GetNetCode());b.Add(via)
  elif u[1:]!=v[1:]:
   t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(u[1]),p.FromMM(u[2])));t.SetEnd(p.VECTOR2I(p.FromMM(v[1]),p.FromMM(v[2])));t.SetWidth(p.FromMM(r['width']));t.SetLayer(p.F_Cu if u[0]==0 else p.B_Cu);t.SetNetCode(b.FindNet(r['net']).GetNetCode());b.Add(t)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();out=R/'artifacts/local/B2-repaired.kicad_pcb';p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(src.with_suffix(ext),out.with_suffix(ext))
print('Imported',len(rep['routes']),'repair branches; native unrouted',b.GetConnectivity().GetUnconnectedCount(False))
