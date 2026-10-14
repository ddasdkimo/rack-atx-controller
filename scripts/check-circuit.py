#!/usr/bin/env python3
"""Check exported KiCad connectivity, isolation boundaries and analytical margins.
Not a SPICE run or a substitute for prototype electrical measurements.
"""
import json, csv, math, itertools, xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1]
x=json.loads((R/'hardware/circuit.json').read_text());parts=x['parts']
report={'revision':x['revision'],'method':'KiCad exported netlist + bounded DC calculations; simulation reported separately; no physical test'}
for board in ['controller','adapter']:
 tree=ET.parse(R/f'artifacts/local/{board}.xml')
 actual={}
 for net in tree.findall('.//nets/net'):
  for node in net.findall('node'):actual[(node.attrib['ref'],node.attrib['pin'])]=net.attrib['name']
 expected=[c for c in x['components'] if (c['sheet']=='adapter')==(board=='adapter') and c['key']!='flag']
 checked=0
 for c in expected:
  for pin,net in c['nets'].items():
   got=actual.get((c['ref'],pin))
   assert (got is None or got.startswith('unconnected-')) if net is None else got==net,(c['ref'],pin,net,got)
   checked+=1
 bom=list(csv.DictReader((R/f'hardware/bom/{board}-bom.csv').open()))
 assert sum(int(r['Quantity per board']) for r in bom)==len(expected)
 erc=json.loads((R/f'artifacts/local/{board+"-" if board=="adapter" else ""}erc.json').read_text())
 violations=[v for s in erc['sheets'] for v in s['violations']]
 assert not violations,violations[:2]
 report[board]={'components':len(expected),'pins_checked_against_KiCad':checked,'erc_violations':len(violations)}
# For every component, define only the electrically connected internal domains.
# Isolation components have two separate domains. No component may bridge hosts.
def domain(net):
 if net is None:return None
 if net.startswith('H') and len(net)>3 and net[1:3].isdigit() and not net.endswith(('_PLED_N','_HDD_N')):return net[:3]
 return 'CTRL'
for c in x['components']:
 if c['sheet']=='adapter' or c['key']=='flag':continue
 groups={'iso':[['1','2'],['3','4']], 'ssr':[['1','3'],['4','6']], 'opto':[['1','2'],['3','4']]}.get(c['key'],[list(c['nets'])])
 for group in groups:
  domains={domain(c['nets'][p]) for p in group}-{None}
  assert len(domains)<=1,(c['ref'],c['key'],domains)
# Published selected footprints must have matching physical pad numbers.
fpbase=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
import re
missing=[]
for key,p in parts.items():
 if not p['footprint']:
  if key!='flag':missing.append(key)
  continue
 lib,name=p['footprint'].split(':');path=(R/'hardware/cad/RackATX.pretty' if lib=='RackATX' else fpbase/(lib+'.pretty'))/(name+'.kicad_mod')
 pads=set(re.findall(r'\(pad "([^"]+)"',path.read_text()))
 assert pads=={n for n,_,_ in p['pins']},(key,pads,p['pins'])
report['unassigned_footprints']=missing
report['isolation_topology']='PASS: controller and ten host domains remain separate through defined barriers'
# Direct map check catches plausible but wrong 4-pin aliases.
assert [p[0] for p in parts['ssr']['pins']]==['1','3','4','6']
assert [p[1] for p in parts['usbesd']['pins']]==['GND','IO1','IO2','VCC']
# Control-only topology and boot-critical GPIO mapping.
assert x['revision']=='B.2'
assert not any(c['key'] in ['iso','ldo','cmp','opto'] for c in x['components'])
assert not any(n and ('PLED' in n or 'HDD' in n or 'TIMER_FIRE' in n) for c in x['components'] for n in c['nets'].values())
assert x['gpio']['4']=='TIMER_ARM' and x['gpio']['6']=='OUT_OE_N' and x['gpio']['7']=='OUT_LATCH'
assert not any(str(g) in x['gpio'] for g in [1,2,43,44])
for h in range(1,11):
 cs=[c for c in x['components'] if c['sheet']==f'host{h:02}']
 assert sum(c['key']=='ssr' for c in cs)==2
 assert sum(c['key']=='ledred' for c in cs)==2
 for k,button in enumerate(['PWR','RST']):
  idx=(h-1)*2+k+1; by={c['ref']:c for c in cs};pre=f'CTRL_H{h:02}_{button}'
  assert by[f'D{100+idx}']['nets']=={'1':pre+'_K','2':pre+'_IND_A'}
  assert by[f'R{300+idx}']['nets']=={'1':'PHOTO_5V','2':pre+'_IND_A'}
 j=next(c for c in cs if c['key']=='port')
 assert all(j['nets'][str(i)] is None for i in [5,6,7,8,10])
 assert j['nets']['9']==f'H{h:02}_GND'
t=next(c for c in x['components'] if c['key']=='timer')
assert t['nets']=={'1':'TIMER_RTC','2':'TIMER_CTC','3':'TIMER_RS','4':None,'5':'5V','6':'TIMER_MR','7':'GND_CTRL','8':'TIMER_OUT','9':'5V','10':'GND_CTRL','11':None,'12':'5V','13':'5V','14':'5V'}
byref={c['ref']:c for c in x['components']}
assert byref['Q2']['nets']=={'1':'ARM_RESET_B','2':'GND_CTRL','3':'TIMER_MR'}
assert byref['Q3']['nets']=={'1':'GATE_BASE','2':'ARM_SINK','3':'PHOTO_GATE'}
assert byref['Q200']['nets']=={'1':'ARM_GATE_B','2':'GND_CTRL','3':'ARM_SINK'}
assert byref['D201']['nets']=={'1':'GND_CTRL','2':'PWR_IND_A'}
assert byref['D202']['nets']=={'1':'OUT_OE_N','2':'EN_IND_A'}
report['local_indicators']='20 driver LEDs + 3V3 + active-low output-enable; existing RJ45 LINK/ACT; not physical contact feedback'
report['control_only_topology']='PASS: 20 dry contacts, no LED sensing/supplies, ten separate host ESD references'
report['boot_gpio']={'ARM':4,'OE_N':6,'LATCH':7,'removed_uart_timer_assignments':[43,44]}
report['photorelay_if_min_mA']=round((4.5-1.7-.3)/(440*1.01)*1000,3)
assert report['photorelay_if_min_mA']>=5
report['photorelay_if_max_mA']=round((5.25-1.0)/(440*.99)*1000,3)
report['timer_nominal_s']=round(32768*2.3*200000*1e-9,5)
report['timer_note']='MC14541B single-transition, AR=1, MR high default, QSEL=1, A=B=1. 200k/1nF C0G, Rs=400k. ARM gates the output independently. Clock tolerance/model and physical qualification are reported separately.'
(R/'hardware/validation').mkdir(exist_ok=True)
# Preserve the behavioral SPICE summary written by hardware/simulation/run.py; this script does not run SPICE.
_prev=R/'hardware/validation/checks.json'
if _prev.exists():
 _old=json.loads(_prev.read_text())
 if 'spice_simulation' in _old and _old['spice_simulation'].get('revision')==x['revision']:report['spice_simulation']=_old['spice_simulation']
(R/'hardware/validation/checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
