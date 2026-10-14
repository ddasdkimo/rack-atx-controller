#!/usr/bin/env python3
"""Transparent USD planning model from observed JLC catalog, not a quotation."""
import json,csv,collections,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];x=json.loads((R/'hardware/circuit.json').read_text())
parts=x['parts'];counts=collections.Counter(c['key'] for c in x['components'] if c['sheet']!='adapter' and c['key']!='flag')
pcb={'revision':'S.3','quantity':5,'width_mm':100,'height_mm':110,'layers':2,'total_usd':None,'status':'Gerber calculator options observed; qualified QFN process and accepted full quote pending'}
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
 # A fresh outline must not silently inherit the old bare-PCB price.
 rows[-1].update({'pcb_quantity_purchased':5,'spare_unpopulated_pcbs':5-batch,'pcb_total_usd':None,'materials_total_usd':None,'assembled_total_range_usd':None,'delivered_total_range_usd':None,'assembly_added_total_range_usd':[round(v-subtotal,2) for v in [low,high]]})

ad_counts=collections.Counter(c['key'] for c in x['components'] if c['sheet']=='adapter')
ad10=sum(n*10*price(parts[k],n*10) for k,n in ad_counts.items())
report={'revision':x['revision'],'currency':'USD','catalog_checked_date':'2026-10-13–15','fee_source':'https://jlcpcb.com/help/article/pcb-assembly-price','fee_source_updated':'2026-09-09','quote':False,'components_per_controller':sum(counts.values()),'unique_part_numbers':len(counts),'basic_skus':sum(parts[k]['catalog']['classification']=='Basic' for k in counts),'extended_smt_skus':len(ext_smt),'extended_all_skus':len(ext_all),'smt_joints_estimate_per_board':smt_joints,'manual_joints_estimate_per_board':manual_joints,'batches':rows,'ten_passive_adapters_parts_only_usd':round(ad10,2),'exclusions':['PCB fabrication, rails/panelization, DFM-driven extra operations','component attrition/MOQ and price changes','extra pre-reflow, fixtures, freight, taxes','ten adapter bare PCBs and hand labor','custom harnesses, crimp contacts/housings, motherboard patch leads','external 5V supply and enclosure'],'assumptions':['One-side Economic PCBA; final board/stock acceptance pending','Loading lower case: SMT Extended only; upper case: all Extended including through-hole','No promotional coupons assumed','X-ray counts 1..3 components per board; final classified parts are supplier decision','Selected generic footprints are candidates; no CPL or PCB quote exists']}
report.update({'comparison_updated_date':'2026-10-15','pcb_fabrication_estimate':pcb,'comparison_scope':'Central controller board only; one populated board supports ten hosts. Materials-only means PCB plus components without assembly. Assembled means all controller SMT and through-hole parts soldered by the factory, not firmware-loaded or functionally commissioned.','delivery':{'destination':None,'freight_usd':None,'tax_usd':None,'status':'Pending final quote and destination; unknown is not zero.'}})
report['exclusions'][0]='Final PCB rails/panelization, finish/stackup changes and DFM-driven extra operations'
report['assumptions'][-1]='Gerber/CPL candidate exported and independently parsed; factory placement/DFM and full PCBA quote pending. Qualified bare-PCB price remains unselected.'
report['assumptions'].extend(['Materials-only uses JLC component catalog prices as a comparison baseline, not an offer to ship loose parts; separate distributor prices, MOQ and freight may differ.','Both batches buy five bare PCBs; allocate the complete PCB bill over the number of populated controllers.','Surface finish and thermal via process require the actual factory quote; compare ENIG with factory-qualified HASL rather than assume a finish price.'])
report['board_options']=json.loads((R/'hardware/research/jlc-r3-quote-observations.json').read_text())['options']
report['board_options_observed_date']='2026-10-15'
report['observed_quote']=json.loads((R/'hardware/research/jlc-r3-quote-observations.json').read_text())['pcba_quote']
report['assumptions'][-4]='Native Gerber/CPL review passes; JLC preview revealed connector-origin and library-angle differences. Supplier CPL calibration and QFN DFM remain release blockers. Full Economic quote is recorded separately from these planning estimates.'
for option in report['board_options']:
 option['quantity']=5
 option['five_board_materials_usd']=round(rows[1]['parts_total_usd']+option['bare_pcb_usd'],2)
 option['five_board_assembled_estimate_usd']=[round(v+option['bare_pcb_usd'],2) for v in rows[1]['subtotal_range_usd']]
report['one_board_parts_usd']=round(sum(counts[k]*price(parts[k],counts[k]) for k in counts),2)
report['procurement_preference']='Normal lead time, one-sided Economic assembly, no expedite; choose cheaper available freight at checkout. No time-based discount assumed.'
(R/'hardware/bom/cost-model.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
with (R/'hardware/bom/batch-parts-cost.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['MPN','LCSC','Class','Quantity per controller','Unit USD at 2 boards','Unit USD at 5 boards','Source'])
 for k,n in counts.items():
  p=parts[k];d=p['catalog'];w.writerow([d['mpn'],p['code'],d['classification'],n,price(p,n*2),price(p,n*5),d['source']])
print('B.2 costs:',sum(counts.values()),'components',[(r['boards'],r['parts_total_usd'],r['subtotal_range_usd']) for r in rows])

# Human review view, derived from the same exact batch pricing as the model.
review=[]
for k,n in counts.items():
 p=parts[k];d=p['catalog'];unit=price(p,n*5)
 description={'ledred':'每台 POWER／RESET 驅動狀態燈','ledgreen':'3.3V 電源／輸出啟用燈','ssr':'按鍵隔離開關','iso':'各主機隔離電源','port':'主機線束接頭','mcu':'主控 MCU','eth':'Ethernet 控制器','rj45':'含磁性元件網路座','esd':'訊號 ESD 保護','ldo':'各主機隔離側穩壓','opto':'LED 狀態光耦合器','cmp':'LED 差動比較器','hc595':'按鍵輸出鎖存','buck':'主控電源降壓','barrel':'5 V 電源端子','timer':'按鍵最長動作計時器'}.get(k,'電阻' if k.startswith('R') else '電容' if k.startswith('C') else '其他元件')
 review.append(dict(key=k,description=description,mpn=d['mpn'],code=p['code'],value=p['value'],classification=d['classification'],quantity_per_board=n,unit_usd=unit,per_board_usd=n*unit,batch_total_usd=n*unit*5,source=d['source']))
review.sort(key=lambda p:-p['batch_total_usd'])
live=json.loads((R/'hardware/research/jlc-r3-bom-quote.json').read_text())
live_by_code={p['code']:p for p in live['parts']}
assert set(live_by_code)=={p['code'] for p in review}
for p in review:
 q=live_by_code[p['code']]
 assert p['quantity_per_board']==q['installed_per_board']
 p.update(purchased_for_five=q['purchased_for_five'],extra_quantity=q['extra_quantity'],unit_usd=q['total_usd']/q['purchased_for_five'],per_board_usd=q['total_usd']/5,batch_total_usd=q['total_usd'],price_basis='JLC authenticated 5-board PCBA quote 2026-10-15; purchase quantities include displayed overage')
review.sort(key=lambda p:-p['batch_total_usd'])
design_path=R/'hardware/design.json'
design=json.loads(design_path.read_text());design['costs']=report;design['bom_review']=review
design_path.write_text(json.dumps(design,ensure_ascii=False,indent=2)+'\n')
