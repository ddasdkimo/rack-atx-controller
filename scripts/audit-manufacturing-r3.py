#!/usr/bin/env python3
"""Independent Gerbonara CAM parse plus native drill/CPL comparison. No factory DFM claim."""
import argparse,csv,hashlib,json,math,warnings
from pathlib import Path
from gerbonara import LayerStack,GerberFile,ExcellonFile
from gerbonara.utils import MM
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--package',type=Path,required=True);ap.add_argument('--native-reference',type=Path,required=True);a=ap.parse_args()
r=a.package;native=json.loads(a.native_reference.read_text());manifest=json.loads((r/'manifest.json').read_text());reports={}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,prefix,w,h in [('controller','rack-atx-controller',100,110),('adapter','adapter',26,34)]:
 d=r/name;ref=native[name]
 assert ref['pcb_sha256']==manifest['boards'][name]['native_pcb_sha256']
 for rel,digest in manifest['boards'][name]['files'].items():assert sha(r/rel)==digest,(rel,'hash mismatch')
 with warnings.catch_warnings(record=True) as warn:
  warnings.simplefilter('always');stack=LayerStack.open(d)
  layers={p.name:GerberFile.open(p) for p in d.iterdir() if p.suffix in {'.gtl','.gbl','.gts','.gbs','.gto','.gbo','.gtp','.gm1'}}
  drills={p.name:ExcellonFile.open(p) for p in d.glob('*.drl')}
 outline=layers[prefix+'-Edge_Cuts.gm1'];endpoints=set()
 for o in outline.objects:
  assert type(o).__name__=='Line';endpoints.add((o.x1,o.y1));endpoints.add((o.x2,o.y2))
 assert endpoints=={(0.,0.),(w,0.),(0.,-h),(w,-h)} and len(outline.objects)==4
 for side in ['top','bottom']:(r/f'{name}-cam-{side}.svg').write_text(str(stack.to_pretty_svg(side=side,margin=1)))
 rounds=[];slots=[];counts={}
 for f,drill in drills.items():
  pl='NPTH' if 'NPTH' in f else 'PTH'
  for o in drill.objects:
   (x0,y0),(x1,y1)=o.bounding_box(MM);assert x0>=0 and x1<=w and y0>=-h and y1<=0
   key=f'{pl}/{o.aperture.diameter:.3f}mm/{type(o).__name__}';counts[key]=counts.get(key,0)+1
   if type(o).__name__=='Flash':rounds.append([o.x,o.y,o.aperture.diameter,pl])
   elif type(o).__name__=='Line':slots.append({'ends':[[o.x1,o.y1],[o.x2,o.y2]],'diameter_mm':o.aperture.diameter,'plating':pl})
   else:raise AssertionError(('Unexpected drill object',type(o).__name__))
 maxerror=0
 for x,y,diam,pl in ref['round_drills']:
  candidates=[(math.hypot(x-q[0],y-q[1]),i) for i,q in enumerate(rounds) if abs(q[2]-diam)<1e-6 and q[3]==pl]
  error,i=min(candidates);assert error<=.00071;maxerror=max(maxerror,error);rounds.pop(i)
 assert not rounds
 for slot in ref['slots']:
  def err(q):
   if abs(q['diameter_mm']-slot['diameter_mm'])>1e-6 or q['plating']!=slot['plating']:return float('inf')
   return min(max(math.dist(u,v) for u,v in zip(slot['ends'],order)) for order in (q['ends'],list(reversed(q['ends']))))
  error,i=min((err(q),i) for i,q in enumerate(slots));assert error<=.00071,(name,slot,error);maxerror=max(maxerror,error);slots.pop(i)
 assert not slots
 cpl=list(csv.DictReader((d/f'{name}-cpl.csv').open()));bom=list(csv.DictReader((d/f'{name}-bom.csv').open()));refs={v.strip() for row in bom for v in row['Designator'].split(',')}
 assert len(cpl)==len(refs)==manifest['boards'][name]['parts'] and {v['Designator'] for v in cpl}==refs
 for row in cpl:
  q=ref['components'][row['Designator']]
  assert abs(float(row['Mid X'].removesuffix('mm'))-q['x_mm'])<.0000011
  assert abs(float(row['Mid Y'].removesuffix('mm'))-q['y_mm'])<.0000011
  assert abs(float(row['Rotation'])-q['rotation'])<.0000011 and row['Layer']==q['side']=='Top'
 reports[name]={'pcb_sha256':ref['pcb_sha256'],'outline_mm':[w,h],'outline_closed':True,'native_round_drills':len(ref['round_drills']),'native_slots':len(ref['slots']),'drill_coordinate_max_rounding_mm':round(maxerror,8),'drill_geometry_matches_native':True,'cpl_matches_native':True,'bom_cpl_references':len(refs),'parsed_layer_objects':{k:len(v.objects) for k,v in layers.items()},'drill_counts':counts,'parser_warnings':sorted(set(str(x.message).split(': ',1)[-1] for x in warn))}
report={'status':'pass independent file geometry and coordinate parity; factory acceptance pending','parser':'Gerbonara','boards':reports,'limitations':['CPL rotations are native KiCad angles, not verified factory library rotations.','Parser G90/header and rounded macro warnings did not prevent geometry parsing; absent bottom paste is intentional for single-side assembly.','No solderability, process capability, physical fit or functional qualification implied.']}
(r/'cam-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
