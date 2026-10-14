#!/usr/bin/env python3
"""Apply legible silk and conservative ground pours to a review candidate, then run DRC separately."""
from pathlib import Path
import sys,json,uuid,shutil
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/sys.argv[1];out=R/sys.argv[2];b=p.LoadBoard(str(src));c=json.loads((R/'hardware/circuit.json').read_text());byref={c['ref']:c for c in c['components']};V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
for f in b.GetFootprints():
 ref=f.GetReference();key=byref.get(ref,{}).get('key','')
 if key in ['ledred','ledgreen']:
  lib,name=c['parts'][key]['footprint'].split(':');f.SetFPID(p.LIB_ID(lib,name))
 for g in list(f.GraphicalItems()):
  if g.GetLayer()!=p.F_SilkS:continue
  if key in ['ledred','ledgreen'] and isinstance(g,p.PCB_SHAPE) and g.GetStart().x!=g.GetEnd().x:g.SetLayer(p.F_Fab)
  elif isinstance(g,p.PCB_SHAPE):g.SetWidth(p.FromMM(.15))
 if ref.startswith('JA'):
  sp=p.KIID_PATH()
  for k in ['adapter-root',ref]:sp.push_back(p.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,'rack-atx/B2/'+k))))
  f.SetPath(sp)
for t in b.GetDrawings():
 if isinstance(t,p.PCB_TEXT):
  t.SetTextSize(V(1,1));t.SetTextThickness(p.FromMM(.15));q=t.GetPosition()
  if t.GetText() in ['PWR','RST']:
   y=p.ToMM(q.y);t.SetPosition(V(p.ToMM(q.x),26.55 if y<55 else 83.45))
if '--planes' in sys.argv:
 def zone(net,layer,pts):
  z=p.ZONE(b);z.SetLayer(layer);z.SetNetCode(b.FindNet(net).GetNetCode());z.SetLocalClearance(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.2));poly=z.Outline();poly.NewOutline()
  for x,y in pts:poly.Append(p.FromMM(x),p.FromMM(y))
  b.Add(z)
 # Controller planes stop at the isolation barriers and avoid the RJ45 magnetics body.
 outline=[(.7,22.6),(99.3,22.6),(99.3,87.4),(.7,87.4),(.7,59),(14,59),(14,39),(.7,39)]
 for layer in [p.F_Cu,p.B_Cu]:zone('GND_CTRL',layer,outline)
 for i in range(10):
  x=5+(i%5)*18;y=.7 if i<5 else 88.6
  for layer in [p.F_Cu,p.B_Cu]:zone(f'H{i+1:02}_GND',layer,[(x+.6,y),(x+17.4,y),(x+17.4,y+20.7),(x+.6,y+20.7)])
 b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones())
b.BuildConnectivity();p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:
 f=src.with_suffix(ext)
 if f.exists() and f!=out.with_suffix(ext):shutil.copyfile(f,out.with_suffix(ext))
print(out.name,len(b.GetTracks()),'copper;',b.GetConnectivity().GetUnconnectedCount(False),'unrouted')
