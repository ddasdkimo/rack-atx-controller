#!/usr/bin/env python3
"""Configure the local Freerouting trial. Native KiCad DRC remains authoritative.
This tool does not qualify differential impedance, power current or return paths.
"""
from pathlib import Path
import re,json,sys
R=Path(__file__).resolve().parents[1]
s=(R/'artifacts/local/R1.dsn').read_text()
a=s.index('    (class kicad_default ');end=s.index('\n  )\n  (wiring',a)
nets=s[a:s.index('(circuit',a)].split()[2:]
groups={'Ground':[], 'Power5V':[], 'Power3V3':[], 'Signal':[], 'Fine':[], 'Critical':[]}
critical={'MCU_XN','MCU_XP','MCU_XP_CR','ETH_XI','ETH_XO','USB_DP','USB_DM','USB_DP_MCU','USB_DM_MCU','ETH_TXP','ETH_TXN','ETH_RXP','ETH_RXN','RJ_RD_P','RJ_RD_N','BUCK_SW','BUCK_BST'}
fine={'SPI_MISO','SPI_MOSI','SPI_MOSI_RAW','SPI_SCK','SPI_SCK_RAW','OUT_LATCH','OUT_OE_N','EN','BOOT_N','STRAP45','STRAP46','ETH_CS_N','ETH_RST_N','ETH_INT_N','TIMER_ARM','TIMER_FIRE','USB_VBUS_SENSE','VDD_SPI'}
for n in nets:
 key='Ground' if n=='GND_CTRL' or re.fullmatch('H[0-9]{2}_GND',n) else 'Critical' if n in critical else 'Power5V' if n in ['5V','5V_FUSED','5V_JACK','PHOTO_5V'] else 'Power3V3' if n in ['3V3','3V3_ETH_A'] or re.fullmatch('H[0-9]{2}_(3V3|RAW5)',n) else 'Fine' if n in fine or re.fullmatch('H[0-9]{2}_(PLED_N|HDD_N)',n) else 'Signal'
 groups[key].append(n)
width={'Ground':250,'Power5V':800,'Power3V3':400,'Signal':250,'Fine':150,'Critical':150}
# Optional completion pass uses narrow branches; existing power trunks stay protected.
if '--neckdown' in sys.argv:width.update(Power3V3=150,Power5V=250)
classes=''
for k,ns in groups.items():
 classes+=f'    (class {k} '+ ' '.join(ns)+f'\n (circuit (use_via "Via[0-1]_600:300_um")) (rule (width {width[k]}) (clearance 200)))\n'
s=s[:a]+classes+s[end:]
# KiCad DSN serializes this pour-only area as a track keepout. Remove only
# that interchange restriction; the native board retains the no-pour area.
s,nremoved=re.subn(r'    \(keepout "" \(polygon [FB]\.Cu 0  0 -67000  22300 -67000  22300 -85000  0 -85000  0 -67000\)\)\n','',s)
assert nremoved==2,('Unexpected RJ45 interchange geometry',nremoved)
# Preserve ground/critical copper. Let the router optimize ordinary signals.
offset=s.index('  (wiring\n')
def protect(match):
 text=match.group(0);net=re.search(r'\(net ([^)]+)\)',text).group(1)
 return text.replace('(type route)','(type protect)') if net in groups['Ground']+groups['Critical'] or '--protect-all' in sys.argv else text
s=s[:offset]+re.sub(r'    \((?:wire|via) .*?\(type route\)\)',protect,s[offset:],flags=re.S)
(R/'artifacts/local/R1-configured.dsn').write_text(s)
(R/'hardware/routing-R1-constraints.json').write_text(json.dumps(dict(router='Freerouting 1.9.0',groups=groups,width_um=width,clearance_um=200,excluded_classes=['Ground','Critical'],note='Power widths are initial routing constraints, not final current/voltage-drop signoff. Fine-pitch neckdown is checked in native DRC. Critical nets handled separately.'),indent=2)+'\n')
