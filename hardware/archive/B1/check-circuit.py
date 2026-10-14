#!/usr/bin/env python3
"""Check exported KiCad connectivity, isolation boundaries and analytical margins.
Not a SPICE run or a substitute for prototype electrical measurements.
"""
import json, csv, math, itertools, xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1]
x=json.loads((R/'hardware/circuit.json').read_text());parts=x['parts']
report={'revision':x['revision'],'method':'KiCad exported netlist + bounded DC calculations; no physical test / SPICE'}
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
 lib,name=p['footprint'].split(':');path=fpbase/(lib+'.pretty')/(name+'.kicad_mod')
 pads=set(re.findall(r'\(pad "([^"]+)"',path.read_text()))
 assert pads=={n for n,_,_ in p['pins']},(key,pads,p['pins'])
report['unassigned_footprints']=missing
report['isolation_topology']='PASS: controller and ten host domains remain separate through defined barriers'
# Direct map check catches plausible but wrong 4-pin aliases.
assert [p[0] for p in parts['ssr']['pins']]==['1','3','4','6']
assert [p[1] for p in parts['usbesd']['pins']]==['GND','IO1','IO2','VCC']
# LED threshold corners: independently 1.5% effective resistor variation (1% tolerance + 0.5% thermal allowance), 3.3V +/-3%,
# conservative total input-referred error +/-14mV covers offset + bias mismatch.
# Solve conductance network including finite comparator output pull-up resistance.
def threshold(vcm,rail,res,on,err):
 rp,rg,rm,rmg,rb,rf1,rf2,ro=res;rf=rf1+rf2
 if on:
  # Low state <=0.7V at <=4mA over 0..70C; test both bounds.
  ov=ro
  vm=(vcm/rm+rail/rb+ov/rf)/(1/rm+1/rmg+1/rb+1/rf)
 else:
  # Output high: the feedback draws through the 10k pullup.
  vm=(vcm/rm+rail/rb+rail/(rf+ro))/(1/rm+1/rmg+1/rb+1/(rf+ro))
 return (vm+err)*(1+rp/rg)-vcm
bounds={}
for state in ['turn_on','turn_off']:
 vals=[]
 for vcm,rail,err,signs in itertools.product([0,5],[3.201,3.399],[-.014,.014],itertools.product([.985,1.015],repeat=8)):
  rr=[a*b for a,b in zip([100e3,10e3,100e3,10e3,390e3,1020e3,1020e3,10e3],signs)]
  if state=='turn_off':
   for low in [0,.7]:vals.append(threshold(vcm,rail,rr[:-1]+[low],True,err))
  else:vals.append(threshold(vcm,rail,rr,False,err))
 bounds[state]=[round(min(vals),3),round(max(vals),3)]
assert bounds['turn_on'][1]<1.4,bounds
assert bounds['turn_off'][0]>.2,bounds
report['led_threshold_V']=bounds
report['led_input_loading_bound_uA']=round(5/(100e3*.99)*1e6,2)
report['led_conditions']='0..5V on each input, OFF differential <=0.2V, ON >=1.4V; resistor effective 1.5% including temperature allowance, host rail +/-3%, combined comparator input error +/-14mV. Motherboard envelope must be measured.'
report['photorelay_if_min_mA']=round((4.5-1.7-.3)/(440*1.01)*1000,3)
assert report['photorelay_if_min_mA']>=5
report['photorelay_if_max_mA']=round((5.25-1.0)/(440*.99)*1000,3)
report['timer_nominal_s']=round(math.log(3)*510000*30e-6,2)
report['timer_note']='Timing capacitance under DC bias and temperature is unmeasured; 8..25s is a qualification target, not a guaranteed bound. Static stall releases; repeated edges can trigger further windows.'
(R/'hardware/validation').mkdir(exist_ok=True)
# Preserve the behavioral SPICE summary written by hardware/simulation/run.py; this script does not run SPICE.
_prev=R/'hardware/validation/checks.json'
if _prev.exists():
 _old=json.loads(_prev.read_text())
 if 'spice_simulation' in _old:report['spice_simulation']=_old['spice_simulation']
(R/'hardware/validation/checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
