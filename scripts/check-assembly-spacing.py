#!/usr/bin/env python3
"""Conservative JLC spacing screening, not IPC certification or full DFM."""
import json, math, hashlib
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1]
path=R/'hardware/cad/layout-S2-review.kicad_pcb'
b=p.LoadBoard(str(path))
def kind(f):
 n=str(f.GetFPID().GetLibItemName())
 for size in ['0201','0402','0603','0805','1206']:
  if n.startswith(('R_'+size,'C_'+size)):return size
 if 'QFN' in n:return 'QFN'
 if 'QFP' in n:return 'QFP'
 if 'SOIC' in n or 'SOP' in n or 'TLP3122A' in n:return 'SOP'
 if 'SOT' in n:return 'SOT'
 return None
order=['0201','0402','0603','0805','1206','QFN','QFP','SOP','SOT']
rows=[[.15,.15,.18,.18,.25,1,.5,.4,.2],[.15,.18,.18,.25,1,.5,.4,.2],[.18,.18,.25,1,.5,.4,.2],[.18,.25,1,.5,.4,.2],[.35,1,.5,.4,.2],[1,1,1,1],[1.25,1.25,1],[.5,.4],[.4]]
# Union of F.Fab body/lead drawings and copper pads. This overbounds nonrectangular
# shapes; candidates require exact geometry review, not automatic failure.
def bounds(f):
 items=list(f.Pads())+[g for g in f.GraphicalItems() if g.GetLayer()==p.F_Fab and isinstance(g,p.PCB_SHAPE)]
 boxes=[g.GetBoundingBox() for g in items]
 return [min(p.ToMM(q.GetX()) for q in boxes),min(p.ToMM(q.GetY()) for q in boxes),max(p.ToMM(q.GetRight()) for q in boxes),max(p.ToMM(q.GetBottom()) for q in boxes)]
fps=[f for f in b.GetFootprints() if not f.GetReference().startswith('MH')]
known=[(f.GetReference(),kind(f),bounds(f)) for f in fps if kind(f)]
unknown=sorted(f.GetReference() for f in fps if not kind(f))
findings=[];count=0
for i,(ra,ka,a) in enumerate(known):
 for rb,kb,c in known[i+1:]:
  x,y=sorted((order.index(ka),order.index(kb)));limit=rows[x][y-x]
  gap=math.hypot(max(0,a[0]-c[2],c[0]-a[2]),max(0,a[1]-c[3],c[1]-a[3]));count+=1
  if gap<limit-1e-6:findings.append(dict(a=ra,b=rb,packages=[ka,kb],bbox_gap_mm=round(gap,4),recommended_mm=limit,status='needs_exact_review'))
report=dict(source='https://jlcpcb.com/help/article/minimum-spacing-for-smd-components',pcb_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),method='Conservative union of pad and F.Fab bounding boxes; near pairs require exact geometry verification.',classified_components=len(known),unclassified_components=unknown,pairs_screened=count,candidates=findings,ipc_compliance_verified=False,routing_gate='not_passed')
(R/'hardware/assembly-spacing-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(classified=len(known),unclassified=len(unknown),candidate_count=len(findings),candidates=findings[:12]),indent=2))
