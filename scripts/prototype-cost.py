#!/usr/bin/env python3
"""P.0 scope budget using B.1 catalog parts; NOT a schematic-derived production BOM."""
import json, collections
from pathlib import Path
R=Path(__file__).resolve().parents[1]
x=json.loads((R/'hardware/circuit.json').read_text());parts=x['parts']
selected=[]
for c in x['components']:
 if c['key']=='flag':continue
 if c['sheet'].startswith('outputs') and c['ref'] not in {'U5','U6','C38','C39'}:selected.append(c['key'])
 elif c['ref'] in {'J101','F1','Q1','C1','C2'}:selected.append(c['key'])
 elif c['sheet'].startswith(('host01_','host02_')):
  nets=[n for n in c['nets'].values() if n]
  control=(c['key'] in {'port','ssr'} or any(n.startswith('CTRL_') or n=='PHOTO_5V' or n.startswith('DRV_') for n in nets))
  control_esd=c['key']=='esd' and any('_PWR_' in n or '_RST_' in n for n in nets)
  if control or control_esd:selected.append(c['key'])
 elif c['sheet']=='adapter':selected.extend([c['key']]*2)
# Provisional 16-pin bench interface: eight known two-pin headers, not a final keyed connector.
selected+=['header2']*8+['R10k','R100k','R100k','C1u']
counts=collections.Counter(selected)
assert counts['ssr']==4 and counts['port']==4 and counts['hc595']==1
assert not any(counts[k] for k in ['iso','ldo','cmp','opto','mcu','eth','rj45','buck'])
def unit(k,n):return max((b for b in parts[k]['catalog']['prices'] if b['min_qty']<=n),key=lambda b:b['min_qty'])['usd']
manual=[k for k in counts if parts[k]['catalog']['assembly']=='Wave Soldering']
smt=[k for k in counts if k not in manual]
extended=[k for k in smt if parts[k]['catalog']['classification']=='Extended']
ext_th=[k for k in manual if parts[k]['catalog']['classification']=='Extended']
smt_joints=sum(counts[k]*len(parts[k]['pins']) for k in smt)
th_joints=sum(counts[k]*len(parts[k]['pins']) for k in manual)
batches=[]
for n in [2,5]:
 rows=[dict(key=k,mpn=parts[k]['catalog']['mpn'],code=parts[k]['code'],per_panel=q,batch_qty=q*n,unit_usd=unit(k,q*n),total_usd=round(q*n*unit(k,q*n),4),assembly=parts[k]['catalog']['assembly'],source=parts[k]['catalog']['source']) for k,q in counts.items()]
 total=sum(row['total_usd'] for row in rows)
 pcb=14.26; common=8.18+1.53+.45+8.21; feeder=len(extended)*3.07
 smt_labor=n*smt_joints*.0016; th_labor=3.58+n*th_joints*.0164
 minimum=pcb+total+common+feeder+smt_labor
 batches.append(dict(assembled_panels=n,bare_panels_purchased=5,control_modules=n,passive_adapters=2*n,host_capacity=2*n,spare_bare_panels=5-n,parts_total_usd=round(total,2),parts_smt_usd=round(sum(r['total_usd'] for r in rows if r['key'] in smt),2),parts_through_hole_usd=round(sum(r['total_usd'] for r in rows if r['key'] in manual),2),pcb_usd=pcb,materials_usd=round(pcb+total,2),setup_stencil_confirmation_panel_usd=round(common,2),smt_feeder_usd=round(feeder,2),smt_labor_usd=round(smt_labor,2),smt_factory_th_self_solder_total_usd=round(minimum,2),through_hole_labor_usd=round(th_labor,2),optional_th_feeder_usd=round(len(ext_th)*3.07,2),fully_soldered_total_usd_range=[round(minimum+th_labor,2),round(minimum+th_labor+len(ext_th)*3.07,2)],rows=rows))
report=dict(revision='P.0 budget only',currency='USD',catalog_basis_date='2026-10-13',pcb_calculator_date='2026-10-14',production_bom=False,provisional_parts_per_panel=sum(counts.values()),provisional_unique_mpn=len(counts),smt_joints_per_panel=smt_joints,through_hole_joints_per_panel=th_joints,extended_smt_keys=extended,extended_through_hole_keys=ext_th,batches=batches,assumptions=['One 2-host control module and two passive adapters per panel; two different designs','100 x 100 mm total panel INCLUDING rails is a quotation scenario only; layout feasibility unverified','Two-layer 1.6 mm LeadFree HASL green/white, tented vias, normal lead time','Keep TLP3122A, one 74HC595, TLC555 limiting and protection; omit custom MCU/Ethernet and all LED sensing','Use 3.3 V logic from external dev board; verify its current budget and 5 V power source','Provisional sixteen-pin interface priced as eight known two-pin headers; final connector and pinout not selected','All parts use observed JLC catalog quantity breaks at actual prototype batch quantity; no QFN/BGA/X-ray assumed','SMT-only total includes through-hole parts budget sourced separately by user; JLC does not ship those loose parts','Through-hole feeder upper bound counts Extended through-hole MPNs; final cart decides'],excludes=['ESP32 development board, power supply, USB cable','Host harnesses, crimp housings/contacts, wire and enclosure','Component attrition/MOQ and separate-distributor price differences','Final panel engineering/DFM or fixture charges beyond observed calculator and explicit PCBA panel fee','Shipping, tax, tools, user soldering labor and firmware commissioning'])
(R/'hardware/prototype-cost.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='batches'},ensure_ascii=False,indent=2))
print(json.dumps([{k:v for k,v in b.items() if k!='rows'} for b in batches],ensure_ascii=False,indent=2))
