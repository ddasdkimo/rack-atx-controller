#!/usr/bin/env python3
"""Conservative local two-layer repair trials; native DRC is mandatory.
Requires numpy. Does not route USB/Ethernet differential pairs.
"""
import json,math,heapq,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];d=json.loads((R/'artifacts/local/r1-route-work.json').read_text());routes=[];failed=[]
requested=[a for a in sys.argv[1:] if not a.startswith('--')];verbose=bool(requested)
critical=set('MCU_XN MCU_XP MCU_XP_CR ETH_XI ETH_XO USB_DP USB_DM USB_DP_MCU USB_DM_MCU ETH_TXP ETH_TXN ETH_RXP ETH_RXN RJ_RD_P RJ_RD_N BUCK_SW BUCK_BST'.split())
def domain(n):return n[:3] if n.startswith('H') and n[1:3].isdigit() and not n.endswith(('PLED_N','HDD_N')) else 'CTRL'
def dist(q,a,z):
 a=np.asarray(a);z=np.asarray(z);q=np.asarray(q);v=z-a;t=np.clip(np.sum((q-a)*v,axis=-1)/(np.sum(v*v)+1e-30),0,1);return np.linalg.norm(q-a-t[...,None]*v,axis=-1)
def solve(a,z,n,w):
 a=dict(a);z=dict(z)
 single_layer=n in {'ETH_TXP','ETH_TXN','ETH_RXP','ETH_RXN','RJ_RD_P','RJ_RD_N'}
 if single_layer:a['layers']=[0];z['layers']=[0]
 A=np.array(a['at']);Z=np.array(z['at']);aa=A.copy();zz=Z.copy()
 if verbose:print('solve',n,a,z,w,flush=True)
 for row,v in [(a,aa),(z,zz)]:
  if row.get('escape'):
   delta=v-np.array(row['fp']);axis=int(abs(delta[1])>abs(delta[0]));v[axis]+=(-1 if '--inward-escape' in sys.argv else 1)*math.copysign(.45 if '--short-escape' in sys.argv else .9,delta[axis])
 step=.05 if '--fine-grid' in sys.argv else .1;lo=np.floor((np.minimum(aa,zz)-12)/step)*step;hi=np.ceil((np.maximum(aa,zz)+12)/step)*step
 lo=np.maximum(lo,[.8,.8]);hi=np.minimum(hi,[199.2,169.2]);nx,ny=(np.round((hi-lo)/step).astype(int)+1);blocked=np.zeros((2,nx,ny),bool);vblock=np.zeros((nx,ny),bool)
 boxes=[];segs=[]
 def boxmark(arr,bb,margin):
  x0,y0,x1,y1=bb;x0=max(0,math.ceil((x0-margin-lo[0])/step));y0=max(0,math.ceil((y0-margin-lo[1])/step));x1=min(nx-1,math.floor((x1+margin-lo[0])/step));y1=min(ny-1,math.floor((y1+margin-lo[1])/step))
  if x1>=x0 and y1>=y0:
   xx,yy=np.meshgrid(lo[0]+np.arange(x0,x1+1)*step,lo[1]+np.arange(y0,y1+1)*step,indexing='ij');dx=np.maximum(np.maximum(bb[0]-xx,xx-bb[2]),0);dy=np.maximum(np.maximum(bb[1]-yy,yy-bb[3]),0);arr[x0:x1+1,y0:y1+1]|=(dx*dx+dy*dy)<margin*margin
 def segmark(arr,u,v,r):
  x0=max(0,math.ceil((min(u[0],v[0])-r-lo[0])/step));y0=max(0,math.ceil((min(u[1],v[1])-r-lo[1])/step));x1=min(nx-1,math.floor((max(u[0],v[0])+r-lo[0])/step));y1=min(ny-1,math.floor((max(u[1],v[1])+r-lo[1])/step))
  if x1<x0 or y1<y0:return
  xx,yy=np.meshgrid(lo[0]+np.arange(x0,x1+1)*step,lo[1]+np.arange(y0,y1+1)*step,indexing='ij');q=np.stack([xx,yy],axis=-1);arr[x0:x1+1,y0:y1+1]|=dist(q,u,v)<r
 for pad in d['pads']:
  if pad['net']!=n:
   gap=1.005 if pad['net'] and domain(pad['net'])!=domain(n) else (.155 if '--six-mil' in sys.argv else .205)
   for layer in pad['layers']:boxmark(blocked[layer],pad['box'],w/2+gap+.015);boxes.append((layer,pad['box'],w/2+gap))
   boxmark(vblock,pad['box'],.25+gap+.015)
  else:boxmark(vblock,pad['box'],.26)
  if pad['drill']:segmark(vblock,pad['at'],pad['at'],.15+pad['drill']/2+.451+.015)
 for t in d['tracks']:
  if t['net']==n:continue
  gap=1.005 if domain(t['net'])!=domain(n) else (.155 if '--six-mil' in sys.argv else .205)
  segmark(blocked[t['layer']],t['a'],t['b'],w/2+t['width']/2+gap+.015);segmark(vblock,t['a'],t['b'],.25+t['width']/2+gap+.015);segs.append((t['layer'],t['a'],t['b'],w/2+t['width']/2+gap))
 for v in d['vias']:
  if v['net']!=n:
   gap=1.005 if domain(v['net'])!=domain(n) else (.155 if '--six-mil' in sys.argv else .205)
   for layer in [0,1]:segmark(blocked[layer],v['at'],v['at'],w/2+v['diameter']/2+gap+.015);segs.append((layer,v['at'],v['at'],w/2+v['diameter']/2+gap))
   segmark(vblock,v['at'],v['at'],.25+v['diameter']/2+gap+.015)
  segmark(vblock,v['at'],v['at'],.15+v['drill']/2+.251+.015)
 for bb in d['keepouts']:
  for layer in [0,1]:boxmark(blocked[layer],bb,w/2+.025);boxes.append((layer,bb,w/2+.01))
  boxmark(vblock,bb,.275)
 if single_layer:blocked[1,:,:]=True
 # Exact short escape checks sampled at 0.01 mm, with guard above DRC clearance.
 def clear(u,v,l):
  q=np.linspace(u,v,max(2,int(np.linalg.norm(v-u)/.01)+2))
  for layer,bb,mar in boxes:
   if layer==l:
    dx=np.maximum(np.maximum(bb[0]-q[:,0],q[:,0]-bb[2]),0);dy=np.maximum(np.maximum(bb[1]-q[:,1],q[:,1]-bb[3]),0)
    if np.any(dx*dx+dy*dy<mar*mar):return False
  for layer,x,y,r in segs:
   if layer==l and np.any(dist(q,x,y)<r):return False
  return True
 if not clear(A,aa,a['layers'][0]) or not clear(zz,Z,z['layers'][0]):
  if verbose:print('escape blocked',a,z,flush=True)
  return None
 def entries(q,layers):
  out=[];ix,iy=np.round((q-lo)/step).astype(int)
  for x in range(max(0,ix-2),min(nx,ix+3)):
   for y in range(max(0,iy-2),min(ny,iy+3)):
    for l in layers:
     if not blocked[l,x,y] and clear(q,lo+np.array([x,y])*step,l):out.append((l,x,y))
  return out
 starts=entries(aa,a['layers']);goals=set(entries(zz,z['layers']))
 if not starts or not goals:
  if verbose:print('no grid access',len(starts),len(goals),a,z,flush=True)
  return None
 heuristic=1.6 if '--fast-search' in sys.argv else 1.0
 goalxy=(zz-lo)/step;cost={q:0. for q in starts};prev={q:None for q in starts};queue=[(heuristic*np.linalg.norm(np.array(q[1:])-goalxy),0.,q) for q in starts];heapq.heapify(queue);count=0
 while queue and count<(400000 if '--fast-search' in sys.argv else 2000000):
  _,g,q=heapq.heappop(queue)
  if g!=cost.get(q):continue
  count+=1
  if q in goals:
   seq=[]
   while q is not None:seq.append(q);q=prev[q]
   seq.reverse();pts=[(a['layers'][0],*A),(seq[0][0],*aa)]+[(l,*(lo+np.array([x,y])*step)) for l,x,y in seq]+[(seq[-1][0],*zz),(z['layers'][0],*Z)]
   out=[pts[0]]
   for i in range(1,len(pts)-1):
    u,v,e=pts[i-1:i+2]
    if u[0]!=v[0] or v[0]!=e[0] or abs((v[1]-u[1])*(e[2]-v[2])-(v[2]-u[2])*(e[1]-v[1]))>1e-8:out.append(v)
   out.append(pts[-1])
   if not all(u[0]!=v[0] or clear(np.array(u[1:]),np.array(v[1:]),u[0]) for u,v in zip(out,out[1:])):return None
   return out
  l,x,y=q
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
   xx,yy=x+dx,y+dy
   if not(0<=xx<nx and 0<=yy<ny) or blocked[l,xx,yy]:continue
   ng=g+math.hypot(dx,dy);nq=l,xx,yy
   if ng<cost.get(nq,1e30):cost[nq]=ng;prev[nq]=q;heapq.heappush(queue,(ng+heuristic*math.hypot(xx-goalxy[0],yy-goalxy[1]),ng,nq))
  nq=1-l,x,y
  if not vblock[x,y] and not blocked[1-l,x,y] and g+60<cost.get(nq,1e30):cost[nq]=g+60;prev[nq]=q;heapq.heappush(queue,(g+60+heuristic*math.hypot(x-goalxy[0],y-goalxy[1]),g+60,nq))
 if verbose:print('no path',count,'queue',len(queue),'starts',starts,'goals',goals,'grid',nx,ny,'layers',[sum(k[0]==l for k in cost) for l in [0,1]],'via nodes',int(np.sum(~vblock)),flush=True)
 if verbose:np.savez(R/'artifacts/local/router-mask.npz',blocked=blocked,vblock=vblock,lo=lo,visited=np.array(list(cost)))
 return None
for work in sorted(d['work'],key=lambda a:(a['net'] not in critical,not a['net'].endswith('GND'),a['net'])):
 n=work['net']
 if '--signals-only' in sys.argv and n in ['3V3','3V3_ETH_A','5V','PHOTO_5V']:continue
 if n in critical and '--all' not in sys.argv:continue
 if requested and n not in requested:continue
 groups=work['groups'];parent=list(range(len(groups)))
 def root(i):
  while parent[i]!=i:i=parent[i]
  return i
 pairs=[]
 for i in range(len(groups)):
  for j in range(i+1,len(groups)):
   A=np.array([x['at'] for x in groups[i]]);Z=np.array([x['at'] for x in groups[j]]);dd=np.sum((A[:,None,:]-Z[None,:,:])**2,axis=-1);selected=[]
   buckets={}
   for ind in np.argsort(dd,axis=None):
    ai,zi=np.unravel_index(int(ind),dd.shape)
    la=tuple(groups[i][ai]['layers']);lz=tuple(groups[j][zi]['layers']);key=(la,lz)
    bucket=buckets.setdefault(key,[])
    if len(bucket)>=3:continue
    if any(np.linalg.norm(A[ai]-A[u])<1 and np.linalg.norm(Z[zi]-Z[v])<1 for u,v in bucket):continue
    bucket.append((int(ai),int(zi)))
    if sum(len(v) for v in buckets.values())>=24:break
   for bucket in buckets.values():
    for ai,zi in bucket:pairs.append((dd[ai,zi]**.5,i,j,ai,zi))
 done=0
 for length,i,j,ai,zi in sorted(pairs):
  if root(i)==root(j) or length>120:continue
  a,z=groups[i][ai],groups[j][zi];w=.15 if any(x.get('escape') for x in [a,z]) or n in critical or n in ['3V3','3V3_ETH_A'] or n.endswith(('PLED_N','HDD_N')) else .25
  if '--fine-traces' in sys.argv and (n.endswith(('PLED_N','HDD_N')) or n in ['EN','BOOT_N','OUT_LATCH','OUT_OE_N','SPI_MOSI','SPI_MISO','SPI_SCK','SPI_SCK_RAW','SPI_MOSI_RAW','ETH_INT_N','ETH_CS_N','ETH_RST_N','TIMER_ARM','TIMER_FIRE','USB_VBUS_SENSE']):w=.125
  pts=solve(a,z,n,w)
  if not pts and w>.15 and n not in ['5V','PHOTO_5V']:
   w=.15;pts=solve(a,z,n,w)
  if not pts:continue
  plen=sum(math.dist(u[1:],v[1:]) for u,v in zip(pts,pts[1:]))
  if w==.15 and n in ['3V3','3V3_ETH_A'] and plen>12:continue
  vias=[]
  for u,v in zip(pts,pts[1:]):
   if u[0]!=v[0]:
    at=list(u[1:]);vias.append(at);d['vias'].append(dict(net=n,at=at,diameter=.5,drill=.3))
   elif math.dist(u[1:],v[1:])>1e-8:d['tracks'].append(dict(net=n,a=list(u[1:]),b=list(v[1:]),layer=u[0],width=w))
  routes.append(dict(net=n,width=w,points=pts,length=plen,vias=vias));parent[root(i)]=root(j);done+=1
 print(n,'connected',done,'of',len(groups)-1,flush=True)
 if done<len(groups)-1:failed.append(n)
 (R/'artifacts/local/r1-repair-routes.json').write_text(json.dumps(dict(routes=routes,deferred=failed),indent=2))
print('Added',len(routes),'branches; deferred',failed)
