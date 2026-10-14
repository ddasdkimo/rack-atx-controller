#!/usr/bin/env python3
"""B.2 aggregate-counter behavioral study. Not a vendor model or hardware test."""
import json,itertools,subprocess,tempfile,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
c=json.loads((R/'hardware/circuit.json').read_text());cs={x['ref']:x for x in c['components']};parts=c['parts']
assert c['revision']=='B.2' and parts['timer']['code']=='C7292' and parts['C1n']['code']=='C163508'
assert cs['R31']['key']==cs['R32']['key']=='R100k'
assert all(cs['RT'+str(i)]['key']=='R100k' for i in range(1,5))
assert c['gpio']['4']=='TIMER_ARM' and c['gpio']['6']=='OUT_OE_N' and c['gpio']['7']=='OUT_LATCH'
NOM=32768*2.3*200e3*1e-9
# IC clock +/-25% stress assumption, R +/-1.5%, C +/-5.2%.
DECK='''B.2 counted timeout and independent ARM gate
.include {models}
.param V5={v5} TRAMP={ramp} ARM_T={arm_t} ARM_PW={arm_pw} ARM_PER={arm_per} TSTOP={stop}
.param PERIOD={period} LEAK={leak} FORCE_OE={force_oe} QFAULT={qfault}
V5 5V 0 PWL(0 0 {{TRAMP}} {{V5}})
Bv33 3V3 0 V = min(3.3,max(0,V(5V)-1))
Vcmd CMD 0 PULSE(0 1 {{ARM_T}} 1u 1u {{ARM_PW}} {{ARM_PER}})
Barm_src ARM_SRC 0 V = V(CMD)*V(3V3)
.model GPIO SW(VT=0.5 VH=0.05 RON=40 ROFF=1e12)
Sarm ARM_SRC ARM CMD 0 GPIO
Ileak 3V3 ARM {{LEAK}}
R27 ARM 0 10k
R28 ARM ARM_RESET_B 10k
R29 ARM_RESET_B 0 100k
Q2 TIMER_MR ARM_RESET_B 0 MMBT3904_LO
R30 5V TIMER_MR 10k
* Aggregated 32768 clock counts, MR resets. QSEL=1: Q HIGH while reset.
* AR=1: disable internal auto-reset, which is not specified at 5 V.
Ccount COUNT 0 1 IC=0
Bcount 0 COUNT I = (V(TIMER_MR)<0.3*V(5V) && V(5V)>3 && V(COUNT)<1.1) ? 1/{{PERIOD}} : 0
Breset COUNT 0 I = (V(TIMER_MR)>0.7*V(5V) || V(5V)<3) ? V(COUNT)/1u : 0
Bq QI 0 V = ((V(COUNT)<1 || {{QFAULT}}>0.5) && V(5V)>0.1) ? V(5V) : 0
Rout QI TIMER_OUT 500
R33 TIMER_OUT GATE_BASE 10k
R34 GATE_BASE 0 100k
Q3 PHOTO_GATE GATE_BASE ARM_SINK MMBT3904_LO
R37 ARM ARM_GATE_B 10k
R38 ARM_GATE_B 0 100k
Q200 ARM_SINK ARM_GATE_B 0 MMBT3904_LO
R35 PHOTO_GATE 5V 10k
XQ4 PHOTO_GATE 5V PHOTO_5V AO3401A
R36 PHOTO_5V 0 10k
Rload PHOTO_5V 0 {load}
* Indicators use conservative piecewise forward-drop models, not vendor LED models.
Bpwr 3V3 0 I = max(0,(V(3V3)-2.6)/330)
Ben 3V3 OE_N I = max(0,(V(3V3,OE_N)-2.6)/330)
R25 3V3 OE_N 10k
Boe OE_N 0 I = (V(CMD)>0.5 || {{FORCE_OE}}>0.5) ? V(OE_N)/40 : 0
Bdrv DRV_I 0 V = (V(OE_N)<0.3*V(3V3)) ? V(3V3) : 0
Rdrv DRV_I DRV 40
R39 DRV CTRL_B 1.5k
R40 CTRL_B 0 100k
Q5 CTRL_K CTRL_B 0 MMBT3904_LO
R41 PHOTO_5V CTRL_R 220
R42 CTRL_R CTRL_A 220
XSSR CTRL_A CTRL_K H_PWR_A H_PWR_B TLP3122A
Vind INDK CTRL_K 0
Bind PHOTO_5V INDK I = max(0,(V(PHOTO_5V,CTRL_K)-1.8)/1500)
Vhost HV H_PWR_B 3.3
Rhost HV H_PWR_A 10k
Rtie H_PWR_B 0 1G
Bon ONFLAG 0 V = V(PHOTO_5V)>2.5 ? 1 : 0
Bcl CLOSED 0 V = V(H_PWR_A,H_PWR_B)<1 ? 1 : 0
.options method=gear
.tran 2m {{TSTOP}}
.meas tran ARM_BOOT_MAX MAX V(ARM) FROM=0 TO=0.04
.meas tran RAIL_BOOT_MAX MAX V(PHOTO_5V) FROM=0 TO=0.04
.meas tran IF_MAX MAX I(V.XSSR.VSENS)
.meas tran IND_MAX MAX I(Vind)
.meas tran IND_END FIND I(Vind) AT={{TSTOP-0.01}}
.meas tran CLOSED_TOTAL INTEG V(CLOSED)
.meas tran ON_TOTAL INTEG V(ONFLAG)
.meas tran T_ON WHEN V(PHOTO_5V)=2.5 RISE=1
.meas tran T_OFF WHEN V(PHOTO_5V)=2.5 FALL=1
.meas tran PULSE_W PARAM='T_OFF-T_ON'
.meas tran RAIL_END FIND V(PHOTO_5V) AT={{TSTOP-0.01}}
.end
'''
def run(**changes):
 d=dict(models=str(H/'models.lib'),v5=5,ramp='10m',arm_t='0.05',arm_pw=40,arm_per=1000,stop=35,period=NOM,leak='1u',force_oe=0,qfault=0,load=22);d.update(changes)
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'b2.cir';f.write_text(DECK.format(**d));p=subprocess.run(['/opt/homebrew/bin/ngspice','-b',str(f)],capture_output=True,text=True,timeout=45)
  out=p.stdout+'\n'+p.stderr;m={}
  for k,v in re.findall(r'^\s*([a-z_]+)\s*=\s*([-+0-9.eE]+)',out,re.M):
   try:m[k]=float(v)
   except ValueError:pass
  if not {'on_total','closed_total','if_max','rail_end'}<=m.keys():raise RuntimeError(out[-1800:])
  return m

def main():
 corners=[]
 for kr,kc,kf,v5 in itertools.product([.985,1.015],[.948,1.052],[.75,1.25],[4.75,5.25]):
  period=NOM*kr*kc/kf;m=run(period=period,v5=v5)
  assert 8<=m['pulse_w']<=25 and m['rail_end']<.1 and m['if_max']>=.005 and .001<m['ind_max']<.003 and m['ind_end']<1e-6,m
  corners.append({'resistor_scale':kr,'capacitor_scale':kc,'clock_scale':kf,'supply_V':v5,'pulse_s':m['pulse_w']})
  print('corner',len(corners),round(m['pulse_w'],3),flush=True)
 cases={}
 for name,args in {'nominal':{},'held_arm_60s':{'arm_pw':70,'stop':60},'disarm_after_5s':{'arm_pw':5},'boot_no_firmware':{'arm_t':1000},'boot_oe_stuck_enabled':{'arm_t':1000,'force_oe':1},'boot_timer_q_forced_high':{'arm_t':1000,'force_oe':1,'qfault':1},'fast_power_ramp':{'ramp':'10u','arm_t':1000,'force_oe':1},'slow_power_ramp':{'ramp':1,'arm_t':1000,'force_oe':1},'repeated_arm_commands':{'arm_pw':5,'arm_per':10,'stop':35}}.items():
  m=run(**args);cases[name]=m
  if name.startswith(('boot','fast','slow')):assert m['on_total']<1e-6 and m['closed_total']<1e-6 and m['if_max']<1e-6 and m['ind_max']<1e-6,(name,m)
  if name=='disarm_after_5s':assert 4.95<m['pulse_w']<5.02,m
  if name=='held_arm_60s':assert m['on_total']<25 and m['rail_end']<.1,m
  print(name,'PASS',flush=True)
 report={'revision':'B.2','date':'2026-10-14','method':'ngspice datasheet-fitted aggregate counter and transistor/photorelay behavioral models','vendor_model':False,'hardware_correlated':False,'pass':True,'circuit_sha256':hashlib.sha256((R/'hardware/circuit.json').read_bytes()).hexdigest(),'nominal_timeout_s':NOM,'timer_pulse_range_s':[min(x['pulse_s'] for x in corners),max(x['pulse_s'] for x in corners)],'timer_target_s':[8,25],'oscillator_error_envelope_percent':25,'oscillator_bound_is_model_assumption':True,'corners':corners,'cases':cases,'limitations':['Clock aggregated using datasheet RC equation; physical oscillator and exact IC behavior are not vendor modeled.','Bench-qualify timeout over power and operating temperature before manufacturing release.','Repeated ARM low/high transitions start new windows; not a safety-rated anti-malicious-firmware interlock.','USB/Ethernet SI, ESD, EMC, load transients and PCB behavior not covered.']}
 (H/'results/B2-summary.json').write_text(json.dumps(report,indent=2)+'\n')
 summary={k:report[k] for k in ['revision','method','circuit_sha256','vendor_model','hardware_correlated','pass','nominal_timeout_s','timer_pulse_range_s','oscillator_bound_is_model_assumption','limitations']}
 summary.update(corner_count=len(report['corners']),functional_case_count=len(report['cases']))
 validation=R/'hardware/validation/checks.json';checks=json.loads(validation.read_text());checks['spice_simulation']=summary
 validation.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
 print('B.2 behavioral study PASS',report['timer_pulse_range_s'])
if __name__=='__main__':main()
