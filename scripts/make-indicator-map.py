#!/usr/bin/env python3
"""Readable indicator-position map from the active native-placement manifest."""
import json,html
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'hardware/design.json').read_text());cs=d['layout_study']['components']
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 850"><style>text{font-family:Arial,"PingFang TC",sans-serif;fill:#e7f3ed}.small{font-size:15px}.led{font-size:13px}.note{font-size:19px}.title{font-size:29px;font-weight:700}</style><rect width="1160" height="850" fill="#10241e"/>']
def txt(x,y,t,cl='note',anchor='start',color=None):
 s.append(f'<text x="{x}" y="{y}" class="{cl}" text-anchor="{anchor}"'+(f' style="fill:{color}"' if color else '')+'>'+html.escape(t)+'</text>')
txt(42,55,'R.2 狀態燈位置｜PCB 正面俯視','title')
txt(42,88,'100 × 110 mm · 位置依原生佈局；亮色用於定位，不代表目前真的在操作','small')
ox,oy,k=54,140,5.8
s.append(f'<rect x="{ox}" y="{oy}" width="{100*k}" height="{110*k}" rx="5" fill="#1a4334" stroke="#85b99f" stroke-width="2"/>')
for c in cs:
 x,y,w,h=[c[z] for z in ['x','y','w','h']]
 if c['key'] in ['ledred','ledgreen']:continue
 s.append(f'<rect x="{ox+x*k:.2f}" y="{oy+y*k:.2f}" width="{w*k:.2f}" height="{h*k:.2f}" fill="#1b2c26" stroke="#527967" stroke-width=".6"/>')
 if c['key']=='port':txt(ox+(x+w/2)*k,oy+(y+h/2)*k+5,c['ref'],'note','middle')
 if c['key']=='rj45':txt(ox+(x+w/2)*k,oy+(y+h/2)*k+6,'RJ45','note','middle')
for c in cs:
 if c['key'] not in ['ledred','ledgreen']:continue
 x=ox+(c['x']+c['w']/2)*k;y=oy+(c['y']+c['h']/2)*k
 green=c['key']=='ledgreen';n=int(c['ref'][1:]);label=('3V3' if n==201 else 'EN') if green else ('PWR' if n%2 else 'RST')
 s.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6" fill="{"#57e18b" if green else "#ff6a5f"}" stroke="#fff" stroke-width="1"/>')
 txt(x,y-12 if c['y']<55 else y+24,label,'led','middle', '#85efac' if green else '#ffc0b6')
for x,y in d['layout_study']['mounting_hole_centres_mm']:
 s.append(f'<circle cx="{ox+x*k}" cy="{oy+y*k}" r="9.3" fill="#10241e" stroke="#85b99f"/>')
txt(54,818,'上排 J01–J05：PWR 左／RST 右；下排 J06–J10：鏡像，RST 左／PWR 右','small')
for y,title,lines,color in [
 (178,'① 每台兩顆紅燈',['J01–J05：在上排接頭內側。','J06–J10：在下排接頭內側。','PWR 亮：POWER 接點正在驅動。','RST 亮：RESET 接點正在驅動。'],'#ff9d92'),
 (370,'② 兩顆綠燈',['左側 RJ45 插座上方。','3V3：控制板 3.3 V 電源存在。','EN：輸出已啟用；待命時仍亮。'],'#85efac'),
 (532,'③ 網路燈',['LINK／ACT 沿用 RJ45 內建燈。','位於插座外露端，沒有另加 PCB LED。'],'#e7d097'),
 (680,'判讀方式',['EN 亮＋紅燈全熄：啟用待命。','EN 熄：輸出未啟用。','紅燈只代表驅動，不回讀實體接點，','也不是主機開機／關機的狀態。'],'#e7f3ed')]:
 txt(690,y,title,'title',color=color)
 for i,line in enumerate(lines):txt(690,y+36+i*28,line,'note')
s.append('</svg>');(R/'hardware/indicator-layout-R2.svg').write_text(''.join(s))
print('Indicator map exported: 20 red, 2 green, existing RJ45 LINK/ACT.')
