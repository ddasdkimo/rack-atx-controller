#!/usr/bin/env python3
"""Export actual R.3 native copper (both layers, vias and filled plane polygons)."""
import json,hashlib,html,collections,math
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];path=R/'hardware/cad/B2/rack-atx-controller.kicad_pcb';b=p.LoadBoard(str(path));baseline=p.LoadBoard(str(R/'hardware/cad/B2/placement/rack-atx-controller.kicad_pcb'))
d=json.loads((R/'hardware/design.json').read_text());components={x['ref']:x for x in json.loads((R/'hardware/circuit.json').read_text())['components'] if x['sheet']!='adapter' and x['key']!='flag'}
fps={f.GetReference():f for f in b.GetFootprints()};old={f.GetReference():f for f in baseline.GetFootprints()}
def xy(q):v=q.GetPosition();return [p.ToMM(v.x),p.ToMM(v.y)]
def pos(v):return [round(p.ToMM(v.x),4),round(p.ToMM(v.y),4)]
def domain(n):return n[:3] if n.startswith('H') and n[1:3].isdigit() and n[3:4]=='_' and not n.endswith(('PLED_N','HDD_N')) else 'CTRL'
changes=[]
for ref,c in components.items():
 f=fps[ref]
 for pin,net in c['nets'].items():
  if net:assert any(x.GetNumber()==pin and x.GetNetname()==net for x in f.Pads()),(ref,pin,net)
 if xy(f)!=xy(old[ref]) or f.GetOrientationDegrees()!=old[ref].GetOrientationDegrees() or (str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()))!=(str(old[ref].GetFPID().GetLibNickname())+':'+str(old[ref].GetFPID().GetLibItemName())):changes.append(dict(ref=ref,old_position_mm=xy(old[ref]),position_mm=xy(f),rotation_deg=f.GetOrientationDegrees()))
assert set(x['ref'] for x in changes)<={'U2','C21','C22','C23','R18','R19','R20','R21','C33','C34','C35','R8','R9','R10','R11','R14','R25','R26'},changes
segments=[];vias=[]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):vias.append(dict(at=xy(t),diameter_mm=p.ToMM(t.GetWidth(p.F_Cu)),drill_mm=p.ToMM(t.GetDrill()),net=t.GetNetname()));continue
 assert isinstance(t,p.PCB_TRACK)
 segments.append(dict(a=pos(t.GetStart()),b=pos(t.GetEnd()),layer=b.GetLayerName(t.GetLayer()),net=t.GetNetname(),width_mm=p.ToMM(t.GetWidth())))
zones=[]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 polygons=z.GetFilledPolysList(z.GetLayer());out=[]
 for i in range(polygons.OutlineCount()):
  chain=polygons.COutline(i);outer=[pos(chain.CPoint(k)) for k in range(chain.PointCount())];holes=[]
  for j in range(polygons.HoleCount(i)):
   chain=polygons.CHole(i,j);holes.append([pos(chain.CPoint(k)) for k in range(chain.PointCount())])
  out.append(dict(outer=outer,holes=holes))
 zones.append(dict(net=z.GetNetname(),layer=b.GetLayerName(z.GetLayer()),polygons=out))
b.BuildConnectivity();unrouted=b.GetConnectivity().GetUnconnectedCount(False)
validation=json.loads((R/'hardware/validation/routing-R3-checks.json').read_text());assert validation['controller']['pcb_sha256']==hashlib.sha256(path.read_bytes()).hexdigest() and validation['controller']['native_unrouted']==unrouted==0
drc=json.loads((R/'artifacts/local/b2-controller-final-drc.json').read_text());assert not drc['violations'],collections.Counter(x['type'] for x in drc['violations'])
report=dict(revision='R.3',status='partial_routing' if unrouted else 'connected_candidate',pcb_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),track_segments=len(segments),vias=len(vias),ground_zones=len({z['net'] for z in zones}),zone_objects=len(zones),native_unrouted=unrouted,total_track_length_mm=round(sum(math.dist(s['a'],s['b']) for s in segments),3),placement_changes=changes,net_pin_mapping='All connected B.2 schematic pins mapped to matching nets',segments=segments,via_geometry=vias,filled_zones=zones,drc=dict(violations=0,unconnected_items_reported=len(drc['unconnected_items']),full_schematic_parity=False,note='Native connectivity is reported separately. DRC report item cap is not a completion percentage.'),manufacturing_ready=False,remaining=['Factory stack-up/DFM acceptance and physical USB/Ethernet tests','Assembled power/ground transient and thermal measurements','Assembly DFM and prototype verification'])
d['routing_study']=report;d['layout_study']=json.loads((R/'hardware/placement-S3.json').read_text());d['stage']='routed-prototype-candidate';d['outline_status']='R.3 native 100 x 110 mm two-layer routed candidate; not a manufacturing release'
# Keep the immutable placement report, apply explicitly audited overrides to the renderer.
updated=[]
for c in d['layout_study']['components']:
 c=dict(c)
 if c['ref'] in {x['ref'] for x in changes}:
  f=fps[c['ref']];bb=f.GetBoundingBox(False,False)
  c.update(x=p.ToMM(bb.GetX()),y=p.ToMM(bb.GetY()),w=p.ToMM(bb.GetWidth()),h=p.ToMM(bb.GetHeight()),rotation=f.GetOrientationDegrees(),footprint=(str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())),key=components[c['ref']]['key'])
 updated.append(c)
d['routing_study']['component_overrides']=[c for c in updated if c['ref'] in {x['ref'] for x in changes}]
(R/'hardware/routing-R3.json').write_text(json.dumps(report,indent=2)+'\n')
(R/'hardware/design.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
# Exact pad/track/filled-plane drawing. All geometry is presentation-only;
# native KiCad remains the manufacturing source when eventually qualified.
colors={'CTRL':'#73bba1',**{f'H{n:02}':('#eeb868' if n%2 else '#8fbce5') for n in range(1,11)}}
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -8 104 126"><style>text{font-family:monospace}.ref{font-size:1.15px;fill:#e7f5ee}</style><rect x="-2" y="-8" width="104" height="126" fill="#10241e"/><rect width="100" height="110" fill="#153c32" stroke="#5b9b7e" stroke-width=".3"/>',f'<text x="1" y="-3" fill="#eee" font-size="1.8">R.3 / 100 x 110 mm / {unrouted} UNROUTED / NOT FOR FABRICATION</text>','<g id="copper-planes" fill="#426db8" opacity=".35" fill-rule="evenodd">']
for z in zones:
 for poly in z['polygons']:
  paths=' '.join('M'+' L'.join(f'{x},{y}' for x,y in loop)+' Z' for loop in [poly['outer']]+poly['holes'])
  svg.append(f'<path d="{paths}"><title>{z["net"]} / actual filled {z["layer"]}</title></path>')
svg.append('</g>')
for z in b.Zones():
 if z.GetIsRuleArea():
  bb=z.GetBoundingBox();svg.append(f'<rect x="{p.ToMM(bb.GetX())}" y="{p.ToMM(bb.GetY())}" width="{p.ToMM(bb.GetWidth())}" height="{p.ToMM(bb.GetHeight())}" fill="#fa7575" opacity=".3"/>')
for ref,f in fps.items():
 bb=f.GetBoundingBox(False,False);x,y,w,h=map(p.ToMM,[bb.GetX(),bb.GetY(),bb.GetWidth(),bb.GetHeight()])
 if ref.startswith('MH'):xx,yy=xy(f);svg.append(f'<circle cx="{xx}" cy="{yy}" r="1.6" fill="#ecf3ee"/>');continue
 svg.append(f'<g><title>{html.escape(ref+" "+f.GetValue())}</title><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#10251f" stroke="#749589" stroke-width=".1"/>')
 for pad in f.Pads():
  if not pad.IsOnLayer(p.F_Cu):continue
  bb=pad.GetBoundingBox();a,bb_y,ww,hh=map(p.ToMM,[bb.GetX(),bb.GetY(),bb.GetWidth(),bb.GetHeight()])
  svg.append(f'<rect x="{a}" y="{bb_y}" width="{ww}" height="{hh}" fill="{colors[domain(pad.GetNetname())]}"><title>{html.escape(ref+"."+pad.GetNumber()+" "+pad.GetNetname())}</title></rect>')
 if ref[0] in 'UJYLF':svg.append(f'<text class="ref" x="{x+w/2}" y="{y+h/2+.5}" text-anchor="middle">{ref}</text>')
 svg.append('</g>')
for layer,color in [('B.Cu','#75adff'),('F.Cu','#ff9999')]:
 svg.append(f'<g id="copper-{layer[0]}" fill="none" stroke="{color}" stroke-linecap="round">')
 for s in segments:
  if s['layer']!=layer:continue
  a,z=s['a'],s['b'];svg.append(f'<path d="M{a[0]},{a[1]} L{z[0]},{z[1]}" stroke-width="{s["width_mm"]}"><title>{html.escape(s["net"])} / {layer}</title></path>')
 svg.append('</g>')
svg.append('<g id="copper-vias" fill="#bed1f5" stroke="#162b21" stroke-width=".13">')
for v in vias:x,y=v['at'];svg.append(f'<circle cx="{x}" cy="{y}" r="{v["diameter_mm"]/2}"><title>{v["net"]} / via</title></circle>')
svg.append('</g></svg>');(R/'hardware/routing-R3.svg').write_text(''.join(svg))
print('R.3:',len(segments),'tracks,',len(vias),'vias,',len(zones),'zones,',unrouted,'native unrouted. DRC zero, not released.')
