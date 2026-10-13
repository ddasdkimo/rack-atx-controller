#!/usr/bin/env python3
"""Reproducible pin-connected KiCad schematics and procurement BOM. No PCB placement data."""
import json,uuid,csv,math,re
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/cad';OUT.mkdir(exist_ok=True)
REV='B.1'
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'rack-atx/B1/'+s))
def q(s):return json.dumps(str(s),ensure_ascii=False)
P={}
def part(key,code,value,footprint,pins,kind='ic',note=''):
 d=json.loads((ROOT/'hardware/research'/f'{code}.json').read_text()) if code else {}
 assert not code or d.get('mpn'), (key,code)
 P[key]=dict(key=key,code=code,value=value,footprint=footprint,pins=pins,kind=kind,note=note,catalog=d)
def pins(names,types=None):return [(str(i+1),n,(types or {}).get(str(i+1),'passive')) for i,n in enumerate(names.split(','))]
rfoot='Resistor_SMD:R_0603_1608Metric';cfoot='Capacitor_SMD:C_0603_1608Metric'
for value,code in [('33','C23140'),('0','C21189'),('47','C23182'),('49.9','C23185'),('220','C22962'),('330','C23138'),('1.5k','C22843'),('5.1k','C23186'),('10k','C25804'),('12.4k','C22865'),('100k','C25803'),('510k','C23192'),('390k','C23150')]:part('R'+value,code,value+' 1%',rfoot,pins('~,~'),'r')
for value,code,foot in [('100n','C14663',cfoot),('1n','C1588',cfoot),('10n','C57112',cfoot),('6.8n','C1631',cfoot),('22n','C1729','Capacitor_SMD:C_0805_2012Metric'),('20p','C1648',cfoot),('1u','C15849',cfoot),('4.7u','C19666',cfoot),('10u','C15850','Capacitor_SMD:C_0805_2012Metric'),('22u','C45783','Capacitor_SMD:C_0805_2012Metric')]:part('C'+value,code,value,foot,pins('~,~'),'c')
part('npn','C20526','MMBT3904','Package_TO_SOT_SMD:SOT-23',pins('B,E,C'))
part('pmos','C15127','AO3401A','Package_TO_SOT_SMD:SOT-23',pins('G,S,D'))
part('diode','C2128','1N4148WS','Diode_SMD:D_SOD-323',pins('K,A'),'diode')
part('ssr','C4153843','TLP3122A(TPL,E','',[('1','A','passive'),('3','K','passive'),('4','OUT','passive'),('6','OUT','passive')],note='Toshiba 4-pin SO6; NOT generic SOP4. Land pattern pending manufacturer drawing review.')
part('opto','C42381015','EL357N(B)(TA)-G','Package_SO:SO-4_4.4x2.3mm_P1.27mm',pins('A,K,E,C'),note='Verify actual SOP4 2.54mm pin pitch against package drawing before PCB layout.')
# Correct the pin pitch for the 357 package (2.54 mm, body ~4.4 x 2.6); custom footprint pending dimensional review.
P['opto']['footprint']='';P['opto']['note']='Everlight pin map 1=A, 2=K, 3=E, 4=C; CTR B bin. Qualified input current/temperature margin needs prototype.'
part('cmp','C67470','LM393DR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',pins('OUT1,IN1-,IN1+,GND,IN2+,IN2-,OUT2,VCC',{'1':'open_collector','7':'open_collector','2':'input','3':'input','5':'input','6':'input','4':'power_in','8':'power_in'}))
part('iso','C20622559','B0505S-1WR3L','Rack:HENIPER_B0505S-1WR3L',pins('GND_IN,VIN,GND_ISO,VOUT_ISO',{'1':'power_in','2':'power_in','3':'power_out','4':'power_out'}))
part('ldo','C14289','HT7533-1','Package_TO_SOT_SMD:SOT-89-3',pins('GND,VIN,VOUT',{'1':'power_in','2':'power_in','3':'power_out'}))
part('port','C161672','S10B-PHDSS(LF)(SN)','Connector_JST:JST_PHD_S10B-PHDSS_2x05_P2.00mm_Horizontal',pins('PWR_A,PWR_B,RST_A,RST_B,PLED+,PLED-,HDD+,HDD-,HOST_REF,NC'))
part('esd','C2841440','PESD5V0S2BT','Package_TO_SOT_SMD:SOT-23',pins('IO1,IO2,GND'),note='TECH PUBLIC bidirectional dual TVS; verify pin 3 common on vendor drawing.')
part('hc595','C5947','74HC595D,118','Package_SO:SOIC-16_3.9x9.9mm_P1.27mm',pins('QB,QC,QD,QE,QF,QG,QH,GND,QH_SER,MR_N,SHCP,STCP,OE_N,DS,QA,VCC',{**{str(i):'output' for i in [1,2,3,4,5,6,7,9,15]},**{str(i):'input' for i in [10,11,12,13,14]},'8':'power_in','16':'power_in'}))
part('timer','C6986','TLC555CDR','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',pins('GND,TRIG,OUT,RESET_N,CTRL,THRESH,DISCH,VCC',{'1':'power_in','2':'input','3':'output','4':'input','5':'passive','6':'input','7':'open_collector','8':'power_in'}))
part('buck','C780769','AP63203WU-7','Package_TO_SOT_SMD:TSOT-23-6',pins('FB,EN,VIN,GND,SW,BST',{'1':'input','2':'input','3':'power_in','4':'power_in','5':'power_out','6':'passive'}))
part('ind','C167806','4.7uH FNR4018S4R7MT','Inductor_SMD:L_Sunlord_MWSA0402_4.2x4.0mm',pins('~,~'),'l',note='Confirm FNR4018 pad geometry; assigned footprint is size reference only.')
part('fuse','C78695','MF-MSMF150/24X-2 1.5A','Fuse:Fuse_1812_4532Metric',pins('~,~'),'r')
part('barrel','C8465','WJ500V-5.08-2P','',pins('+5V,GND'),note='5 V regulated only, 2 A external supply; screw terminal pin 1 positive, pin 2 GND. Supply separately sourced.')
part('xtal40','C18214314','40MHz CL12pF','Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',pins('X1,GND,X2,GND'))
part('xtal25','C9006','25MHz CL12pF','Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',pins('X1,GND,X2,GND'))
part('bead','C12391','120R@100MHz GZ1608D121TF','Inductor_SMD:L_0603_1608Metric',pins('~,~'),'l')
part('usb','C165948','TYPE-C-31-M-12','Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',[(x,x,'passive') for x in ['A1','A4','A5','A6','A7','A8','A9','A12','B1','B4','B5','B6','B7','B8','B9','B12','SH']])
part('usbesd','C12333','PRTR5V0U2X,215','Package_TO_SOT_SMD:SOT-143',pins('GND,IO1,IO2,VCC'))
part('rj45','C12074','HR911105A','Connector_RJ:RJ45_Hanrun_HR911105A_Horizontal',pins('TD+,TD-,RD+,TCT,RCT,RD-,NC,CHS_GND,LED_G_A,LED_G_K,LED_Y_K,LED_Y_A')+[('SH','SHIELD','passive')])
# Pin numbers transcribed from vendor datasheets; NC does not mean internally absent.
s=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/MCU_Espressif.kicad_sym').read_text();i=s.index('(symbol "ESP32-S3"');j=s.index('\n\t(symbol ',i+10)
mpins=[(num,name,typ) for typ,name,num in re.findall(r'\(pin (\w+) .*?\(name "([^"]+)".*?\(number "([^"]+)"',s[i:j],re.S)]
mpins=[(n,nm,'power_out' if n=='29' else t) for n,nm,t in mpins]
part('mcu','C2913196','ESP32-S3FN8','Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm',mpins)
wnames='TXN,TXP,AGND,AVDD,RXN,RXP,DNC,AVDD,AGND,EXRES1,AVDD,NC,NC,AGND,AVDD,AGND,AVDD,VBG,AGND,TOCAP,AVDD,1V2O,RSVD,SPDLED,LINKLED,DUPLED,ACTLED,VDD,GND,XI,XO,CS_N,SCLK,MISO,MOSI,INT_N,RST_N,RSVD,RSVD,RSVD,RSVD,RSVD,PMODE2,PMODE1,PMODE0,NC,NC,AGND'
wp=pins(wnames,{**{str(i):'power_in' for i in [3,4,8,9,11,14,15,16,17,19,21,28,29,48]},**{str(i):'input' for i in [5,6,23,30,32,33,35,37,43,44,45]},**{str(i):'output' for i in [1,2,18,20,22,24,25,26,27,31]},'34':'tri_state','36':'open_collector'})
part('eth','C32843','W5500','Package_QFP:LQFP-48_7x7mm_P0.5mm',wp)
part('flag',None,'POWER SOURCE','', [('1','PWR','power_out')],'flag')
# Same stocked two-pin header for the controller debug jumpers and passive adapters.
part('header2','C492401','PZ254V-11-02P','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',pins('1,2'))
# Explicitly leave unreviewed land patterns unassigned. Package/MPN remain in the
# procurement BOM; assigning a similar but incompatible footprint would be worse.
for key in ['opto','iso','barrel','ind']:
 P[key]['note'] += ' PCB footprint must be created/reviewed from the manufacturer drawing before layout release.'
 P[key]['footprint']=''

components=[]; sheets={}; seq=defaultdict(int); sheet=''
def page(name,title,notes):
 global sheet
 sheet=name;sheets[name]={'title':title,'notes':notes}
def add(key,nets,ref=None,section=''):
 p=P[key];prefix='R' if p['kind']=='r' and key!='fuse' else 'C' if p['kind']=='c' else 'L' if p['kind']=='l' else 'Q' if key in ['npn','pmos'] else 'D' if key in ['diode','esd','usbesd'] else 'J' if key in ['port','barrel','usb','rj45','header2'] else 'Y' if key.startswith('xtal') else 'F' if key=='fuse' else '#FLG' if key=='flag' else 'U'
 if ref is None:seq[prefix]+=1;ref=prefix+str(seq[prefix])
 if not isinstance(nets,dict):nets={pn:net for (pn,_,_),net in zip(p['pins'],nets)}
 assert set(nets)=={pn for pn,_,_ in p['pins']},(ref,set(nets),p['pins'])
 c=dict(ref=ref,key=key,sheet=sheet,nets=nets,section=section);components.append(c);return ref
def r(v,a,b,**kw):return add('R'+v,[a,b],**kw)
def cap(v,a,b,**kw):return add('C'+v,[a,b],**kw)
def flag(n):return add('flag',[n])
G='GND_CTRL';V='3V3';V5='5V'
page('power','5 V input, protection and 3.3 V buck','Regulated 5 V +/-5%, 2 A, terminal 1 positive. USB VBUS is NOT a power input.\nCheck PCB thermal/current loops and external PSU before energizing.')
add('barrel',['5V_JACK',G],ref='J101');add('fuse',['5V_JACK','5V_FUSED']);add('pmos',[G,V5,'5V_FUSED']);flag(G);flag('5V_JACK');flag('5V_FUSED');flag(V5);flag(V)
cap('10u',V5,G);cap('100n',V5,G)
add('buck',[V,V5,V5,G,'BUCK_SW','BUCK_BST']);cap('100n','BUCK_BST','BUCK_SW');add('ind',['BUCK_SW',V]);cap('22u',V,G);cap('22u',V,G)
page('processor','ESP32-S3FN8 / USB programming','Wired Ethernet only. Leave LNA_IN open and never initialize Wi-Fi/BLE.\nGPIO26..32 used by internal quad flash: do not route. GPIO45 pulled low selects 3.3 V flash.')
# GPIO numbers -> physical package pins
mapping={0:5,1:6,2:7,3:8,**{i:i+5 for i in range(4,15)},15:21,16:22,17:23,18:24,19:25,20:26,21:27,33:38,34:39,35:40,36:41,37:42,38:43,39:44,40:45,41:47,42:48,43:49,44:50,45:51,46:52,47:36,48:37}
mn={n:None for n,_,_ in mpins}
for n in ['2','3','20','46','55','56']:mn[n]=V
mn['57']=G;mn['4']='EN';mn['29']='VDD_SPI';mn['53']='MCU_XN';mn['54']='MCU_XP'
gpio={0:'BOOT_N',1:'OUT_LATCH',2:'OUT_OE_N',19:'USB_DM_MCU',20:'USB_DP_MCU',33:'USB_VBUS_SENSE',39:'SPI_SCK_RAW',40:'SPI_MOSI_RAW',41:'SPI_MISO',42:'ETH_CS_N',43:'TIMER_ARM',44:'TIMER_FIRE',45:'STRAP45',46:'STRAP46',47:'ETH_RST_N',48:'ETH_INT_N'}
ledgp=list(range(4,19))+[21,35,36,37,38]
for idx,g in enumerate(ledgp):gpio[g]=f'H{idx//2+1:02}_'+('PLED_N' if idx%2==0 else 'HDD_N')
for g,n in gpio.items():mn[str(mapping[g])]=n
add('mcu',mn);cap('100n','VDD_SPI',G);cap('1u','VDD_SPI',G)
for _ in range(6):cap('100n',V,G)
cap('10u',V,G);cap('10u',V,G);r('10k',V,'EN');cap('1u','EN',G);r('10k',V,'BOOT_N');r('10k','STRAP45',G);r('10k','STRAP46',G)
add('header2',['EN',G],ref='J102');add('header2',['BOOT_N',G],ref='J103')
add('xtal40',['MCU_XP_CR',G,'MCU_XN',G]);r('0','MCU_XP','MCU_XP_CR');cap('20p','MCU_XP_CR',G);cap('20p','MCU_XN',G)
r('47','SPI_SCK_RAW','SPI_SCK');r('47','SPI_MOSI_RAW','SPI_MOSI')
usb={n:G if n in ['A1','A12','B1','B12','SH'] else 'USB_VBUS' if n in ['A4','A9','B4','B9'] else 'USB_DP' if n in ['A6','B6'] else 'USB_DM' if n in ['A7','B7'] else 'USB_CC1' if n=='A5' else 'USB_CC2' if n=='B5' else None for n,_,_ in P['usb']['pins']}
add('usb',usb,ref='J104');add('usbesd',[G,'USB_DM','USB_DP','USB_VBUS']);r('5.1k','USB_CC1',G);r('5.1k','USB_CC2',G);r('33','USB_DM','USB_DM_MCU');r('33','USB_DP','USB_DP_MCU');r('100k','USB_VBUS','USB_VBUS_SENSE');r('100k','USB_VBUS_SENSE',G)
page('ethernet','W5500 / HR911105A Ethernet','WIZnet RJ45 reference topology. HR911105A pin numbering differs from J1B1211CCD.\n100-ohm differential MDI routing; crystal load caps need final frequency measurement.')
wn={str(i):None for i in range(1,49)}
for i in [3,9,14,16,19,23,29,48]:wn[str(i)]=G
for i in [4,8,11,15,17,21]:wn[str(i)]='3V3_ETH_A'
for i in [28,43,44,45]:wn[str(i)]=V
wn.update({str(k):v for k,v in {1:'ETH_TXN',2:'ETH_TXP',5:'ETH_RXN',6:'ETH_RXP',10:'ETH_EXRES',20:'ETH_TOCAP',22:'ETH_1V2',25:'ETH_LINK_N',27:'ETH_ACT_N',30:'ETH_XI',31:'ETH_XO',32:'ETH_CS_N',33:'SPI_SCK',34:'SPI_MISO',35:'SPI_MOSI',36:'ETH_INT_N',37:'ETH_RST_N'}.items()})
add('eth',wn);add('bead',[V,'3V3_ETH_A']);flag('3V3_ETH_A');r('12.4k','ETH_EXRES',G);cap('4.7u','ETH_TOCAP',G);cap('10n','ETH_1V2',G)
for _ in range(6):cap('100n','3V3_ETH_A',G)
cap('10u','3V3_ETH_A',G);cap('100n',V,G);cap('10u',V,G)
r('10k',V,'ETH_CS_N');r('10k',V,'ETH_INT_N');r('10k',V,'ETH_RST_N');cap('1u','ETH_RST_N',G)
add('xtal25',['ETH_XI',G,'ETH_XO',G]);cap('20p','ETH_XI',G);cap('20p','ETH_XO',G)
r('49.9','ETH_TXP','3V3_ETH_A');r('49.9','ETH_TXN','3V3_ETH_A');r('49.9','ETH_RXP','ETH_RX_TERM');r('49.9','ETH_RXN','ETH_RX_TERM');cap('10n','ETH_RX_TERM',G)
# Series receive AC coupling in WIZnet reference. TX centre-tap is AC-bypassed to GND.
cap('6.8n','ETH_RXP','RJ_RD_P');cap('6.8n','ETH_RXN','RJ_RD_N');cap('22n','RJ_TX_CT',G)
r('330',V,'RJ_LED_G_A');r('330',V,'RJ_LED_Y_A')
add('rj45',['ETH_TXP','ETH_TXN','RJ_RD_P','RJ_TX_CT','ETH_RX_TERM','RJ_RD_N',None,G,'RJ_LED_G_A','ETH_LINK_N','ETH_ACT_N','RJ_LED_Y_A','CHASSIS'],ref='J105')
r('0','CHASSIS',G)
page('outputs','Output latches / timed drive rail','595 stores 20 output bits; unused 4 outputs not connected. Shift 24 zeros before OE low.\nSPI traffic shifts internal register only; latch ONLY after a complete output frame. Never latch Ethernet data.\nTimer: nominal 16.8 s, qualify 8..25 s with capacitor bias/tolerance. Firmware long press 5 s.\nOne command at a time. Repeated trigger edges can extend a 555 pulse: firmware is not a safety-rated system.')
for bank in range(3):
 base=bank*8;outs=[f'DRV_{n+1:02}' if n<20 else None for n in range(base,base+8)]
 add('hc595',[*outs[1:],G,f'SHIFT_{bank+1}' if bank<2 else None,'EN','SPI_SCK','OUT_LATCH','OUT_OE_N','SPI_MOSI' if bank==0 else f'SHIFT_{bank}',outs[0],V]);cap('100n',V,G)
r('10k',V,'OUT_OE_N');r('100k','OUT_LATCH',G);r('100k','TIMER_ARM',G);r('100k','TIMER_FIRE',G)
# AC-coupled trigger cannot remain active merely because the MCU pin is stuck high.
cap('100n','TIMER_FIRE','TRIG_AC');r('10k','TRIG_AC','TRIG_BASE');r('10k','TRIG_BASE',G);add('diode',['TRIG_BASE',G]);add('npn',['TRIG_BASE',G,'TRIG_N']);r('10k',V5,'TRIG_N')
add('timer',[G,'TRIG_N','TIMER_OUT','TIMER_ARM','TIMER_CTRL','TIMER_RC','TIMER_RC',V5]);cap('10n','TIMER_CTRL',G);cap('100n',V5,G);r('510k',V5,'TIMER_RC')
for _ in range(3):cap('10u','TIMER_RC',G)
r('10k','TIMER_OUT','GATE_BASE');r('100k','GATE_BASE',G);add('npn',['GATE_BASE',G,'PHOTO_GATE']);r('10k','PHOTO_GATE',V5);add('pmos',['PHOTO_GATE',V5,'PHOTO_5V']);r('10k','PHOTO_5V',G);flag('PHOTO_5V')
for h in range(1,11):
 H=f'H{h:02}';HG=H+'_GND';HV=H+'_3V3';HR=H+'_RAW5'
 page('host'+str(h).zfill(2),f'Host {h:02}: isolated controls / LEDs','All HOST_REF and ESD grounds on this sheet belong only to this host.\nCase buttons and LEDs remain straight-through on passive adapter. No host power is supplied on the cable.\nLED input envelope: 0..5 V common-mode; OFF differential <=0.2 V; ON >=1.4 V. Qualify actual motherboard.\nLM393 inputs tolerate positive voltage with VCC=0; 100k series limits signal loading. Not a universal F_PANEL map.')
 ns=[H+'_'+x for x in ['PWR_A','PWR_B','RST_A','RST_B','PLED_P','PLED_M','HDD_P','HDD_M']]+[HG,None]
 add('port',ns,ref='J'+str(h).zfill(2));add('iso',[G,V5,HG,HR]);cap('4.7u',V5,G);cap('10u',HR,HG);add('ldo',[HG,HR,HV]);cap('10u',HV,HG);cap('100n',HV,HG)
 # Modest bleeder ensures the isolated rail discharges and has a defined light load. Module permits 0% load; LDO rated 30V.
 r('10k',HV,HG)
 for k,pair in enumerate([('PWR_A','PWR_B'),('RST_A','RST_B')]):
  pre='CTRL_'+H+('_PWR' if k==0 else '_RST');out=f'DRV_{(h-1)*2+k+1:02}'
  r('1.5k',out,pre+'_B');r('100k',pre+'_B',G);add('npn',[pre+'_B',G,pre+'_K']);r('220','PHOTO_5V',pre+'_R');r('220',pre+'_R',pre+'_A');add('ssr',[pre+'_A',pre+'_K',H+'_'+pair[0],H+'_'+pair[1]])
 for k in range(4):add('esd',[ns[2*k],ns[2*k+1],HG])
 cp=[]
 for sig in ['PLED','HDD']:
  pre=H+'_'+sig;ip=pre+'_SPLUS';im=pre+'_SMINUS';o=pre+'_CMP'
  r('100k',pre+'_P',ip);r('10k',ip,HG);cap('1n',ip,HG)
  r('100k',pre+'_M',im);r('10k',im,HG);cap('1n',im,HG);r('390k',HV,im);r('510k',o,pre+'_FB1');r('510k',pre+'_FB1',pre+'_FB2');r('510k',pre+'_FB2',pre+'_FB3');r('510k',pre+'_FB3',im)
  r('10k',HV,o);r('330',HV,pre+'_OR');r('330',pre+'_OR',pre+'_OA');add('opto',[pre+'_OA',o,G,pre+'_N']);r('10k',V,pre+'_N');cap('1n',pre+'_N',G)
  cp.append([o,ip,im])
 add('cmp',[*cp[0],HG,cp[1][2],cp[1][1],cp[1][0],HV])
page('adapter','Passive host adapter','Build 10 identical copies. This board has no active parts and no power supply.\n2.54 mm pairs are labelled by function, not motherboard physical pin number. Connect by motherboard manual.\nPin 9 goes to separately verified host signal ground. Pin 10 stays NC at both cable ends.\nTo save a separate PCBA setup: order bare PCBs and hand-solder connectors, or substitute a crimped Y harness.')
add('port',['PWR_A','PWR_B','RST_A','RST_B','PLED_P','PLED_M','HDD_P','HDD_M','HOST_REF',None],ref='JA1')
for idx,(a,b) in enumerate([('PWR_A','PWR_B'),('RST_A','RST_B'),('PLED_P','PLED_M'),('HDD_P','HDD_M')]):
 add('header2',[a,b],ref='JA'+str(idx+2));add('header2',[a,b],ref='JA'+str(idx+6))
add('header2',['HOST_REF',None],ref='JA10')

# CAD generator: separate, labelled functional sheets. Pin types are preserved for ERC.
rootid=uid('root');adid=uid('adapter-root')
def library(key):
 p=P[key];ps=p['pins'];kind=p['kind'];lib='Rack:'+key
 n=math.ceil(len(ps)/2);step=2.54;half=max(2.54,(n+1)*step/2)
 if kind=='flag':locs=[(0,0,90)]
 elif kind in ['r','c','l','diode']:locs=[(-5.08,0,0),(5.08,0,180)];half=1.27
 else:locs=[(-15.24,((n-1)/2-i)*step,0) for i in range(n)]+[(15.24,((n-1)/2-i)*step,180) for i in range(len(ps)-n)]
 graphics=''
 if kind=='c':
  graphics=''.join(f'(polyline (pts (xy {xx} -1.5)(xy {xx} 1.5))(stroke(width 0.254)(type default))(fill(type none)))' for xx in [-.6,.6])
 elif kind=='flag':graphics='(polyline (pts(xy 0 0)(xy 0 2.54)(xy 1.27 1.27)(xy 0 0))(stroke(width 0.254)(type default))(fill(type none)))'
 else:
  hw=2.54 if kind in ['r','l','diode'] else 12.7
  graphics=f'(rectangle (start {-hw} {half})(end {hw} {-half})(stroke(width 0.254)(type default))(fill(type none)))'
  if kind=='diode':graphics+='(text "K" (at -1 0 0)(effects(font(size 1 1))))'
 sg=f'(symbol {q(lib)} (pin_names (offset 1.016){" (hide yes)" if kind in ["r","c","l","diode","flag"] else ""}) (exclude_from_sim no)(in_bom yes)(on_board yes) (property "Reference" "U" (at 0 0 0)(effects(font(size 1.27 1.27)))) (property "Value" {q(p["value"])} (at 0 0 0)(effects(font(size 1.27 1.27)))) (symbol {q(key+"_0_1")} {graphics}) (symbol {q(key+"_1_1")} '
 for (num,name,typ),(x,y,ang) in zip(ps,locs):
  length=0 if kind=='flag' else 4.48 if kind=='c' else 2.54
  sg+=f'(pin {typ} line (at {x} {y} {ang})(length {length})(name {q(name)}(effects(font(size 1.016 1.016))))(number {q(num)}(effects(font(size 1.016 1.016)))))'
 return sg+'))',locs,half

def schematic(name,items,title,notes,root=False):
 parent=adid if name=='adapter' else rootid; sid=parent if root else uid('sheet:'+name)
 data=f'(kicad_sch (version 20250114)(generator "eeschema")(uuid {sid})(paper "A3")(title_block (title {q(title)})(rev {q(REV)})(company "Rack ATX Controller / ddasdkimo")(comment 1 "SCHEMATIC REVIEW - not a fabrication release"))\n(lib_symbols\n'
 for k in sorted({c['key'] for c in items}):data+=library(k)[0]+'\n'
 data+=')\n'
 def txt(t,x,y,size=1.27):return f'(text {q(t)}(at {x} {y} 0)(effects(font(size {size} {size}))(justify left))(uuid {uid(name+str(x)+str(y)+t)}))\n'
 data+=txt(notes,12,20)
 # Larger devices on first row, remaining parts in compact 5-column rows. All labels are real KiCad global nets.
 large=[c for c in items if len(P[c['key']]['pins'])>16]
 small=[c for c in items if c not in large]
 x=55;y=55;maxh=0;poses=[]
 for c in large:
  _,_,hh=library(c['key']);poses.append((c,x,y+hh));x+=110;maxh=max(maxh,2*hh+18)
 ystart=55+maxh if large else 50
 # 4 columns provide room for readable net names. Auto-flow with per-row height.
 rows=[];row=[]
 for c in small:
  row.append(c)
  if len(row)==4:rows.append(row);row=[]
 if row:rows.append(row)
 yy=ystart
 for row in rows:
  heights=[2*library(c['key'])[2]+17 for c in row];hh=max(heights)
  for ix,c in enumerate(row):poses.append((c,46+ix*100,yy+hh/2))
  yy+=hh
 if yy>260: # Split component sheets before calling rather than silently spilling off-page.
  raise ValueError((name,'sheet too tall',yy))
 for c,x,y in poses:
  x=round(round(x/1.27)*1.27,4);y=round(round(y/1.27)*1.27,4)
  p=P[c['key']];lib,locs,half=library(c['key']);ref=c['ref'];inst=uid(ref);path='/'+parent if root else '/'+rootid+'/'+uid('sheet:'+name)
  data+=f'(symbol(lib_id {q("Rack:"+c["key"])})(at {x} {y} 0)(unit 1)(exclude_from_sim no)(in_bom {"no" if c["key"]=="flag" else "yes"})(on_board {"no" if c["key"]=="flag" else "yes"})(dnp no)(uuid {inst})'
  for field,value,dy,hide in [('Reference',ref,-half-5,False),('Value',p['value'],-half-2.5,False),('Footprint',p['footprint'],0,True),('LCSC',p['code'] or '',0,True),('MPN',p['catalog'].get('mpn') or p['value'],0,True)]:
   data+=f'(property {q(field)} {q(value)}(at {x} {y+dy} 0)(effects(font(size 1.016 1.016)){"(hide yes)" if hide else ""}))'
  for num,_,_ in p['pins']:data+=f'(pin {q(num)}(uuid {uid(ref+"/pin/"+num)}))'
  data+=f'(instances(project "rack-atx-controller"(path {q(path)}(reference {q(ref)})(unit 1)))))\n'
  for (num,_,_),(dx,dy,ang) in zip(p['pins'],locs):
   px=round(x+dx,4);py=round(y-dy,4);net=c['nets'][num]
   if net is None:data+=f'(no_connect(at {px} {py})(uuid {uid(ref+"/nc/"+num)}))\n';continue
   side=-1 if dx<=0 else 1;ex=round(px+side*2.54,4)
   data+=f'(wire(pts(xy {px} {py})(xy {ex} {py}))(stroke(width 0)(type default))(uuid {uid(ref+"/wire/"+num)}))\n'
   # Local labels suffice inside adapter; global labels connect controller sheets.
   data+=f'(global_label {q(net)}(shape bidirectional)(at {ex} {py} {180 if side<0 else 0})(effects(font(size 1.016 1.016))(justify {"right" if side<0 else "left"}))(uuid {uid(ref+"/label/"+num)})(property "Intersheetrefs" "${{INTERSHEET_REFS}}"(at {ex} {py} 0)(effects(font(size 1 1))(hide yes))))\n'
 return data+')\n'

# One dense page is split into IC/analog stages as needed without changing nets.
# Use up to 24 small symbols per sheet to remain legible; host channels get two sheets.
finals={}
for name,meta in list(sheets.items()):
 cs=[c for c in components if c['sheet']==name]
 if name=='adapter':finals[name]=(meta,cs);continue
 large=[c for c in cs if len(P[c['key']]['pins'])>16]
 small=[c for c in cs if c not in large]
 chunks=[]
 if large:chunks.append(large+small[:8]);small=small[8:]
 while small:chunks.append(small[:24]);small=small[24:]
 for idx,chunk in enumerate(chunks):
  nm=name if len(chunks)==1 else name+'_'+str(idx+1)
  finals[nm]=({**meta,'title':meta['title']+(f' ({idx+1}/{len(chunks)})' if len(chunks)>1 else '')},chunk)
  for c in chunk:c['sheet']=nm
for name,(meta,cs) in finals.items():
 (OUT/(name+'.kicad_sch')).write_text(schematic(name,cs,meta['title'],meta['notes'],root=name=='adapter'))
# Store the editable project symbol library as well as each sheet's cache.
(OUT/'Rack.kicad_sym').write_text('(kicad_symbol_lib (version 20241209)(generator "kicad_symbol_editor")\n'+'\n'.join(library(k)[0].replace(q('Rack:'+k),q(k),1) for k in sorted(P))+')\n')
for project in ['rack-atx-controller','adapter']:
 (OUT/(project+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':project+'.kicad_pro','version':1}},indent=2)+'\n')
(OUT/'sym-lib-table').write_text('(sym_lib_table (lib (name "Rack")(type "KiCad")(uri "${KIPRJMOD}/Rack.kicad_sym")(options "")(descr "Rack ATX schematic symbols")))\n')
# Root hierarchy, separate adapter schematic is not included in central-board BOM/netlist.
root=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid {rootid})(paper "A3")(title_block(title "10-host rack ATX controller")(rev "B.1")(comment 1 "SCHEMATIC REVIEW - no PCB routing or Gerber release"))(lib_symbols)'
root+='(text "5 V input -> 3.3 V logic / ten isolated host supplies\\nESP32-S3FN8 + W5500 -> three 74HC595 -> twenty isolated dry contacts\\nTwenty differential LED detectors -> twenty isolated returns -> MCU GPIO\\nOriginal case wiring bypasses this controller on passive adapters" (at 15 18 0)(effects(font(size 2 2))(justify left))(uuid '+uid('rootnote')+'))'
for idx,(name,(meta,_)) in enumerate((x for x in finals.items() if x[0]!='adapter')):
 x=15+(idx%4)*100;y=52+(idx//4)*23
 root+=f'(sheet(at {x} {y})(size 85 14)(stroke(width .254)(type default))(fill(color 0 0 0 0))(uuid {uid("sheet:"+name)})(property "Sheetname" {q(meta["title"])}(at {x} {y-2} 0)(effects(font(size 1 1))(justify left)))(property "Sheetfile" {q(name+".kicad_sch")}(at {x} {y+16} 0)(effects(font(size 1 1))(justify left)))(instances(project "rack-atx-controller"(path "/{rootid}"(page "{idx+2}")))))'
root+=f'(sheet_instances(path "/"(page "1"))))'
(OUT/'rack-atx-controller.kicad_sch').write_text(root)
(ROOT/'hardware/circuit.json').write_text(json.dumps({'revision':REV,'parts':P,'components':components,'gpio':gpio,'sheets':{n:m for n,(m,_) in finals.items()}},ensure_ascii=False,indent=2)+'\n')
# Procurement groups and JLC format. Board-specific physical refdes never refer to virtual host adapters.
for board in ['controller','adapter']:
 cs=[c for c in components if (c['sheet']=='adapter')==(board=='adapter') and c['key']!='flag']
 groups=defaultdict(list)
 for c in cs:groups[c['key']].append(c['ref'])
 rows=[];jrows=[]
 for key,refs in groups.items():
  p=P[key];d=p['catalog'];rows.append([','.join(refs),len(refs),p['value'],d.get('manufacturer',''),d.get('mpn',p['value']),p['code'] or '',d.get('package','2.54mm THT'),p['footprint'],d.get('classification','External / hand assembly'),d.get('assembly','Hand assembly'),d.get('pcba_type',''),d.get('stock',''),d.get('checked_at',''),d.get('source',''),p['note']])
  if p['code']:jrows.append([p['value'],','.join(refs),p['footprint'] or d.get('package',''),p['code']])
 for filename,head,rs in [(f'{board}-bom.csv',['Designator','Quantity per board','Comment','Manufacturer','MPN','LCSC Part #','Package','Footprint candidate','Library class','Assembly','PCBA mode','Observed stock','Checked at UTC','Source','Notes'],rows),(f'{board}-jlc-bom.csv',['Comment','Designator','Footprint','LCSC Part #'],jrows)]:
  with (ROOT/'hardware/bom'/filename).open('w',newline='') as f:w=csv.writer(f);w.writerow(head);w.writerows(rs)
print('Generated',len(components),'symbols,',len(finals)+1,'schematic sheets,',len(P),'part definitions')
