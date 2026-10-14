#!/usr/bin/env python3
"""Seed R.1 from immutable R.0: isolated B.Cu ground planes and local stitching.
Run with KiCad Python. Outputs a new candidate; never modifies R.0.
"""
import json, math, shutil
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(R/'hardware/cad/routing-R0.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
# Route-informed adjustment: preserve nets and parts, avoid crystal crossing.
fps['Y1'].SetOrientationDegrees(fps['Y1'].GetOrientationDegrees()+180)
ca=p.VECTOR2I(fps['C17'].GetPosition());cb=p.VECTOR2I(fps['C18'].GetPosition())
fps['C17'].SetPosition(cb);fps['C18'].SetPosition(ca)
# Reuse only pure geometry helpers, never execute the R.0 generator.
text=(R/'scripts/start-local-routing.py').read_text()
exec(text[text.index('def xy('):text.index('keepouts=[]')])
keepouts=[box(z) for z in b.Zones() if z.GetIsRuleArea()]
segments=[(xy(t), (p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)),t.GetNetname(),p.ToMM(t.GetWidth())) for t in b.GetTracks()]
allpads=[d for f in b.GetFootprints() for d in f.Pads() if d.IsOnLayer(p.F_Cu)]
holes=[(xy(d),p.ToMM(max(d.GetDrillSize().x,d.GetDrillSize().y))) for d in allpads if d.GetDrillSize().x]
viapoints=[];added=[];deferred=[]
def vec(a):return p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]))
def safe(a,v,n,width=.25):
 if not (1<v[0]<199 and 1<v[1]<169):return False
 if any(hits(a,v,k,.32) for k in keepouts):return False
 for d in allpads:
  dn=d.GetNetname()
  if dn==n:continue
  gap=1.01 if dn and domain(dn)!=domain(n) else .21
  if hits(a,v,box(d),width/2+gap) or hits(v,v,box(d),.3+gap):return False
 if any(nn!=n and (segdist(a,v,u,w)<width/2+ww/2+.21 or point_seg(v,u,w)<.3+ww/2+.21) for u,w,nn,ww in segments):return False
 if any(math.dist(v,h)<.15+dia/2+.451 for h,dia in holes):return False
 if any(math.dist(v,q)<(.751 if nn==n else 1.21 if domain(nn)!=domain(n) else .811) for q,nn in viapoints):return False
 return True
def addvia(a,n):
 v=p.PCB_VIA(b);v.SetPosition(vec(a));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(b.FindNet(n).GetNetCode());b.Add(v);viapoints.append((a,n));holes.append((a,.3))
def track(a,v,n):
 if math.dist(a,v)<1e-6:return
 t=p.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(v));t.SetWidth(p.FromMM(.25));t.SetLayer(p.F_Cu);t.SetNetCode(b.FindNet(n).GetNetCode());b.Add(t);segments.append((a,v,n,.25))
# EPAD's paste grid is already present in the library footprint. Thermal vias
# require solder-wicking / bottom tenting review before assembly release.
for x in [33,34,35]:
 for y in [96,97,98]:addvia((x,y),'GND_CTRL')
for f in b.GetFootprints():
 for d in f.Pads():
  n=d.GetNetname()
  if n!='GND_CTRL' and not (n.startswith('H') and n.endswith('_GND')):continue
  if d.GetDrillSize().x or not d.IsOnLayer(p.F_Cu) or (f.GetReference()=='U2' and d.GetNumber()=='57'):continue
  a=xy(d);found=False
  # Prefer a nearby existing same-net via, avoiding gratuitous holes.
  for v,nn in viapoints:
   if nn==n and math.dist(a,v)<1.5 and all(not hits(a,v,box(dd),.335) for dd in allpads if dd.GetNetname()!=n) and all(not hits(a,v,k,.135) for k in keepouts) and all(nn2==n or segdist(a,v,u,w)>=.125+ww/2+.21 for u,w,nn2,ww in segments):
    track(a,v,n);found=True;break
  if found:continue
  # Start outside the pad to avoid unfilled via-in-pad solder loss.
  bb=box(d)
  for radius in [.9,1.1,1.4,1.8,2.2]:
   for theta in [0,90,180,270,45,135,225,315]:
    angle=math.radians(theta);v=(a[0]+radius*math.cos(angle),a[1]+radius*math.sin(angle))
    if hits(v,v,bb,.31):continue
    if safe(a,v,n):addvia(v,n);track(a,v,n);added.append(f.GetReference()+'.'+d.GetNumber());found=True;break
   if found:break
  if not found:deferred.append(f.GetReference()+'.'+d.GetNumber())
# Ground planes stay in their own physical domains. Use native DRC rules for
# the additional cross-domain 1 mm gap (functional low-voltage rule only).
regions=[('GND_CTRL',(1,48.75,199,121.25))]
for i in range(10):
 x=5+(i%5)*38;y0,y1=(1,47.25) if i<5 else (122.75,169)
 regions.append((f'H{i+1:02}_GND',(x+.25,y0,x+37.75,y1)))
for n,(x0,y0,x1,y1) in regions:
 z=p.ZONE(b);z.SetLayer(p.B_Cu);z.SetNetCode(b.FindNet(n).GetNetCode());z.SetZoneName(n+' reference');z.SetLocalClearance(p.FromMM(.25));z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetMinThickness(p.FromMM(.2));z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
 poly=z.Outline();poly.NewOutline()
 for pt in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:poly.Append(*[p.FromMM(v) for v in pt])
 b.Add(z)
# WIZnet guide: no power/GND pour below the integrated magnetics/RJ45 body.
z=p.ZONE(b);z.SetIsRuleArea(True);z.SetZoneName('RJ45 magnetics no planes');z.SetLayerSet(p.LSET.AllCuMask());z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False);z.SetDoNotAllowZoneFills(True)
poly=z.Outline();poly.NewOutline()
for x,y in [(0,67),(22.3,67),(22.3,85),(0,85)]:poly.Append(p.FromMM(x),p.FromMM(y))
b.Add(z)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
path=R/'artifacts/local/R1-seed.kicad_pcb';p.SaveBoard(str(path),b)
shutil.copyfile(R/'hardware/cad/routing-R1.kicad_pro',path.with_suffix('.kicad_pro'))
shutil.copyfile(R/'hardware/cad/routing-R1.kicad_dru',path.with_suffix('.kicad_dru'))
print('Ground stitching:',len(viapoints),'vias;',len(added),'new pad branches;',len(deferred),'deferred',deferred,'native unconnected',b.GetConnectivity().GetUnconnectedCount(False))
(R/'artifacts/local/r1-ground-stage.json').write_text(json.dumps(dict(vias=len(viapoints),branches=added,deferred=deferred),indent=2))
print('DSN export:',p.ExportSpecctraDSN(b,str(R/'artifacts/local/R1.dsn')))
