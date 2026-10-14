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
out={'checked_at':'2026-10-15','pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tlp3122a_land_pattern':{'status':'pass drawing and actual PCB pad geometry','checked_instances':sorted(ssrs),'pad_mm':[.8,1.2],'same_row_pitch_mm':2.54,'opposing_row_centers_mm':6.3,'pin_assignment':{'1':'anode','3':'cathode','4':'drain','6':'drain'},'source':'https://toshiba.semicon-storage.com/us/semiconductor/design-development/package/detail.4pin%20SO6.html','drawing':'https://toshiba.semicon-storage.com/content/dam/toshiba-ss-v3/master/en/semiconductor/design-development/package-detail/Pkg_paddim/4pinSO6_paddim.gif','method':'Original maker land-pattern drawing visually inspected in browser; pad geometry checked in all 20 native footprints. Not assembly process qualification.'},'highspeed_nets':rows,'blocking_findings':[{'id':'HS-01','description':'Ethernet TX has two vias per net; WIZnet MDI guide prohibits via/layer changes. RX connector-side pair must also be inspected, not just ETH_RX* segment.','source':'https://docs.wiznet.io/Design-Guide/hardware_design_guide'},{'id':'HS-02','description':'USB and MDI runs have no established impedance geometry or complete reference continuity. Total net copper lengths include branches and must not be used as pair skew.','source':'https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html'}],'manufacturing_ready':False}
(R/'hardware/validation/pre-release-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
