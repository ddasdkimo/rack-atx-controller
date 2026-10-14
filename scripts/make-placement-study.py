#!/usr/bin/env python3
"""KiCad 10 spatial study, deliberately NOT a routed/fabrication board.
Run with KiCad's bundled Python (pcbnew module). Missing land patterns are
pad-free envelopes. Packing checks test space only, never routing/isolation.
"""
import json, os, math
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
C=json.loads((R/'hardware/circuit.json').read_text())
D=json.loads((R/'hardware/design.json').read_text())
assert D['controller_outline_mm']==[160,110,1.6], 'Redesign packing regions for changed outline before regeneration'
LIB=Path(os.environ.get('KICAD_FOOTPRINT_DIR','/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'))
B=p.BOARD(); B.SetCopperLayerCount(2)
B.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
# Conservative spatial envelopes including estimated land-pattern allowance.
# No copper pads are invented for the five unqualified families.
ENV={'ssr':(8.5,5.5,2.5),'opto':(7.5,5.5,2.5),'iso':(12.6,7,10.1),'ind':(5,5,1.8),'barrel':(11.2,10.2,13)}
mm=lambda x:p.FromMM(x)
vec=lambda x,y:p.VECTOR2I(mm(x),mm(y))
def line(parent,x1,y1,x2,y2,layer,width=.12):
 s=p.PCB_SHAPE(parent);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(vec(x1,y1));s.SetEnd(vec(x2,y2));s.SetLayer(layer);s.SetWidth(mm(width));parent.Add(s)
def rect(parent,x,y,w,h,layer):
 for a,b,c,d in [(x,y,x+w,y),(x+w,y,x+w,y+h),(x+w,y+h,x,y+h),(x,y+h,x,y)]:line(parent,a,b,c,d,layer)
def text(t,x,y,size=1,layer=p.Dwgs_User):
 o=p.PCB_TEXT(B);o.SetText(t);o.SetPosition(vec(x,y));o.SetTextSize(vec(size,size));o.SetTextThickness(mm(.15));o.SetLayer(layer);B.Add(o)
netnames=sorted({n for c in C['components'] if c['sheet']!='adapter' for n in c['nets'].values() if n})
nets={}
for name in netnames:
 n=p.NETINFO_ITEM(B,name);B.Add(n);nets[name]=n
comps=[c for c in C['components'] if c['sheet']!='adapter' and c['key']!='flag']
objects={};records=[]
for c in comps:
 k=c['key'];spec=C['parts'][k];fid=spec['footprint']
 if fid:
  lib,name=fid.split(':');f=p.FootprintLoad(str(LIB/(lib+'.pretty')),name)
  if f is None:raise RuntimeError(fid)
 else:
  f=p.FOOTPRINT(B);w,h,_=ENV[k];rect(f,-w/2,-h/2,w,h,p.F_CrtYd);rect(f,-w/2+.4,-h/2+.4,w-.8,h-.8,p.F_Fab)
  line(f,-w/2,-h/2,w/2,h/2,p.F_Fab);line(f,-w/2,h/2,w/2,-h/2,p.F_Fab)
  f.SetFPID(p.LIB_ID('Study','UNQUALIFIED_'+k))
 f.SetReference(c['ref']);f.SetValue(spec['value']+(' [ENVELOPE ONLY]' if not fid else ''))
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 f.SetPosition(vec(0,0));f.SetOrientationDegrees(180 if k=='port' else 0)
 for pad in f.Pads():
  name=c['nets'].get(pad.GetNumber())
  if name:pad.SetNet(nets[name])
 B.Add(f);bb=f.GetBoundingBox(False,False)
 objects[c['ref']]={'c':c,'fp':f,'w':p.ToMM(bb.GetWidth()),'h':p.ToMM(bb.GetHeight()),'fid':fid}

def place(obj,x,y,rot=0):
 f=obj['fp'];f.SetOrientationDegrees((180 if obj['c']['key']=='port' else 0)+rot)
 bb=f.GetBoundingBox(False,False);f.Move(vec(x-p.ToMM(bb.GetX()),y-p.ToMM(bb.GetY())))
 bb=f.GetBoundingBox(False,False);k=obj['c']['key'];w=p.ToMM(bb.GetWidth());h=p.ToMM(bb.GetHeight())
 z=ENV[k][2] if k in ENV else {'port':6,'rj45':13.5,'usb':3.2,'ldo':1.8}.get(k, .6 if k.startswith(('R','C')) else 1.5)
 records.append({'ref':obj['c']['ref'],'key':k,'sheet':obj['c']['sheet'],'x':round(x,4),'y':round(y,4),'w':round(w,4),'h':round(h,4),'z':z,'rotation':(180 if k=='port' else 0)+rot,'footprint':obj['fid'] or 'UNQUALIFIED_ENVELOPE','qualified':False})
 return (x,y,w,h)

def pack(items,x,y,w,h):
 # Bottom-left grid search with 0.4 mm spacing beyond bounding boxes/courtyards.
 occupied=[]
 for obj in sorted(items,key=lambda o:-(o['w']*o['h'])):
  choices=[]
  for rot in [0,90]:
   ow,oh=(obj['w'],obj['h']) if rot==0 else (obj['h'],obj['w'])
   xs=sorted({x}|{round(a+c+.4,5) for a,b,c,d in occupied})
   ys=sorted({y}|{round(b+d+.4,5) for a,b,c,d in occupied})
   for yy in ys:
    for xx in xs:
     if xx+ow>x+w+.00001 or yy+oh>y+h+.00001:continue
     if any(xx<a+c+.399 and xx+ow+.399>a and yy<b+d+.399 and yy+oh+.399>b for a,b,c,d in occupied):continue
     choices.append((yy+oh,xx,yy,rot))
  if not choices:raise RuntimeError('No space: '+obj['c']['ref']+' in '+str((x,y,w,h)))
  _,xx,yy,rot=min(choices);occupied.append(place(obj,xx,yy,rot))
 return max(b+d for a,b,c,d in occupied)

rect(B,0,0,160,110,p.Edge_Cuts)
for i in range(10):
 x=5+i*15;channel=f'host{i+1:02}'
 its=[o for o in objects.values() if o['c']['sheet'].startswith(channel)]
 port=next(o for o in its if o['c']['key']=='port');place(port,x+(14-port['w'])/2,1)
 # 14 mm width + 1 mm inter-channel gap, not an approved isolation spacing.
 ymax=pack([o for o in its if o!=port],x,14,14,62)
 rect(B,x-.2,.7,14.4,76,p.Dwgs_User);text(f'H{i+1:02}',x+7,78,1)
 print(channel,len(its),'end y',round(ymax,2))
# Shared domain: physically separated functional blocks, routing still pending.
groups=[('ethernet',5,81,46,27),('processor',54,81,42,27),('outputs',99,81,36,27),('power',138,81,18,27)]
for prefix,x,y,w,h in groups:
 its=[o for o in objects.values() if o['c']['sheet'].startswith(prefix)]
 pack(its,x,y,w,h);text(prefix,x+w/2,112,1.2)
text('S.1 SPACE STUDY / 160 x 110 mm / 2 layers / NOT FOR FABRICATION',80,-5,1.6)
text('694 components. Crossed boxes = 5 unqualified footprint families. No routing / ground planes / mounting holes.',80,117,1)
# Mechanical envelope overlap / outline test, no claim of DRC or isolation clearance.
assert len(records)==694
for a in records:
 assert a['x']>=0 and a['y']>=0 and a['x']+a['w']<=160 and a['y']+a['h']<=110,a
for i,a in enumerate(records):
 for b in records[i+1:]:
  assert not (a['x']<b['x']+b['w']-.001 and a['x']+a['w']>b['x']+.001 and a['y']<b['y']+b['h']-.001 and a['y']+a['h']>b['y']+.001),(a['ref'],b['ref'])
B.BuildConnectivity()
p.SaveBoard(str(R/'hardware/cad/compact-S1-placement.kicad_pcb'),B)
out={'revision':'S.1','schematic_revision':C['revision'],'outline_mm':[160,110,1.6],'layers':2,'status':'Spatial packing study only; no routed traces, planes, mounting holes, DRC or production approval','footprint_count':len(records),'unqualified_envelope_count':sum(not o['fid'] for o in objects.values()),'unqualified_families':list(ENV),'routing_feasibility_verified':False,'envelope_overlap_count':0,'components':records}
(R/'hardware/placement-study.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('PASS: 694 candidate/envelope placements inside outline with no bounding-box overlap. NOT DRC.')
