#!/usr/bin/env python3
from pathlib import Path
import wx,re,shutil,json
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/'artifacts/local/B2-critical.kicad_pcb';b=p.LoadBoard(str(src))
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(R/('hardware/cad/B2/rack-atx-controller'+ext),src.with_suffix(ext))
p.ExportSpecctraDSN(b,str(R/'artifacts/local/B2-seeded.dsn'))
s=(R/'artifacts/local/B2-seeded.dsn').read_text();a=s.index('    (class kicad_default ');end=s.index('\n  )\n  (wiring',a);nets=s[a:s.index('(circuit',a)].split()[2:]
power=[n for n in nets if n in ['5V','3V3','5V_JACK','5V_FUSED','PHOTO_5V']];fine=[n for n in nets if n.startswith(('ETH_','USB_','MCU_','SPI_'))];signal=[n for n in nets if n not in power+fine]
classes=''
for name,ns,w in [('Power',power,300),('Fine',fine,150),('Signal',signal,200)]:classes+=f'    (class {name} '+ ' '.join(ns)+f' (circuit (use_via "Via[0-1]_600:300_um")) (rule (width {w}) (clearance 150)))\n'
s=s[:a]+classes+s[end:];s=s.replace('(type route)','(type protect)');(R/'artifacts/local/B2-seeded.dsn').write_text(s)
