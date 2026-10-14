#!/usr/bin/env python3
"""Short, top-layer-only buck/crystal route trial, checked in native DRC.
No USB or Ethernet differential routing is implied by this routine.
"""
import math,json,heapq,sys
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
path=R/('artifacts/local/R1-general.kicad_pcb' if len(sys.argv)==1 else sys.argv[1])
b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()}
text=(R/'scripts/start-local-routing.py').read_text();exec(text[text.index('def xy('):text.index('keepouts=[]')])
keepouts=[box(z) for z in b.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowTracks()]
tracks=[(xy(t),(p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)),t.GetNetname(),p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())) for t in b.GetTracks() if t.IsOnLayer(p.F_Cu)]
routes=[];deferred=[]
def solve(a,z,net,width):
 step=.1;padobs=[bb for _,_,n,bb in pads if n!=net]
 tr=[(u,v,w) for u,v,n,w in tracks if n!=net]
 def clear(a,z,extra=0):
  return not any(hits(a,z,q,width/2+.205+extra) for q in padobs) and not any(hits(a,z,q,width/2+.02+extra) for q in keepouts) and not any(segdist(a,z,u,v)<width/2+w/2+.205+extra for u,v,w in tr)
 # Try direct 45-degree escape first.
 dx=z[0]-a[0];dy=z[1]-a[1];m=min(abs(dx),abs(dy));sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
 for pts in [[a,(a[0]+sx*m,a[1]+sy*m),z],[a,(z[0]-sx*m,z[1]-sy*m),z]]:
  if all(clear(u,v) for u,v in zip(pts,pts[1:])):return pts
 x0=math.floor((min(a[0],z[0])-3)/step);x1=math.ceil((max(a[0],z[0])+3)/step);y0=math.floor((min(a[1],z[1])-3)/step);y1=math.ceil((max(a[1],z[1])+3)/step)
 # Conservative raster masks, including additional half-cell guard.
 blocked=set();margin=width/2+.28
 for bb in padobs+keepouts:
  l,t,r,bt=bb
  for x in range(max(x0,math.ceil((l-margin)/step)),min(x1,math.floor((r+margin)/step))+1):
   for y in range(max(y0,math.ceil((t-margin)/step)),min(y1,math.floor((bt+margin)/step))+1):blocked.add((x,y))
 for u,v,w in tr:
  mar=width/2+w/2+.28
  lx=max(x0,math.ceil((min(u[0],v[0])-mar)/step));rx=min(x1,math.floor((max(u[0],v[0])+mar)/step));ty=max(y0,math.ceil((min(u[1],v[1])-mar)/step));by=min(y1,math.floor((max(u[1],v[1])+mar)/step))
  for x in range(lx,rx+1):
   for y in range(ty,by+1):
    if point_seg((x*step,y*step),u,v)<mar:blocked.add((x,y))
 starts=[];goals=set()
 for q,out in [(a,starts),(z,goals)]:
  for x in range(round(q[0]/step)-2,round(q[0]/step)+3):
   for y in range(round(q[1]/step)-2,round(q[1]/step)+3):
    if (x,y) not in blocked and clear(q,(x*step,y*step)):
     if isinstance(out,set):out.add((x,y))
     else:out.append((x,y))
 if not starts or not goals:return None
 cost={q:math.dist(a,(q[0]*step,q[1]*step))/step for q in starts};prev={q:None for q in starts};queue=[(g+math.hypot(q[0]-z[0]/step,q[1]-z[1]/step),q) for q,g in cost.items()];heapq.heapify(queue)
 while queue:
  _,q=heapq.heappop(queue)
  if q in goals:
   seq=[]
   while q is not None:seq.append((q[0]*step,q[1]*step));q=prev[q]
   pts=[a]+seq[::-1]+[z];simple=[pts[0]]
   for i in range(1,len(pts)-1):
    u,v,w=pts[i-1],pts[i],pts[i+1]
    if abs((v[0]-u[0])*(w[1]-v[1])-(v[1]-u[1])*(w[0]-v[0]))>1e-7:simple.append(v)
   simple.append(z)
   if all(clear(u,v) for u,v in zip(simple,simple[1:])):return simple
   return None
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
   v=q[0]+dx,q[1]+dy
   if not (x0<=v[0]<=x1 and y0<=v[1]<=y1) or v in blocked:continue
   g=cost[q]+math.hypot(dx,dy)
   if g<cost.get(v,1e10):cost[v]=g;prev[v]=q;heapq.heappush(queue,(g+math.hypot(v[0]-z[0]/step,v[1]-z[1]/step),v))
 return None
for net in ['BUCK_SW','BUCK_BST','MCU_XN','MCU_XP','MCU_XP_CR','ETH_XI','ETH_XO']:
 entries=by_net[net];parent=list(range(len(entries)))
 def root(i):
  while parent[i]!=i:i=parent[i]
  return i
 for _,i,j in sorted((math.dist(xy(a),xy(z)),i,j) for i,(_,a) in enumerate(entries) for j,(_,z) in enumerate(entries) if j>i):
  if root(i)==root(j):continue
  ra,da=entries[i];rb,db=entries[j];width=.6 if net=='BUCK_SW' else .25 if net=='BUCK_BST' else .15
  pa,pb=xy(da),xy(db)
  def escape(ref,pt):
   if ref not in ['U2','U3']:return pt
   cx,cy=xy(fps[ref]);dx,dy=pt[0]-cx,pt[1]-cy
   return (pt[0]+(1 if dx>0 else -1)*1.0,pt[1]) if abs(dx)>abs(dy) else (pt[0],pt[1]+(1 if dy>0 else -1)*1.0)
  ea,eb=escape(ra,pa),escape(rb,pb)
  def escape_clear(u,v):
   return all(not hits(u,v,bb,width/2+.205) for _,_,n,bb in pads if n!=net) and all(n==net or segdist(u,v,a,z)>=width/2+w/2+.205 for a,z,n,w in tracks)
  pts=solve(ea,eb,net,width) if escape_clear(pa,ea) and escape_clear(eb,pb) else None
  if pts:pts=[pa]+pts+[pb]
  if not pts:deferred.append([net,ra+'.'+da.GetNumber(),rb+'.'+db.GetNumber()]);continue
  length=sum(math.dist(u,v) for u,v in zip(pts,pts[1:]))
  if length>15:deferred.append([net,ra,rb,'detour exceeds 15 mm']);continue
  for u,v in zip(pts,pts[1:]):
   if math.dist(u,v)<1e-6:continue
   t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*[p.FromMM(k) for k in u]));t.SetEnd(p.VECTOR2I(*[p.FromMM(k) for k in v]));t.SetWidth(p.FromMM(width));t.SetLayer(p.F_Cu);t.SetNetCode(da.GetNetCode());b.Add(t);tracks.append((u,v,net,width))
  parent[root(i)]=root(j);routes.append(dict(net=net,a=ra+'.'+da.GetNumber(),b=rb+'.'+db.GetNumber(),points=pts,length_mm=length));print(net,ra,rb,round(length,2),flush=True)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(R/'artifacts/local/R1-critical.kicad_pcb'),b)
(R/'artifacts/local/r1-critical.json').write_text(json.dumps(dict(routes=routes,deferred=deferred),indent=2));print('Deferred',deferred)
