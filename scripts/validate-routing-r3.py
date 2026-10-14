#!/usr/bin/env python3
"""Native B.2/R.3 checks. Run with KiCad Python; does not release manufacturing."""
import wx, json, hashlib, subprocess, collections, uuid, math
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
cli='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
C=json.loads((R/'hardware/circuit.json').read_text())
reports={}
for name,base in [('controller','rack-atx-controller'),('adapter','adapter')]:
 path=R/f'hardware/cad/B2/{base}.kicad_pcb'
 sha=hashlib.sha256(path.read_bytes()).hexdigest()
 out=R/f'artifacts/local/b2-{name}-final-drc.json'
 subprocess.run([cli,'pcb','drc','--format','json','--severity-all','-o',str(out),str(path)],check=True,capture_output=True)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==sha,'Board changed during DRC'
 j=json.loads(out.read_text());b=p.LoadBoard(str(path));b.BuildConnectivity()
 fps={f.GetReference():f for f in b.GetFootprints()}
 parts=[c for c in C['components'] if c['key']!='flag' and ((c['sheet']=='adapter')==(name=='adapter'))]
 assert set(fps)=={c['ref'] for c in parts}|(set() if name=='adapter' else {'MH1','MH2','MH3','MH4'})
 pins=0
 for c in parts:
  f=fps[c['ref']]
  assert str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())==C['parts'][c['key']]['footprint'],c['ref']
  keys=['adapter-root',c['ref']] if name=='adapter' else ['root','sheet:'+c['sheet'],c['ref']]
  expected='/'+'/'.join(str(uuid.uuid5(uuid.NAMESPACE_URL,'rack-atx/B2/'+key)) for key in keys)
  assert f.GetPath().AsString()==expected,(c['ref'],'schematic UUID')
  for num,net in c['nets'].items():
   actual=[d.GetNetname() for d in f.Pads() if d.GetNumber()==num]
   assert actual and all(n==(net or '') for n in actual),(c['ref'],num,net,actual)
   pins+=1
 native=b.GetConnectivity().GetUnconnectedCount(False)
 assert native==0 and not j['violations'] and not j['unconnected_items'],(name,native,collections.Counter(v['type'] for v in j['violations']))
 tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)]
 vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
 nets={}
 for net in ['BUCK_SW','BUCK_BST','MCU_XN','MCU_XP','MCU_XP_CR','ETH_XI','ETH_XO','USB_DP','USB_DM','ETH_TXP','ETH_TXN','ETH_RXP','ETH_RXN']:
  ts=[t for t in tracks if t.GetNetname()==net]
  if ts:nets[net]=dict(total_copper_length_mm=round(sum(p.ToMM(t.GetLength()) for t in ts),3),vias=sum(t.GetNetname()==net for t in vias),layers=sorted({b.GetLayerName(t.GetLayer()) for t in ts}))
 for net in ['BUCK_SW','BUCK_BST','MCU_XN','MCU_XP','MCU_XP_CR','ETH_XI','ETH_XO']:
  if net in nets:assert nets[net]['vias']==0 and nets[net]['layers']==['F.Cu'],(net,nets[net])
 reports[name]=dict(pcb_sha256=sha,kicad_version=j['kicad_version'],native_unrouted=native,drc_violations=0,drc_unconnected_items=0,ignored_checks=j['ignored_checks'],pins_checked=pins,electrical_components=len(parts),track_segments=len(tracks),vias=len(vias),copper_layers=b.GetCopperLayerCount(),key_net_metrics=nets,schematic_validation='Component set, all defined pin nets (including NC), footprint IDs and symbol UUID paths match circuit.json; circuit.json is separately checked against native KiCad XML/ERC.')
power=json.loads((R/'artifacts/local/r3-power-path-audit.json').read_text())
assert power['pcb_sha256']==reports['controller']['pcb_sha256']
mcu=[x for x in power['paths'] if x['target'].startswith('U2.')]
assert len(mcu)==6 and all(x['drop_v'] is not None for x in mcu)
# Report nominal geometry separately from an intentionally conservative width stress.
power['mcu_max_nominal_copper_drop_v']=max(x['drop_v'] for x in mcu)
power['mcu_width_minus_20pct_drop_upper_bound_v']=round(power['mcu_max_nominal_copper_drop_v']/.8,4)
power['review_copper_drop_budget_v']=.15
assert power['mcu_width_minus_20pct_drop_upper_bound_v']<.15
summary=dict(revision='R.3',schematic_revision='B.2',**reports,power=power,manufacturing_ready=False,limits=['DRC applies the committed two-layer, 1 oz, 0.15 mm trace/clearance profile; default ignored checks are listed explicitly.','Total copper lengths include branches; they are not differential-pair skew measurements. USB/Ethernet impedance and return continuity are not qualified.','Copper-only DC estimate excludes ground return, component drops and transients; not a temperature-rise test.','Footprint/factory DFM, ESD/EMC, real timer behavior and host compatibility still require physical qualification.'])
(R/'hardware/validation/routing-R3-checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print('PASS: controller and adapter native connectivity/DRC, pin nets, footprints and UUIDs. Manufacturing remains unqualified.')
