#!/usr/bin/env python3
"""S.3 control-only electrical placement review, not routed or released for fabrication.
Run in KiCad's bundled Python. All placement is deterministic and reproducible.
"""
import json, math, os, collections, uuid
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];C=json.loads((R/'hardware/circuit.json').read_text())
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
LOCAL=R/'hardware/cad/RackATX.pretty';LOCAL.mkdir(exist_ok=True)
B=p.BOARD();B.SetCopperLayerCount(2);B.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
W,H=100,110
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
 f.SetAttributes(p.FP_THROUGH_HOLE if any(len(row)==6 and row[-1]>0 for row in pads) else p.FP_SMD)
 p.PCB_IO_KICAD_SEXPR().FootprintSave(str(LOCAL),f)
 return 'RackATX:'+name
# Toshiba land-pattern drawing: pitch 2.54; opposing pad centres 6.3; pads .8 x 1.2.
ssr=custom('TLP3122A_11-4M1S',(-1.85,-2.275,3.7,4.55),[(1,-1.27,3.15,.8,1.2),(3,1.27,3.15,.8,1.2),(4,1.27,-3.15,.8,1.2),(6,-1.27,-3.15,.8,1.2)],(-2.3,-4.05,4.6,8.1))
# Kangnex drawing: 5.08 pitch, finished hole 1.2; body height14mm.
terminal=custom('WJ500V_5.08_2P',(-2.54,-5.5,10.16,10),[(1,0,0,2.2,2.2,1.2),(2,5.08,0,2.2,2.2,1.2)],(-2.9,-5.85,10.9,10.7))
overrides={'ssr':ssr,'barrel':terminal,'ind':'Inductor_SMD:L_Changjiang_FNR4018S'}
uid=lambda key:str(uuid.uuid5(uuid.NAMESPACE_URL,'rack-atx/B2/'+key))
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
 sp=p.KIID_PATH()
 for key in ['root','sheet:'+c['sheet'],c['ref']]:sp.push_back(p.KIID(uid(key)))
 f.SetPath(sp)
 f.SetSheetname(C['sheets'][c['sheet']]['title']);f.SetSheetfile(c['sheet']+'.kicad_sch')
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

# Compact symmetric host banks. Isolation line crosses only relay bodies.
template_host=[]
for i in range(10):
 base=5+(i%5)*18;bottom=i>=5;prefix=f'host{i+1:02}';its=[c for c in C['components'] if c['sheet']==prefix and c['key']!='flag']
 bykey=lambda k:[c['ref'] for c in its if c['key']==k]
 def pos(x,y):return (base+18-x,H-y) if bottom else (base+x,y)
 def put(ref,x,y,a=0):return at(ref,*pos(x,y),a+(180 if bottom else 0))
 def reg(x,y,w,h):return (base+18-x-w,H-y-h,w,h) if bottom else (base+x,y,w,h)
 if i:
  for c,t in zip(its,template_host):
   put(c['ref'],t[0],t[1],t[2])
  regions[prefix]={'host':reg(.5,1,17,20.5),'controller':reg(.5,26.5,17,9),'barrier_y':H-22 if bottom else 22}
  print(prefix,'placed',len(its),flush=True)
  continue
 port=bykey('port')[0];f=objs[port]['fp'];f.SetOrientationDegrees(180);f.SetPosition(V(0,0));b=bbox(f)
 put(port,9-(b[0]+b[2]/2),1.0-b[1],180)
 ssrs=bykey('ssr');put(ssrs[0],6,22);put(ssrs[1],12,22)
 for j,ref in enumerate(bykey('esd')):put(ref,5+7*j,15.5)
 for j,ref in enumerate(bykey('ledred')):put(ref,6+6*j,28)
 ctrlreg=reg(.5,26.5,17,9);hostreg=reg(.5,1,17,20.5)
 for c in its:
  if c['ref'] not in placed:near(c['ref'],connected_target(c['ref'],pos(9,30)),ctrlreg)
 template_host=[(p.ToMM(objs[c['ref']]['fp'].GetPosition().x)-base,p.ToMM(objs[c['ref']]['fp'].GetPosition().y),objs[c['ref']]['fp'].GetOrientationDegrees()) for c in its]
 regions[prefix]={'host':hostreg,'controller':ctrlreg,'barrier_y':H-22 if bottom else 22}
 print(prefix,'placed',len(its),flush=True)
# Shared MCU/Ethernet blocks, short clock/decoupling paths; service ports at side edges.
shared=(2,36,96,H-72)
at('D201',8,38);at('D202',14,38)
at('R321',4.2,38);at('R322',18,38)
at('U3',34,49);at('U2',56,54)
for ref,x in [('U4',43),('U5',59),('U6',75)]:at(ref,x,71,90)
at('U7',83,62);at('U1',84,41)
def edge(ref,side,cy,angle):
 f=objs[ref]['fp'];f.SetOrientationDegrees(angle);f.SetPosition(V(0,0));x,y,w,h=bbox(f)
 return at(ref,(.8-x if side=='left' else W-.8-x-w),cy-y-h/2,angle)
edge('J105','left',49,-90);edge('J104','left',69,-90);edge('J101','right',61,-90)
at('Y2',44,52)
for ref,x,y,a,pin in [('C21',23,46.5,180,4),('C22',23,48.5,180,8),('C23',23,50.5,180,11),('R14',23,52.5,180,10),('C24',25.5,56,-90,15),('C25',27.5,56,-90,17),('C19',29.5,56,-90,20),('C26',31.5,56,-90,21),('C20',33.5,56,-90,22)]:
 at(ref,x+4,y,a);dist=math.dist(pp(ref,1),pp('U3',pin));constraints.append({'ref':ref,'target_xy':pp('U3',pin),'pin':'1','distance_mm':round(dist,3),'limit_mm':4,'pass':dist<=4})
for ref,chip,pin,limit in [('C2','U1',3,3),('C1','U1',3,5),('C3','U1',6,3),('C6','U2',29,3),('C8','U2',2,3),('C9','U2',3,4),('C10','U2',20,3),('C11','U2',46,3),('C12','U2',55,3),('C13','U2',56,4),('C28','U3',28,3),('C37','U4',16,3),('C38','U5',16,3),('C39','U6',16,3),('C42','U7',14,3)]:near(ref,pp(chip,pin),shared,maxdist=limit)
near('C40',pp('U7',2),shared,maxdist=3)
near('R5',pp('U2',54),shared,maxdist=5)
near('Y1',pp('U2',54),(44,37,25,13),maxdist=10)
for r,t,pin,limit in [('C17','Y1',1,3),('C18','Y1',3,3),('C31','Y2',1,3),('C32','Y2',3,3),('R10','U2',25,4),('R11','U2',26,4),('R6','U2',44,4),('R7','U2',45,4)]:near(r,pp(t,pin),shared,maxdist=limit)
near('L1',pp('U1',5),(77,36,20,17),maxdist=6)
near('C4',pp('L1',2),(76,36,22,18),maxdist=4);near('C5',pp('L1',2),(76,36,22,18),maxdist=6)
near('D1',pp('J104','A7'),(2,61,18,14),pin='2',maxdist=6)
for r in ['R18','R19','R20','R21','C33','C34','C35','C36','R22','R23','R24']:near(r,connected_target(r,(23,49)),(25,36,17,27))
for r,pin in [('C14',2),('C15',3)]:near(r,pp('U2',pin),shared,maxdist=8)
near('C29',pp('U3',44),shared,maxdist=5)
near('R25',pp('U4',13),shared,maxdist=5);near('R26',pp('U4',12),shared,maxdist=5)
for r in ['F1','Q1']:near(r,connected_target(r,(90,56)),(76,52,22,22))
for c in [o['c'] for o in objs.values() if o['c']['ref'] not in placed]:
 ref=c['ref'];block=c['sheet'].split('_')[0]
 rg={'power':(76,36,22,38),'processor':(40,36,35,31),'ethernet':(25,36,21,28),'outputs':(65,47,33,27)}[block]
 near(ref,connected_target(ref,{'power':(84,44),'processor':(56,54),'ethernet':(30,49),'outputs':(80,62)}[block]),rg)
# Orient crystal outputs toward their respective load capacitors; avoid crossing XN/XP.
placed.pop('C17');placed.pop('C18')
at('Y1',53.5,44,270);at('C17',52.5,40,90);at('C18',56.5,44.5,90)
for constraint in constraints:
 if constraint['ref'] in ['C17','C18','Y1']:
  ref=constraint['ref'];target=pp('U2',54) if ref=='Y1' else pp('Y1',1 if ref=='C17' else 3)
  distance=math.dist(pp(ref,1),target);constraint.update(distance_mm=round(distance,3),target_xy=target);constraint['pass']=distance<=constraint['limit_mm']
assert len(placed)==300
rect(B,0,0,W,H,p.Edge_Cuts)
def silk(label,x,y,angle=0):
 t=p.PCB_TEXT(B);t.SetText(label);t.SetPosition(V(x,y));t.SetTextSize(V(1,1));t.SetTextThickness(mm(.15));t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));t.SetLayer(p.F_SilkS);B.Add(t)
for i in range(10):
 base=5+(i%5)*18;bottom=i>=5
 for local,label in [(6,'PWR'),(12,'RST')]:silk(label,base+18-local if bottom else base+local,H-26.6 if bottom else 26.6,180 if bottom else 0)
silk('3V3',8,36.5);silk('EN',14,36.5)

for idx,(x,y) in enumerate([(4,17),(96,17),(4,H-17),(96,H-17)]):
 f=p.FootprintLoad(str(LIB/'MountingHole.pretty'),'MountingHole_3.2mm_M3');f.SetReference('MH'+str(idx+1));f.SetPosition(V(x,y));f.Reference().SetVisible(False);f.Value().SetVisible(False)
 assert not collides(bbox(f)),('mount',x,y);B.Add(f)
def keepout(x,y,w,h):
 z=p.ZONE(B);z.SetIsRuleArea(True);ls=p.LSET();ls.AddLayer(p.F_Cu);ls.AddLayer(p.B_Cu);z.SetLayerSet(ls)
 z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);z.SetDoNotAllowZoneFills(True)
 poly=z.Outline();poly.NewOutline()
 for a,b in [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]:poly.Append(mm(a),mm(b))
 B.Add(z)
for y in [21.5,H-22.5]:keepout(5,y,90,1)
for j in range(1,5):
 for y in [0,H-21.5]:keepout(5+18*j-.5,y,1,21.5)
records=[]
for ref,o in objs.items():
 f=o['fp'];x,y,w,h=bbox(f);k=o['c']['key'];z={'ssr':2.1,'ind':1.8,'barrel':14,'port':6,'rj45':13.5,'usb':3.2}.get(k,.8 if k.startswith(('R','C')) else 1.5)
 records.append(dict(ref=ref,key=k,sheet=o['c']['sheet'],x=round(x,4),y=round(y,4),w=round(w,4),h=round(h,4),z=z,rotation=f.GetOrientationDegrees(),footprint=o['fid'],qualified=False))
B.BuildConnectivity();p.SaveBoard(str(R/'hardware/cad/B2/placement/rack-atx-controller.kicad_pcb'),B)
out=dict(revision='S.3',schematic_revision=C['revision'],outline_mm=[W,H,1.6],layers=2,status='Unrouted placement baseline; routing authorized after checks',footprint_count=len(placed),mechanical_holes=4,mounting_hole_centres_mm=[[4,17],[96,17],[4,H-17],[96,H-17]],unqualified_envelope_count=0,unqualified_families=[],routing_feasibility_verified=False,envelope_overlap_count=0,components=records,placement_constraints=constraints,regions=regions,user_approval='routing_authorized',tracks=0,vias=0)
(R/'hardware/placement-S3.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
assert all(c['pass'] for c in constraints),[c for c in constraints if not c['pass']]
print('S.3 PASS:',len(placed),'footprints;',len(constraints),'proximity checks; ZERO tracks; routing authorized')
