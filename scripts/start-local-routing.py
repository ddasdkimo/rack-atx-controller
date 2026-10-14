#!/usr/bin/env python3
"""R.0: conservative first pass of short local F.Cu routes, not an autorouted release.
Keep S.2 placement immutable. Skip anything needing vias, dense escape or a detour.
"""
import json,math,shutil,hashlib
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/'hardware/cad/layout-S2-review.kicad_pcb';dst=R/'hardware/cad/routing-R0.kicad_pcb'
b=p.LoadBoard(str(src));assert len(b.GetTracks())==0
fps={f.GetReference():f for f in b.GetFootprints()}
components=json.loads((R/'hardware/circuit.json').read_text())['components'];info={c['ref']:c for c in components}
def xy(d):v=d.GetPosition();return (p.ToMM(v.x),p.ToMM(v.y))
def domain(n):return n[:3] if n.startswith('H') and n[1:3].isdigit() and n[3:4]=='_' and not n.endswith(('PLED_N','HDD_N')) else 'CTRL'
def box(d):
 q=d.GetBoundingBox();return tuple(p.ToMM(v) for v in (q.GetX(),q.GetY(),q.GetRight(),q.GetBottom()))
pads=[(f.GetReference(),d,d.GetNetname(),box(d)) for f in fps.values() for d in f.Pads() if d.IsOnLayer(p.F_Cu)]
by_net={}
for ref,d,n,bb in pads:
 if n:by_net.setdefault(n,[]).append((ref,d))
def hits(a,z,q,margin):
 # Liang-Barsky segment versus expanded axis-aligned pad/keepout rectangle.
 x0,y0,x1,y1=q;x0-=margin;y0-=margin;x1+=margin;y1+=margin
 dx=z[0]-a[0];dy=z[1]-a[1];lo,hi=0.,1.
 for pp,qq in [(-dx,a[0]-x0),(dx,x1-a[0]),(-dy,a[1]-y0),(dy,y1-a[1])]:
  if abs(pp)<1e-12:
   if qq<0:return False
  else:
   t=qq/pp
   if pp<0:lo=max(lo,t)
   else:hi=min(hi,t)
   if lo>hi:return False
 return True
def point_seg(a,u,v):
 dx=v[0]-u[0];dy=v[1]-u[1];s=dx*dx+dy*dy
 t=max(0,min(1,((a[0]-u[0])*dx+(a[1]-u[1])*dy)/s)) if s else 0
 return math.dist(a,(u[0]+t*dx,u[1]+t*dy))
def segdist(a,z,u,v):
 cross=lambda x,y:x[0]*y[1]-x[1]*y[0]
 d=(z[0]-a[0],z[1]-a[1]);e=(v[0]-u[0],v[1]-u[1]);w=(u[0]-a[0],u[1]-a[1]);den=cross(d,e)
 if abs(den)>1e-12:
  t=cross(w,e)/den;s=cross(w,d)/den
  if 0<=t<=1 and 0<=s<=1:return 0
 return min(point_seg(a,u,v),point_seg(z,u,v),point_seg(u,a,z),point_seg(v,a,z))
keepouts=[]
for z in b.Zones():
 if z.GetIsRuleArea():keepouts.append(box(z))
routes=[];segments=[];attempts=[]
def try_pair(ra,da,rb,db,kind):
 net=da.GetNetname();assert net and net==db.GetNetname()
 a,z=xy(da),xy(db);dx=z[0]-a[0];dy=z[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1;m=min(abs(dx),abs(dy));width=.25
 choices=[[a,(a[0]+sx*m,a[1]+sy*m),z],[a,(z[0]-sx*m,z[1]-sy*m),z],[a,(z[0],a[1]),z],[a,(a[0],z[1]),z]]
 for points in choices:
  points=[q for i,q in enumerate(points) if i==0 or math.dist(q,points[i-1])>1e-6]
  ss=list(zip(points,points[1:]));clear=True
  for start,end in ss:
   if any(hits(start,end,k,width/2+.01) for k in keepouts):clear=False;break
   for rr,d,n,bb in pads:
    if n==net:continue
    clearance=1.01 if n and domain(n)!=domain(net) else .21
    if hits(start,end,bb,width/2+clearance):clear=False;break
   if not clear:break
   if any(n!=net and segdist(start,end,u,v)<width/2+w/2+(1.01 if domain(n)!=domain(net) else .21) for u,v,n,w in segments):clear=False;break
  if not clear:continue
  for start,end in ss:
   t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(start[0]),p.FromMM(start[1])));t.SetEnd(p.VECTOR2I(p.FromMM(end[0]),p.FromMM(end[1])));t.SetWidth(p.FromMM(width));t.SetLayer(p.F_Cu);t.SetNetCode(da.GetNetCode());b.Add(t);segments.append((start,end,net,width))
  routes.append(dict(a=ra+'.'+da.GetNumber(),b=rb+'.'+db.GetNumber(),net=net,kind=kind,points=points,width_mm=width,length_mm=round(sum(math.dist(u,v) for u,v in ss),4)))
  return True
 attempts.append(dict(a=ra+'.'+da.GetNumber(),b=rb+'.'+db.GetNumber(),net=net,reason='No clear short path on F.Cu; deferred, not force-routed'));return False
# First place comparator supply branches before analog two-pin nets.
for i in range(1,11):
 parts=[c for c in components if c['sheet'].startswith(f'host{i:02}')]
 cmp=next(c['ref'] for c in parts if c['key']=='cmp');cap=next(c['ref'] for c in parts if c['key']=='C100n')
 get=lambda r,n:next(d for d in fps[r].Pads() if d.GetNumber()==str(n))
 try_pair(cap,get(cap,1),cmp,get(cmp,8),'comparator local decoupling supply')
# Local branch/signal nets only; do not route USB, Ethernet, clocks or shared power here.
for net,entries in sorted(by_net.items()):
 if not 2<=len(entries)<=8 or not (net.startswith('H') and net[1:3].isdigit() or net.startswith('CTRL_H')):continue
 # Connect a minimum-distance forest, retaining deferred branches for manual routing.
 parent=list(range(len(entries)))
 def root(i):
  while parent[i]!=i:i=parent[i]
  return i
 work=[]
 for i,(ra,a) in enumerate(entries):
  for j,(rb,z) in enumerate(entries[i+1:],i+1):
   dist=math.dist(xy(a),xy(z))
   if ra!=rb and dist<=6:work.append((dist,i,j,ra,a,rb,z))
 for _,i,j,ra,a,rb,z in sorted(work,key=lambda x:x[0]):
  if root(i)==root(j):continue
  if try_pair(ra,a,rb,z,'short host-local signal'):parent[root(i)]=root(j)
b.BuildConnectivity();p.SaveBoard(str(dst),b)
shutil.copyfile(src.with_suffix('.kicad_pro'),dst.with_suffix('.kicad_pro'))
report=dict(revision='R.0',source_placement='S.2',source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),pcb_sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),status='partial_local_routing',track_segments=len(b.GetTracks()),vias=0,routed_pairs=len(routes),routes=routes,deferred=attempts,manufacturing_ready=False,remaining=['Main power and isolated ground pours','MCU escape, crystal, USB and Ethernet routing','Remaining host-local nets and interconnect','Return-path/impedance/thermal review and final DRC/connectivity'])
(R/'hardware/routing-R0.json').write_text(json.dumps(report,indent=2)+'\n')
print('R.0:',len(routes),'local pairs;',len(b.GetTracks()),'track segments;',len(attempts),'deferred paths; NOT complete')
