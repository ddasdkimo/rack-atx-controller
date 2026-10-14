#!/usr/bin/env python3
"""Export a traceable R.3 review package. Never authorizes production or an order."""
import argparse, csv, hashlib, json, shutil, subprocess, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--cli', default=shutil.which('kicad-cli'))
ap.add_argument('--output', type=Path, default=ROOT/'hardware/manufacturing/R3-candidate')
a = ap.parse_args()
assert a.cli, 'Pass --cli with the KiCad CLI executable'
out = a.output.resolve(); out.mkdir(parents=True, exist_ok=True)
circuit = json.loads((ROOT/'hardware/circuit.json').read_text())
validation = json.loads((ROOT/'hardware/validation/routing-R3-checks.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = {'revision':'B.2 / R.3', 'status':'engineering review package; NOT FOR PRODUCTION',
            'manufacturing_ready':False, 'coordinate_convention':'mm; absolute KiCad origin; X right, Y up (negative on this PCB); all components Top',
            'rotation_convention':'Native KiCad degrees modulo 360. Supplier placement preview and polarity confirmation required; no unverified generic rotation corrections applied.',
            'boards':{}, 'pending':['JLCPCB full Economic quote and component/placement preview',
                'QFN via-in-pad process, finish and stencil DFM acceptance',
                'Final independent frozen-package review', 'Prototype functional verification']}
for name, base in [('controller','rack-atx-controller'), ('adapter','adapter')]:
    board = ROOT/f'hardware/cad/B2/{base}.kicad_pcb'
    assert sha(board)==validation[name]['pcb_sha256']
    assert validation[name]['native_unrouted']==validation[name]['drc_violations']==0
    d=out/name; d.mkdir(exist_ok=True)
    def cli(*args):
        subprocess.run([a.cli, *map(str,args)], check=True, capture_output=True)
    cli('pcb','export','gerbers','-l','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,Edge.Cuts',
        '--no-netlist','--subtract-soldermask','-o',str(d)+'/',board)
    cli('pcb','export','drill','--excellon-separate-th','--generate-map','--map-format','svg',
        '--generate-report','-o',str(d)+'/',board)
    cli('pcb','export','pos','--format','csv','--units','mm','--side','front','-o',d/'native-pos.csv',board)
    parts=[x for x in circuit['components'] if x['key']!='flag' and ((x['sheet']=='adapter')==(name=='adapter'))]
    refs={x['ref'] for x in parts}
    native=[x for x in csv.DictReader((d/'native-pos.csv').open()) if x['Ref'] in refs]
    assert len(native)==len(refs) and {x['Ref'] for x in native}==refs
    assert all(x['Side']=='top' for x in native)
    with (d/f'{name}-cpl.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
        w.writerows([x['Ref'],x['PosX']+'mm',x['PosY']+'mm','Top',float(x['Rot'])%360] for x in native)
    bom=ROOT/f'hardware/bom/{name}-jlc-bom.csv'
    bom_refs={ref.strip() for row in csv.DictReader(bom.open()) for ref in row['Designator'].split(',')}
    assert bom_refs==refs, (name,'BOM/CPL references differ')
    shutil.copyfile(bom,d/f'{name}-bom.csv')
    gerbers=[p for p in sorted(d.iterdir()) if p.suffix in {'.gtl','.gbl','.gts','.gbs','.gto','.gbo','.gtp','.gm1','.drl'}]
    with zipfile.ZipFile(out/f'{name}-gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in gerbers: z.write(p,p.name)
    assert sha(board)==validation[name]['pcb_sha256'], 'Board changed during export'
    manifest['boards'][name]={'native_pcb_sha256':sha(board),'parts':len(refs),'bom_cpl_reference_parity':True,
        'native_drc':0,'native_unconnected':0,'files':{p.relative_to(out).as_posix():sha(p) for p in sorted(d.iterdir()) if p.is_file()},
        'gerber_zip_sha256':sha(out/f'{name}-gerbers.zip')}
manifest['circuit_sha256']=sha(ROOT/'hardware/circuit.json')
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Exported review package:',out)
print('BOM/CPL match: 300 controller parts, 6 passive adapter parts. Factory acceptance pending.')
