#!/usr/bin/env python3
"""Transparent USD planning model from observed JLC catalog, not a quotation."""
import json,csv,collections,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];x=json.loads((R/'hardware/circuit.json').read_text())
parts=x['parts'];counts=collections.Counter(c['key'] for c in x['components'] if c['sheet']!='adapter' and c['key']!='flag')
pcb=json.loads((R/'hardware/research/pcb-price-2026-10-14.json').read_text())
def price(p,n):
 bands=p['catalog']['prices'];return max((b for b in bands if b['min_qty']<=n),key=lambda b:b['min_qty'])['usd']
for k in counts:
 d=parts[k]['catalog'];assert d['mpn'] and d['stock']>=counts[k]*5 and 'Economic' in d['pcba_type'],(k,d)
manual=[k for k in counts if parts[k]['catalog']['assembly']=='Wave Soldering']
smt=[k for k in counts if k not in manual]
ext_smt=[k for k in smt if parts[k]['catalog']['classification']=='Extended']
ext_all=[k for k in counts if parts[k]['catalog']['classification']=='Extended']
def joints(k):return {'usb':20,'rj45':14}.get(k,len(parts[k]['pins']))
smt_joints=sum(counts[k]*joints(k) for k in smt);manual_joints=sum(counts[k]*joints(k) for k in manual)
rows=[]
for batch in [2,5]:
 subtotal=sum(counts[k]*batch*price(parts[k],counts[k]*batch) for k in counts)
 setup=8.18+1.53+.45+3.58
 assembly=batch*(smt_joints*.0016+manual_joints*.0164)
 # One QFN minimum, plus both leadless crystals as an upper X-ray case.
 xray_min=batch*1.64;xray_qty=batch*3;xray_max=xray_qty*(1.64 if xray_qty<=10 else .82)
 low=subtotal+setup+len(ext_smt)*3.07+assembly+xray_min
 high=subtotal+setup+len(ext_all)*3.07+assembly+xray_max
 rows.append({'boards':batch,'parts_total_usd':round(subtotal,2),'parts_per_board_usd':round(subtotal/batch,2),'assembly_labor_total_usd':round(assembly,2),'setup_stencil_confirmation_manual_setup_usd':round(setup,2),'feeder_usd_range':[round(len(ext_smt)*3.07,2),round(len(ext_all)*3.07,2)],'xray_usd_range':[round(xray_min,2),round(xray_max,2)],'subtotal_range_usd':[round(low,2),round(high,2)],'per_controller_range_usd':[round(low/batch,2),round(high/batch,2)]})
 # Charge the full five-PCB purchase to each batch, including unpopulated spares.
 row=rows[-1];assert batch<=pcb['quantity']
 material_total=round(row['parts_total_usd']+pcb['total_usd'],2)
 assembled_total=[round(v+pcb['total_usd'],2) for v in row['subtotal_range_usd']]
 row.update({'pcb_quantity_purchased':pcb['quantity'],'spare_unpopulated_pcbs':pcb['quantity']-batch,'pcb_total_usd':pcb['total_usd'],'materials_total_usd':material_total,'materials_per_controller_usd':round(material_total/batch,2),'assembly_added_total_range_usd':[round(v-row['parts_total_usd'],2) for v in row['subtotal_range_usd']],'assembled_total_range_usd':assembled_total,'assembled_per_controller_range_usd':[round(v/batch,2) for v in assembled_total],'delivered_total_range_usd':None})
ad_counts=collections.Counter(c['key'] for c in x['components'] if c['sheet']=='adapter')
ad10=sum(n*10*price(parts[k],n*10) for k,n in ad_counts.items())
report={'revision':x['revision'],'currency':'USD','catalog_checked_date':'2026-10-13','fee_source':'https://jlcpcb.com/help/article/pcb-assembly-price','fee_source_updated':'2026-09-09','quote':False,'components_per_controller':sum(counts.values()),'unique_part_numbers':len(counts),'basic_skus':sum(parts[k]['catalog']['classification']=='Basic' for k in counts),'extended_smt_skus':len(ext_smt),'extended_all_skus':len(ext_all),'smt_joints_estimate_per_board':smt_joints,'manual_joints_estimate_per_board':manual_joints,'batches':rows,'ten_passive_adapters_parts_only_usd':round(ad10,2),'exclusions':['PCB fabrication, rails/panelization, DFM-driven extra operations','component attrition/MOQ and price changes','extra pre-reflow, fixtures, freight, taxes','ten adapter bare PCBs and hand labor','custom harnesses, crimp contacts/housings, motherboard patch leads','external 5V supply and enclosure'],'assumptions':['One-side Economic PCBA; final board/stock acceptance pending','Loading lower case: SMT Extended only; upper case: all Extended including through-hole','No promotional coupons assumed','X-ray counts 1..3 components per board; final classified parts are supplier decision','Selected generic footprints are candidates; no CPL or PCB quote exists']}
report.update({'comparison_updated_date':'2026-10-14','pcb_fabrication_estimate':pcb,'comparison_scope':'Central controller board only; one populated board supports ten hosts. Materials-only means PCB plus components without assembly. Assembled means all controller SMT and through-hole parts soldered by the factory, not firmware-loaded or functionally commissioned.','delivery':{'destination':None,'freight_usd':None,'tax_usd':None,'status':'Pending final quote and destination; unknown is not zero.'}})
report['exclusions'][0]='Final PCB rails/panelization, finish/stackup changes and DFM-driven extra operations'
report['assumptions'][-1]='Candidate footprints only; no Gerber/CPL or accepted PCBA quote. Bare PCB price is a dimensional calculator estimate.'
report['assumptions'].extend(['Materials-only uses JLC component catalog prices as a comparison baseline, not an offer to ship loose parts; separate distributor prices, MOQ and freight may differ.','Both batches buy five bare PCBs; allocate the complete PCB bill over the number of populated controllers.','LeadFree HASL is a cost-model assumption, pending final QFN and PCB process review.'])
(R/'hardware/bom/cost-model.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
with (R/'hardware/bom/batch-parts-cost.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['MPN','LCSC','Class','Quantity per controller','Unit USD at 2 boards','Unit USD at 5 boards','Source'])
 for k,n in counts.items():
  p=parts[k];d=p['catalog'];w.writerow([d['mpn'],p['code'],d['classification'],n,price(p,n*2),price(p,n*5),d['source']])
print(json.dumps(report,ensure_ascii=False,indent=2))
