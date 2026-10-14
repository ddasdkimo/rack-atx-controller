#!/usr/bin/env python3
"""Conservative single-path copper resistance check; excludes component/return drops.
Uses 35 um copper at 60 C and 2 mOhm per 0.3 mm through via. No thermal signoff.
"""
import wx,sys,json,math,heapq,hashlib
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/sys.argv[1];b=p.LoadBoard(str(src));fps={f.GetReference():f for f in b.GetFootprints()}
def coord(v):return(v.x/1e6,v.y/1e6)
def key(q,l):return(l,round(q[0],4),round(q[1],4))
def pad(ref,pin):return next(d for d in fps[ref].Pads() if d.GetNumber()==pin)
def resistance(net,source,targets,current):
 ts=[t for t in b.GetTracks() if t.GetNetname()==net];ps=[d for f in b.GetFootprints() for d in f.Pads() if d.GetNetname()==net];nodes=set();edges={}
 def add(a,z,r,length=0,width=None):
  edges.setdefault(a,[]).append((z,r,length,width));edges.setdefault(z,[]).append((a,r,length,width))
 for t in ts:
  if isinstance(t,p.PCB_VIA):
   for l in [p.F_Cu,p.B_Cu]:nodes.add(key(coord(t.GetPosition()),l))
  else:
   for q in [t.GetStart(),t.GetEnd()]:nodes.add(key(coord(q),t.GetLayer()))
 for d in ps:
  for l in [p.F_Cu,p.B_Cu]:
   if d.IsOnLayer(l):nodes.add(key(coord(d.GetPosition()),l))
 for t in ts:
  if isinstance(t,p.PCB_VIA):add(key(coord(t.GetPosition()),p.F_Cu),key(coord(t.GetPosition()),p.B_Cu),.002);continue
  a,z=coord(t.GetStart()),coord(t.GetEnd());dx,dy=z[0]-a[0],z[1]-a[1];length=math.hypot(dx,dy);w=p.ToMM(t.GetWidth())
  if not length:continue
  on=[]
  for n in nodes:
   if n[0]!=t.GetLayer():continue
   ratio=((n[1]-a[0])*dx+(n[2]-a[1])*dy)/length**2
   if -.00001<=ratio<=1.00001 and math.hypot(n[1]-a[0]-ratio*dx,n[2]-a[1]-ratio*dy)<.0002:on.append((max(0,min(1,ratio)),n))
  on.sort()
  for (u,m),(v,n) in zip(on,on[1:]):
   ll=(v-u)*length;add(m,n,ll/w*(.00049257*(1+.00393*40)),ll,w)
 for d in ps:
  group=[]
  for n in nodes:
   if d.IsOnLayer(n[0]) and d.HitTest(p.VECTOR2I(p.FromMM(n[1]),p.FromMM(n[2]))):group.append(n)
  for n in group[1:]:add(group[0],n,0)
 start=key(coord(source.GetPosition()),p.F_Cu);dist={start:0};prev={};queue=[(0,start)]
 while queue:
  cost,a=heapq.heappop(queue)
  if cost!=dist.get(a):continue
  for z,r,length,w in edges.get(a,[]):
   nc=cost+r
   if nc<dist.get(z,1e100):dist[z]=nc;prev[z]=(a,length,w);heapq.heappush(queue,(nc,z))
 out=[]
 for ref,pin in targets:
  d=pad(ref,pin);end=key(coord(d.GetPosition()),p.F_Cu);r=dist.get(end);length=0;thin=0;cur=end
  while cur in prev:
   cur,ll,w=prev[cur];length+=ll
   if w and w<.4:thin+=ll
  out.append(dict(target=ref+'.'+pin,resistance_ohm=None if r is None else round(r,5),assumed_current_a=current,drop_v=None if r is None else round(r*current,4),path_mm=round(length,2),path_below_0_4mm_width_mm=round(thin,2)))
 return out
out=dict(board=src.name,pcb_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),copper_um=35,copper_temperature_c=60,via_resistance_ohm=.002,limits='Conservative one-path supply copper only; excludes regulator tolerance, connectors, fuse, MOSFET, ground return and transient response. No temperature-rise or field validation.',paths=[])
for net,source,targets,current in [('3V3',('L1','2'),[('U2',i) for i in ['2','3','20','46','55','56']],.65),('5V',('Q1','2'),[('U1','2')],.5),('5V_JACK',('J101','1'),[('F1','1')],1),('5V_FUSED',('F1','2'),[('Q1','3')],1)]:
 rows=resistance(net,pad(*source),targets,current)
 for row in rows:row.update(net=net,source='.'.join(source));print(row)
 out['paths'].extend(rows)
(R/(sys.argv[2] if len(sys.argv)>2 else 'artifacts/local/r1-power-path-audit.json')).write_text(json.dumps(out,indent=2)+'\n')
