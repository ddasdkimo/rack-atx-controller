#!/usr/bin/env python3
"""Pre-place staggered inside/outside QFN escapes, then route from through vias."""
import wx,shutil,json,re
from pathlib import Path
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/'artifacts/local/R1-inward.kicad_pcb';b=p.LoadBoard(str(src));removed=[]
critical=set('BUCK_SW BUCK_BST MCU_XN MCU_XP MCU_XP_CR ETH_XI ETH_XO'.split())
for t in list(b.GetTracks()):
 if t.GetNetname() in critical:continue
 if isinstance(t,p.PCB_VIA):
  a=t.GetPosition();x,y=a.x/1e6,a.y/1e6
  delete=28.8<x<39 and 92.1<y<102 and not(t.GetNetname()=='GND_CTRL' and 32.9<x<35.1 and 95.9<y<98.1)
 else:
  a,z=t.GetStart(),t.GetEnd();delete=min(a.x,z.x)/1e6<39 and max(a.x,z.x)/1e6>28.8 and min(a.y,z.y)/1e6<102 and max(a.y,z.y)/1e6>92.1
 if t.GetNetname()=='SPI_MISO':delete=True
 if delete:b.Remove(t);removed.append(t)
fps={f.GetReference():f for f in b.GetFootprints()};fps['C11'].SetPosition(p.VECTOR2I(p.FromMM(35.5),p.FromMM(90.5)))
pads={d.GetNumber():d for d in fps['U2'].Pads() if d.GetNumber()}
fan={4:(31.45,95.3),5:(29.45,95.8),6:(31.45,96.3),7:(29.45,96.8),9:(31.45,97.3),10:(29.45,97.8),11:(31.45,98.3),12:(29.45,98.8),13:(31.45,99.2),14:(29.45,99.8),15:(31.1,101.25),16:(32,99.55),17:(32.1,101.25),18:(33,99.55),19:(33.1,101.25),21:(34,99.55),22:(34.1,101.25),23:(35,99.55),24:(35.1,101.25),27:(36,99.55),36:(36.55,96.8),37:(38.55,96.4),38:(36.55,96),40:(38.55,95.6),41:(38.5,94.85),42:(38,93.75),43:(36.7,92.7),44:(36.4,94.45),45:(35.7,92.45),47:(35.4,94.45),48:(34.7,92.45),49:(34.4,94.45),50:(33.7,92.45),51:(33.4,94.45),52:(32.4,94.45)}
def xy(v):return(v.x/1e6,v.y/1e6)
def vec(q):return p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))
def seg(a,z,n):
 t=p.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(z));t.SetWidth(p.FromMM(.125));t.SetLayer(p.F_Cu);t.SetNetCode(b.FindNet(n).GetNetCode());b.Add(t)
for pin,q in fan.items():
 d=pads[str(pin)];start=xy(d.GetPosition());jogs=[]
 if pin in range(4,15):jogs=[((31.2 if q[0]>31 else 29.9),start[1])]
 elif pin in range(15,28):jogs=[(start[0],(99.8 if q[1]<100 else 101.1))]
 elif pin in range(43,53):jogs=[(start[0],(94.2 if q[1]>94 else 92.95))]
 if pin==40:jogs=[(38.05,95.2)]
 pts=[start]+jogs+[q]
 for a,z in zip(pts,pts[1:]):seg(a,z,d.GetNetname())
 v=p.PCB_VIA(b);v.SetPosition(vec(q));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(d.GetNetCode());b.Add(v)
for net,pts in [('USB_DM_MCU',[(35.4,100.45),(35.4,100.87),(35.6,101.07),(35.6,102.075),(35.5,102.175)]),('USB_DP_MCU',[(35.8,100.45),(35.8,100.87),(36.1,101.17),(37.5,102.175)])]:
 for a,z in zip(pts,pts[1:]):seg(a,z,net)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());out=R/'artifacts/local/R1-mcu-fanout.kicad_pcb';p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(src.with_suffix(ext),out.with_suffix(ext))
pro=json.loads(out.with_suffix('.kicad_pro').read_text());pro['board']['design_settings']['rules']['min_track_width']=.125;out.with_suffix('.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
p.ExportSpecctraDSN(b,str(R/'artifacts/local/R1-mcu-fanout.dsn'));print('Staggered escapes:',len(fan),'removed copper',len(removed),'native unconnected',b.GetConnectivity().GetUnconnectedCount(False))
