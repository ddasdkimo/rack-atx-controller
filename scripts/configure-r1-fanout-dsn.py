#!/usr/bin/env python3
"""Preserve audited local escapes while joining ordinary routes."""
from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
s=(R/'artifacts/local/R1-mcu-fanout.dsn').read_text();c=(R/'artifacts/local/R1-core-fine.dsn').read_text()
a=s.index('    (class kicad_default ');z=s.index('\n  )\n  (wiring',a);a2=c.index('    (class Ground ');z2=c.index('\n  )\n  (wiring',a2);s=s[:a]+c[a2:z2]+s[z:];s=s.replace('(clearance 200)','(clearance 150)')
s=re.sub(r'    \(keepout "" \(polygon [FB]\.Cu 0  0 -67000  22300 -67000  22300 -85000  0 -85000  0 -67000\)\)\n','',s)
critical=set('BUCK_SW BUCK_BST MCU_XN MCU_XP MCU_XP_CR ETH_XI ETH_XO USB_DM_MCU USB_DP_MCU'.split())
def protect(m):
 t=m.group();n=re.search(r'\(net ([^)]+)\)',t).group(1);nums=[]
 if t.lstrip().startswith('(wire'):
  coords=re.search(r'\(path [FB]\.Cu [\d.]+\s+([^)]*)\)',t).group(1);nums=list(map(float,coords.split()))
 else:
  q=re.search(r'_um" ([\d.-]+) ([\d.-]+)',t);nums=list(map(float,q.groups())) if q else []
 local=nums and all(28800<x<39000 and -102000<y<-92100 for x,y in zip(nums[::2],nums[1::2]))
 return t.replace('(type route)','(type protect)') if n in critical or local else t
start=s.index('  (wiring\n');s=s[:start]+re.sub(r'    \((?:wire|via) .*?\(type route\)\)',protect,s[start:],flags=re.S)
(R/'artifacts/local/R1-mcu-fanout-configured.dsn').write_text(s)
print('Protected escapes',s.count('(type protect)'))
