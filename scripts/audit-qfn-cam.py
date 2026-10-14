"""Independent parsing of the local EPAD trial; not a production release check."""
import argparse,json,math,warnings,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from gerbonara import GerberFile,ExcellonFile
from gerbonara.utils import MM
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--gerber-dir',type=Path,required=True)
parser.add_argument('--prefix',required=True)
parser.add_argument('--source-board',type=Path,required=True,help='Native board from which these CAM files were exported')
parser.add_argument('--center-x',type=float,required=True)
parser.add_argument('--center-y',type=float,required=True,help='PCB coordinate, positive down')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--svg',type=Path,required=True)
args=parser.parse_args();D=args.gerber_dir;cx,cy=args.center_x,-args.center_y
bounds=((cx-4,cy-4),(cx+4,cy+4));ep=((cx-2,cy-2),(cx+2,cy+2))

def hit(o):
 (x0,y0),(x1,y1)=o.bounding_box(MM);return x0<ep[1][0] and x1>ep[0][0] and y0<ep[1][1] and y1>ep[0][1]
files={k:GerberFile.open(D/f'{args.prefix}-{v}') for k,v in {'paste':'F_Paste.gtp','top_mask':'F_Mask.gts','bottom_mask':'B_Mask.gbs'}.items()}
with warnings.catch_warnings(record=True) as warn:
 warnings.simplefilter('always');drill_path=D/f'{args.prefix}-PTH.drl'
 if not drill_path.exists():drill_path=D/f'{args.prefix}.drl'
 drill=ExcellonFile.open(drill_path)
warning_messages=[str(w.message).split(':',1)[-1] for w in warn]
pastes=[o for o in files['paste'].objects if hit(o)];holes=[o for o in drill.objects if hit(o)];top=[o for o in files['top_mask'].objects if hit(o)];bottom=[o for o in files['bottom_mask'].objects if hit(o)]
assert len(pastes)==16 and len(holes)==9 and len(top)==1 and len(bottom)==0
assert all(abs(o.aperture.diameter-.3)<1e-6 for o in holes)
assert {(o.x,o.y) for o in holes}=={(cx+x,cy+y) for x in (-1.,0.,1.) for y in (-1.,0.,1.)}
for o in pastes:
 (x0,y0),(x1,y1)=o.bounding_box(MM);assert abs(x1-x0-.75)<1e-6 and abs(y1-y0-.75)<1e-6
 # No drill disk intersects even the more conservative square aperture bounding box.
 for h in holes:
  dx=max(x0-h.x,0,h.x-x1);dy=max(y0-h.y,0,h.y-y1);assert math.hypot(dx,dy)>.15
assert top[0].bounding_box(MM)==ep
report=dict(status='pass local EPAD CAM geometry only',parser='gerbonara',paste_windows=len(pastes),conservative_paste_bbox_to_hole_gap_mm=min(math.hypot(max(o.bounding_box(MM)[0][0]-h.x,0,h.x-o.bounding_box(MM)[1][0]),max(o.bounding_box(MM)[0][1]-h.y,0,h.y-o.bounding_box(MM)[1][1]))-.15 for o in pastes for h in holes),paste_bbox_mm=[.75,.75],drills=len(holes),drill_mm=.3,top_mask_ep_opening_mm=[4,4],bottom_mask_apertures_under_ep=len(bottom),holes_do_not_overlap_paste=True,parser_warnings=warning_messages,limitations=['Bottom tenting is not resin filling or copper capping.','Native DRC checks geometry; fabrication and assembly DFM remain pending.','CAM geometry alone does not constitute factory release.'],sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(D.iterdir()) if p.is_file()})
report['source_board']={'name':args.source_board.name,'sha256':hashlib.sha256(args.source_board.read_bytes()).hexdigest()}
args.output.write_text(json.dumps(report,indent=2)+'\n')
# Render actual parsed CAM data with aligned drill overlay, not a hand-drawn approximation.
root=ET.Element('svg',xmlns='http://www.w3.org/2000/svg',width='1800',height='800',viewBox='0 0 1800 800');ET.SubElement(root,'rect',width='1800',height='800',fill='white')
def label(x,y,text,size=25):
 t=ET.SubElement(root,'text',x=str(x),y=str(y),fill='#142c3a',**{'font-family':'sans-serif','font-size':str(size)});t.text=text
label(40,50,'QFN process geometry — actual Gerber / Excellon data',32)
for i,(key,title,color) in enumerate([('paste','F.Paste + drill: 16 EP windows / 9 EP holes','#0c9b94'),('top_mask','F.Mask + drill: exposed top EPAD','#e2bd63'),('bottom_mask','B.Mask: no openings below EPAD','#28a65c')]):
 x=40+i*590;label(x,110,title,22)
 for layer,fg in [(files[key],color)]+([] if key=='bottom_mask' else [(drill,'#d23535')]):
  svg=ET.fromstring(str(layer.to_svg(force_bounds=bounds,fg=fg,bg='none')));svg.set('x',str(x));svg.set('y','140');svg.set('width','550');svg.set('height','550');root.append(svg)
 ET.SubElement(root,'rect',x=str(x),y='140',width='550',height='550',fill='none',stroke='#afbcc2')
label(40,748,'DRILL: red = 0.30 mm hole. Bottom mask covering is not filled / capped via-in-pad. Not for fabrication.',22)
ET.ElementTree(root).write(args.svg,encoding='unicode');print(json.dumps({k:v for k,v in report.items() if k!='sha256'},indent=2))
