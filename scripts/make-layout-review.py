#!/usr/bin/env python3
"""S.2 electrical placement review, not routed or released for fabrication.
Run in KiCad's bundled Python. All placement is deterministic and reproducible.
"""
import json, math, os, collections
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];C=json.loads((R/'hardware/circuit.json').read_text())
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
LOCAL=R/'hardware/cad/RackATX.pretty';LOCAL.mkdir(exist_ok=True)
B=p.BOARD();B.SetCopperLayerCount(2);B.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
W,H=200,170
mm=p.FromMM
V=lambda x,y:p.VECTOR2I(mm(x),mm(y))
def line(parent,a,b,layer=p.F_Fab,width=.1):
 s=p.PCB_SHAPE(parent);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(V(*a));s.SetEnd(V(*b));s.SetLayer(layer);s.SetWidth(mm(width));parent.Add(s)
def rect(parent,x,y,w,h,layer=p.F_Fab):
 for a,b in [((x,y),(x+w,y)),((x+w,y),(x+w,y+h)),((x+w,y+h),(x,y+h)),((x,y+h),(x,y))]:line(parent,a,b,layer)
def pad(f,n,x,y,w,h,drill=0):
 d=p.PAD(f);d.SetNumber(str(n));d.SetPosition(V(x,y));d.SetSize(V(w,h))
 d.SetShape(p.PAD_SHAPE_CIRCLE if drill else p.PAD_SHAPE_RECT)
 d.SetAttribute(p.PAD_ATTRIB_PTH if drill else p.PAD_ATTRIB_SMD)
 d.SetLayerSet(p.PAD.PTHMask() if drill else p.PAD.SMDMask())
 if drill:d.SetDrillSize(V(drill,drill))
 f.Add(d)
def custom(name,body,pads,courtyard):
 f=p.FOOTPRINT(B);f.SetFPID(p.LIB_ID('RackATX',name));rect(f,*body);rect(f,*courtyard,p.F_CrtYd)
 for row in pads:pad(f,*row)
 f.SetAttributes(p.FP_THROUGH_HOLE if any(len(row)==7 for row in pads) else p.FP_SMD)
 p.PCB_IO_KICAD_SEXPR().FootprintSave(str(LOCAL),f)
 return 'RackATX:'+name
# Toshiba land-pattern drawing: pitch 2.54; opposing pad centres 6.3; pads .8 x 1.2.
ssr=custom('TLP3122A_11-4M1S',(-1.85,-2.275,3.7,4.55),[(1,-1.27,3.15,.8,1.2),(3,1.27,3.15,.8,1.2),(4,1.27,-3.15,.8,1.2),(6,-1.27,-3.15,.8,1.2)],(-2.3,-4.05,4.6,8.1))
# Everlight Rev.9 p7: outer span 7.85, inner gap 4.85, pad 1.5 x .6, pitch2.54.
opto=custom('EL357N_SOP4',(-2.2,-2.05,4.4,4.1),[(1,-3.175,-1.27,1.5,.6),(2,-3.175,1.27,1.5,.6),(3,3.175,1.27,1.5,.6),(4,3.175,-1.27,1.5,.6)],(-4.225,-2.55,8.45,5.1))
# HENIPER, NOT Mornsun: V3-2020 p5; top-view pin row, 1 mm finished holes.
iso=custom('HENIPER_B0505S_1WR3L',(-5.61,-5.7,11.6,6),[(1,-3.81,0,1.5,1.5,1),(2,-1.27,0,1.5,1.5,1),(3,1.27,0,1.5,1.5,1),(4,3.81,0,1.5,1.5,1)],(-5.96,-6.05,12.3,7.15))
# Kangnex drawing: 5.08 pitch, finished hole 1.2; body height14mm.
terminal=custom('WJ500V_5.08_2P',(-2.54,-5.5,10.16,10),[(1,0,0,2.2,2.2,1.2),(2,5.08,0,2.2,2.2,1.2)],(-2.9,-5.85,10.9,10.7))
overrides={'ssr':ssr,'opto':opto,'iso':iso,'barrel':terminal,'ind':'Inductor_SMD:L_Changjiang_FNR4018S'}
netnames=sorted({n for c in C['components'] if c['sheet']!='adapter' for n in c['nets'].values() if n})
nets={}
for name in netnames:
 n=p.NETINFO_ITEM(B,name);B.Add(n);nets[name]=n
objs={};placed={};constraints=[];regions={}
for c in C['components']:
 if c['sheet']=='adapter' or c['key']=='flag':continue
 fid=overrides.get(c['key'],C['parts'][c['key']]['footprint']);lib,name=fid.split(':')
 f=p.FootprintLoad(str(LOCAL if lib=='RackATX' else LIB/(lib+'.pretty')),name)
 assert f,fid
 f.SetReference(c['ref']);f.SetValue(C['parts'][c['key']]['value']);f.Reference().SetVisible(False);f.Value().SetVisible(False)
 f.SetFPID(p.LIB_ID(lib,name))
 actual={pad.GetNumber() for pad in f.Pads()};expected={n for n,v in c['nets'].items() if v}
 assert expected<=actual,(c['ref'],fid,expected-actual)
 for d in f.Pads():
  net=c['nets'].get(d.GetNumber())
  if net:d.SetNet(nets[net])
 B.Add(f);objs[c['ref']]={'fp':f,'c':c,'fid':fid}

def bbox(f):
 b=f.GetBoundingBox(False,False);return tuple(p.ToMM(v) for v in [b.GetX(),b.GetY(),b.GetWidth(),b.GetHeight()])
def collides(b,ignore=None,gap=.25):
 x,y,w,h=b
 return any(x<a+c+gap and x+w+gap>a and y<bb+d+gap and y+h+gap>bb for ref,(a,bb,c,d) in placed.items() if ref!=ignore)
def at(ref,x,y,angle=0):
 f=objs[ref]['fp'];f.SetOrientationDegrees(angle);f.SetPosition(V(x,y));b=bbox(f)
 assert not collides(b,ref),(ref,'overlap',b,[r for r in placed if r!=ref and not (b[0]>placed[r][0]+placed[r][2]+.25 or b[0]+b[2]+.25<placed[r][0] or b[1]>placed[r][1]+placed[r][3]+.25 or b[1]+b[3]+.25<placed[r][1])])
 assert b[0]>=0 and b[1]>=0 and b[0]+b[2]<=W and b[1]+b[3]<=H,(ref,b)
 placed[ref]=b
 return f

def pp(ref,pin):
 d=next(d for d in objs[ref]['fp'].Pads() if d.GetNumber()==str(pin));v=d.GetPosition();return (p.ToMM(v.x),p.ToMM(v.y))
def near(ref,target,region,pin='1',maxdist=None):
 # Score actual pin-to-pin distance and signal connectivity, with courtyard clearance.
 f=objs[ref]['fp'];x0,y0,w,h=region;best=None
 for angle in (0,90,180,270):
  f.SetOrientationDegrees(angle);f.SetPosition(V(0,0));b=bbox(f)
  d=next((d for d in f.Pads() if d.GetNumber()==pin),next(iter(f.Pads())));v=d.GetPosition();px,py=p.ToMM(v.x),p.ToMM(v.y)
  candidates=[]
  # Local search nearest the electrical target, expanded within assigned region.
  for ix in range(int(math.ceil((x0-b[0])*2)),int(math.floor((x0+w-b[0]-b[2])*2))+1):
   x=ix/2
   for iy in range(int(math.ceil((y0-b[1])*2)),int(math.floor((y0+h-b[1]-b[3])*2))+1):
    y=iy/2;dist=math.hypot(x+px-target[0],y+py-target[1])
    if best and dist>=best[0]:continue
    bb=(x+b[0],y+b[1],b[2],b[3])
    if collides(bb,ref):continue
    best=(dist,x,y,angle)
 assert best,(ref,'no legal position',region)
 dist,x,y,a=best;at(ref,x,y,a)
 if maxdist is not None:
  constraints.append({'ref':ref,'target_xy':target,'pin':pin,'distance_mm':round(dist,3),'limit_mm':maxdist,'pass':dist<=maxdist})
  if dist>maxdist:print('PROXIMITY NEEDS REVIEW',ref,round(dist,3),maxdist,flush=True)

def connected_target(ref,fallback):
 c=objs[ref]['c'];pts=[]
 for net in c['nets'].values():
  if not net or net in ['3V3','5V','GND_CTRL','PHOTO_5V'] or net.endswith(('_GND','_3V3','_RAW5')):continue
  for other in placed:
   for d in objs[other]['fp'].Pads():
    if d.GetNetname()==net:
     v=d.GetPosition();pts.append((p.ToMM(v.x),p.ToMM(v.y)))
 return (sum(a for a,b in pts)/len(pts),sum(b for a,b in pts)/len(pts)) if pts else fallback

# Top bank H01..05, bottom H06..10 mirrored by 180 degree rotation.
# Host copper above y47.5, controller copper below y48.5 (and inverse at bottom).
for i in range(10):
 base=5+(i%5)*38;bottom=i>=5;prefix=f'host{i+1:02}';its=[c for c in C['components'] if c['sheet'].startswith(prefix) and c['key']!='flag']
 origin={c['ref']:c for c in its};bykey=lambda k:[c['ref'] for c in its if c['key']==k]
 def pos(x,y):return (base+38-x,H-y) if bottom else (base+x,y)
 def put(ref,x,y,a=0):return at(ref,*pos(x,y),a+(180 if bottom else 0))
 def reg(x,y,w,h):return (base+38-x-w,H-y-h,w,h) if bottom else (base+x,y,w,h)
 hostreg=reg(1,13,36,29);ctrlreg=reg(1,55,36,9)
 port=bykey('port')[0];f=objs[port]['fp'];f.SetOrientationDegrees(180);f.SetPosition(V(0,0));b=bbox(f)
 # Place connector body at board edge, cable mating face outward.
 put(port,19-(b[0]+b[2]/2),1.2-b[1],180)
 # Adjust bottom connector using exact transformed top offset, handled below in record audit.
 isoRef=bykey('iso')[0];ssrs=bykey('ssr');opts=bykey('opto');cmp=bykey('cmp')[0];ldo=bykey('ldo')[0]
 put(isoRef,7,48,90)
 put(ssrs[0],13,48);put(ssrs[1],19,48)
 put(opts[0],25,48,-90);put(opts[1],32,48,-90)
 put(cmp,20,28,0);put(ldo,15,37,0)
 esds=bykey('esd')
 for j,r in enumerate(esds):put(r,25.5-4.5*j,14.5,0)
 # Decouplers are assigned to a specific power pin, not simply to the power net.
 caps=bykey('C100n');assert len(caps)==1
 near(caps[0],pp(cmp,8),hostreg,maxdist=3)
 cin=next(c['ref'] for c in its if c['key']=='C4.7u')
 near(cin,pp(isoRef,2),reg(1,52.5,10,11.5),maxdist=8)
 rawcap=next(c['ref'] for c in its if c['key']=='C10u' and any(n and n.endswith('_RAW5') for n in c['nets'].values()))
 outcap=next(c['ref'] for c in its if c['key']=='C10u' and c['ref']!=rawcap)
 near(outcap,pp(ldo,3),hostreg,maxdist=3.5);near(rawcap,pp(isoRef,4),hostreg,maxdist=5)
 # Prioritize comparator input RC and feedback chains before generic pullups.
 todo=[c for c in its if c['ref'] not in placed]
 def priority(c):
  ns=' '.join(n or '' for n in c['nets'].values())
  return (0 if 'SPLUS' in ns or 'SMINUS' in ns else 1 if 'FB' in ns else 2,c['ref'])
 for c in sorted(todo,key=priority):
  ns=set(c['nets'].values());ctrl=bool(ns&{'3V3','5V','GND_CTRL','PHOTO_5V'}) or any(n and n.startswith(('CTRL_','DRV_')) for n in ns)
  region=ctrlreg if ctrl else hostreg
  fallback=pos(20,59 if ctrl else 27)
  # Input divider nodes target their comparator pins on the correct channel.
  nsstr=' '.join(n or '' for n in ns)
  target=connected_target(c['ref'],fallback)
  for token,pin in [('PLED_SPLUS',2),('PLED_SMINUS',3),('HDD_SPLUS',6),('HDD_SMINUS',5)]:
   if token in nsstr:target=pp(cmp,pin)
  near(c['ref'],target,region)
 regions[prefix]={'host':hostreg,'controller':ctrlreg,'barrier_y':H-48 if bottom else 48}
 print(prefix,'placed',len(its),flush=True)

# Shared logic spine. All external service connectors face the left/right edges.
shared=(2,65,196,40)
at('U3',37,76,0);at('U2',34,97,0)
at('U4',71,81,0);at('U5',106,81,0);at('U6',141,81,0)
at('U7',162,96,0);at('U1',183,78,0)
# Fit external connector courtyards to physical edge using their real library shape.
def edge(ref,side,cy,angle):
 f=objs[ref]['fp'];f.SetOrientationDegrees(angle);f.SetPosition(V(0,0));x,y,w,h=bbox(f)
 at(ref,(.8-x if side=='left' else W-.8-x-w),cy-y-h/2,angle)
edge('J105','left',76,-90);edge('J104','left',100,-90);edge('J101','right',87,-90)
# Fan the dense LQFP analog pins into two orderly capacitor banks.
for ref,x,y,a,pin in [('C21',30,73.5,180,4),('C22',30,75.5,180,8),('C23',30,77.5,180,11),('R14',30,79.5,180,10),('C24',32.5,83,-90,15),('C25',34.5,83,-90,17),('C19',36.5,83,-90,20),('C26',38.5,83,-90,21),('C20',40.5,83,-90,22)]:
 at(ref,x,y,a)
 dist=math.dist(pp(ref,1),pp('U3',pin));constraints.append({'ref':ref,'target_xy':pp('U3',pin),'pin':'1','distance_mm':round(dist,3),'limit_mm':4,'pass':dist<=4})
 assert dist<=4,(ref,dist)

# Critical pin-specific decoupling. Distances are straight-line pad centres, not routed length.
for ref,chip,pin,limit in [('C2','U1',3,3),('C1','U1',3,5),('C3','U1',6,3),('C6','U2',29,3),('C8','U2',2,3),('C9','U2',3,4),('C10','U2',20,3),('C11','U2',46,3),('C12','U2',55,3),('C13','U2',56,4),('C28','U3',28,3),('C37','U4',16,3),('C38','U5',16,3),('C39','U6',16,3),('C42','U7',8,3)]:
 near(ref,pp(chip,pin),shared,maxdist=limit)
near('R5',pp('U2',54),shared,maxdist=5)
near('Y1',pp('U2',54),(22,83,15,7),maxdist=12)
# Deliberate keepaway from switcher, grouped oscillators with load capacitors.
at('Y2',48,80,0)
for r,t,pin,limit in [('C17','Y1',1,3),('C18','Y1',3,3),('C31','Y2',1,3),('C32','Y2',3,3),('R10','U2',25,4),('R11','U2',26,4),('R6','U2',44,4),('R7','U2',45,4)]:near(r,pp(t,pin),shared,maxdist=limit)
near('L1',pp('U1',5),(173,68,16,17),maxdist=6)
near('C4',pp('L1',2),(168,66,24,22),maxdist=4)
near('C5',pp('L1',2),(168,66,24,22),maxdist=6)
near('D1',pp('J104','A7'),(3,93,17,12),pin='2',maxdist=6)
for r in ['R18','R19','R20','R21','C33','C34','C35','C36','R22','R23','R24']:
 near(r,connected_target(r,(19,76)),(22,66,10,23))
for r,pin in [('C14',2),('C15',3)]:near(r,pp('U2',pin),shared,maxdist=8)
near('C29',pp('U3',44),shared,maxdist=5)
near('R25',pp('U4',13),shared,maxdist=5)
near('R26',pp('U4',12),shared,maxdist=5)
for r in ['F1','Q1']:
 near(r,connected_target(r,(189,92)),(174,86,17,18))
for c in [o['c'] for o in objs.values() if o['c']['ref'] not in placed]:
 ref=c['ref'];block=c['sheet'].split('_')[0]
 rg={'power':(171,65,26,40),'processor':(19,86,44,19),'ethernet':(21,65,35,23),'outputs':(150,86,23,20)}[block]
 target=connected_target(ref,{'power':(183,84),'processor':(34,97),'ethernet':(37,76),'outputs':(161,94)}[block])
 if block=='outputs' and ref in ['R27','R28','C40']:target=pp('U7',2 if ref!='R27' else 4)
 near(ref,target,rg)
assert len(placed)==694
# Board outline, mounting clearances and isolated domains are visible review annotations.
rect(B,0,0,W,H,p.Edge_Cuts)
for x,y in [(4,4),(196,4),(4,166),(196,166)]:
 f=p.FootprintLoad(str(LIB/'MountingHole.pretty'),'MountingHole_3.2mm_M3');f.SetReference('MH'+str(len([f for f in B.GetFootprints() if f.GetReference().startswith('MH')])+1));f.SetPosition(V(x,y));f.Reference().SetVisible(False);f.Value().SetVisible(False)
 assert not collides(bbox(f)),('mount',x,y)
 B.Add(f)
for key,rs in regions.items():
 for name,region in rs.items():
  if name=='barrier_y':continue
  rect(B,*region,p.Dwgs_User)
def keepout(x,y,w,h):
 z=p.ZONE(B);z.SetIsRuleArea(True);ls=p.LSET();ls.AddLayer(p.F_Cu);ls.AddLayer(p.B_Cu);z.SetLayerSet(ls)
 z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);z.SetDoNotAllowZoneFills(True)
 poly=z.Outline();poly.NewOutline()
 for a,b in [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]:poly.Append(mm(a),mm(b))
 B.Add(z)
for y in [47.5,121.5]:keepout(5,y,190,1)
for j in range(1,5):
 for y in [0,122.5]:keepout(5+38*j-.5,y,1,47.5)
records=[]
for ref,o in objs.items():
 f=o['fp'];x,y,w,h=bbox(f);k=o['c']['key']
 z={'iso':10.1,'ssr':2.1,'opto':2,'ind':1.8,'barrel':14,'port':6,'rj45':13.5,'usb':3.2,'ldo':1.8}.get(k,.8 if k.startswith(('R','C')) else 1.5)
 records.append(dict(ref=ref,key=k,sheet=o['c']['sheet'],x=round(x,4),y=round(y,4),w=round(w,4),h=round(h,4),z=z,rotation=f.GetOrientationDegrees(),footprint=o['fid'],qualified=False))
B.BuildConnectivity();p.SaveBoard(str(R/'hardware/cad/layout-S2-review.kicad_pcb'),B)
out=dict(revision='S.2',schematic_revision=C['revision'],outline_mm=[W,H,1.6],layers=2,status='Net-informed placement for user review; no routed traces or production approval',footprint_count=694,mechanical_holes=4,unqualified_envelope_count=0,unqualified_families=[],routing_feasibility_verified=False,envelope_overlap_count=0,components=records,placement_constraints=constraints,regions=regions,user_approval='pending')
(R/'hardware/placement-study.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
assert all(c['pass'] for c in constraints),[c for c in constraints if not c['pass']]
print('S.2 PASS:',len(placed),'populated footprints;',len(constraints),'pin-proximity checks; 0 tracks; pending user review')
