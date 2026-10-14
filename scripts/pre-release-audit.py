#!/usr/bin/env python3
"""Read-only manufacturer geometry audit; findings are not a fabrication release."""
import wx,json,hashlib,math,heapq
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];path=R/'hardware/cad/B2/rack-atx-controller.kicad_pcb';b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()}
rows=[]
for n in ['USB_DP','USB_DM','USB_DP_MCU','USB_DM_MCU','ETH_TXP','ETH_TXN','ETH_RXP','ETH_RXN','RJ_RD_P','RJ_RD_N']:
 ts=[t for t in b.GetTracks() if t.GetNetname()==n and not isinstance(t,p.PCB_VIA)];vs=[t for t in b.GetTracks() if t.GetNetname()==n and isinstance(t,p.PCB_VIA)]
 rows.append(dict(net=n,total_copper_mm=round(sum(p.ToMM(t.GetLength()) for t in ts),4),vias=len(vs),widths_mm=sorted({p.ToMM(t.GetWidth()) for t in ts}),layers=sorted({b.GetLayerName(t.GetLayer()) for t in ts})))
ssrs=[]
for f in b.GetFootprints():
 if str(f.GetFPID().GetLibItemName())!='TLP3122A_11-4M1S':continue
 ds={d.GetNumber():d for d in f.Pads()}; sizes={tuple(round(p.ToMM(v),5) for v in [d.GetSize().x,d.GetSize().y]) for d in ds.values()}
 dist=lambda a,z:math.dist((ds[a].GetPosition().x,ds[a].GetPosition().y),(ds[z].GetPosition().x,ds[z].GetPosition().y))/1e6
 assert sizes=={(.8,1.2)}
 assert abs(dist('1','3')-2.54)<1e-6 and abs(dist('1','6')-6.3)<1e-6
 ssrs.append(f.GetReference())
assert len(ssrs)==20, ssrs
f=fps['U2']; ep=next(d for d in f.Pads() if d.GetNumber()=='57')
cx,cy=[p.ToMM(v) for v in [ep.GetPosition().x,ep.GetPosition().y]]
ew,eh=[p.ToMM(v) for v in [ep.GetSize().x,ep.GetSize().y]]
thermal_vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)
 and t.GetNetname()==ep.GetNetname()
 and abs(p.ToMM(t.GetPosition().x)-cx)<ew/2
 and abs(p.ToMM(t.GetPosition().y)-cy)<eh/2]
paste=[d for d in f.Pads() if d.IsOnLayer(p.F_Paste) and not d.GetNumber()]
paste_area=0
for d in paste:
 w,h=[p.ToMM(v) for v in [d.GetSize().x,d.GetSize().y]]
 radius=p.ToMM(d.GetRoundRectCornerRadius()) if d.GetShape()==p.PAD_SHAPE_ROUNDRECT else 0
 paste_area+=w*h-(4-math.pi)*radius*radius
def crosses_rect(a,z,rect):
 # Segment/rectangle clipping, rather than an enclosing-box false positive.
 lo,hi=0.,1.
 for start,delta,mn,mx in zip(a,[z[0]-a[0],z[1]-a[1]],rect[:2],rect[2:]):
  if abs(delta)<1e-10:
   if not mn<=start<=mx:return False
  else:
   u,v=sorted(((mn-start)/delta,(mx-start)/delta));lo=max(lo,u);hi=min(hi,v)
   if lo>hi:return False
 return True
under_ep=[]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.B_Cu or t.GetNetname()==ep.GetNetname():continue
 a=[p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)];z=[p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)]
 if crosses_rect(a,z,[cx-ew/2,cy-eh/2,cx+ew/2,cy+eh/2]):
  under_ep.append(dict(net=t.GetNetname(),start_mm=a,end_mm=z,width_mm=p.ToMM(t.GetWidth())))
out={'checked_at':'2026-10-15','pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tlp3122a_land_pattern':{'status':'pass drawing and actual PCB pad geometry','checked_instances':sorted(ssrs),'pad_mm':[.8,1.2],'same_row_pitch_mm':2.54,'opposing_row_centers_mm':6.3,'pin_assignment':{'1':'anode','3':'cathode','4':'drain','6':'drain'},'source':'https://toshiba.semicon-storage.com/us/semiconductor/design-development/package/detail.4pin%20SO6.html','drawing':'https://toshiba.semicon-storage.com/content/dam/toshiba-ss-v3/master/en/semiconductor/design-development/package-detail/Pkg_paddim/4pinSO6_paddim.gif','method':'Original maker land-pattern drawing visually inspected in browser; pad geometry checked in all 20 native footprints. Not assembly process qualification.'},'highspeed_nets':rows,'blocking_findings':[{'id':'HS-01','description':'Ethernet TX has two vias per net; WIZnet MDI guide prohibits via/layer changes. RX connector-side pair must also be inspected, not just ETH_RX* segment.','source':'https://docs.wiznet.io/Design-Guide/hardware_design_guide'},{'id':'HS-02','description':'USB and MDI runs have no established impedance geometry or complete reference continuity. Total net copper lengths include branches and must not be used as pair skew.','source':'https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html'}],'manufacturing_ready':False}
out['qfn_process']={
 'ref':'U2','mpn':'ESP32-S3FN8','copper_ep_mm':[ew,eh],
 'peripheral_pitch_mm':.4,'thermal_vias_inside_ep':len(thermal_vias),
 'recommended_minimum_vias':9,'paste_windows':len(paste),
 'paste_coverage_percent':round(100*paste_area/(ew*eh),3),
 'non_ground_bottom_tracks_under_ep':under_ep,
 'guide':'https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html',
 'package_drawing':'https://documentation.espressif.com/esp32-s3_datasheet_en.pdf',
 'qualification':'Geometry inspection only. Paste, via treatment, finish and stencil must be agreed with assembler; not solder-joint validation.'}
if len(thermal_vias)<9:
 out['blocking_findings'].append({'id':'DFM-01','description':'U2 exposed pad lacks the recommended nine direct ground vias. Add vias and coordinate paste windows/via treatment; do not rely on a thin surface ground trace.'})
if under_ep:
 out['blocking_findings'].append({'id':'HS-03','description':'Non-ground B.Cu traces run under the ESP32 exposed pad and split its reference copper. Reserve continuous ground beneath MCU and oscillator during routing repair.'})
out['two_layer_impedance']={'factory_controlled_impedance':False,'source':'https://jlcpcb.com/capabilities/pcb-capabilities/','note':'Published controlled-impedance service begins at four layers. Two-layer prototype routing targets are not a factory impedance guarantee; use estimated geometry plus physical link/USB testing.'}
(R/'hardware/validation/pre-release-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
