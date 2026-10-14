#!/usr/bin/env python3
"""Import a Specctra candidate without changing any native placement or pad nets."""
from pathlib import Path
import wx,sys,shutil
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/sys.argv[1];ses=R/sys.argv[2];out=R/sys.argv[3];b=p.LoadBoard(str(src))
def sig():return {f.GetReference():(f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),tuple(sorted((d.GetNumber(),d.GetNetname()) for d in f.Pads()))) for f in b.GetFootprints()}
old=sig();assert p.ImportSpecctraSES(b,str(ses));new=sig();assert old.keys()==new.keys()
for f in b.GetFootprints():
 ref=f.GetReference();a,z=old[ref],new[ref];assert abs(a[0]-z[0])<=100 and abs(a[1]-z[1])<=100 and abs((a[2]-z[2])%360)<.001 and a[3]==z[3],(ref,a,z)
 f.SetPosition(p.VECTOR2I(a[0],a[1]));f.SetOrientationDegrees(a[2])
b.BuildConnectivity();p.SaveBoard(str(out),b)
for ext in ['.kicad_pro','.kicad_dru']:
 f=src.with_suffix(ext)
 if f.exists() and f!=out.with_suffix(ext):shutil.copyfile(f,out.with_suffix(ext))
print('Candidate',len(b.GetTracks()),'copper items;',b.GetConnectivity().GetUnconnectedCount(False),'native unrouted')
