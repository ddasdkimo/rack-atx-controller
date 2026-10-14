#!/usr/bin/env python3
"""Add connected top-side ground copper to bridge bottom-layer routing slots.
Native DRC and connectivity must be rerun; not a return-path certification.
"""
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
R=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(R/'artifacts/local/R1-general.kicad_pcb'))
for old in list(b.Zones()):
 if old.GetIsRuleArea() or old.GetLayer()!=p.B_Cu:continue
 if any(not z.GetIsRuleArea() and z.GetLayer()==p.F_Cu and z.GetNetCode()==old.GetNetCode() for z in b.Zones()):continue
 z=p.ZONE(b);z.SetLayer(p.F_Cu);z.SetNetCode(old.GetNetCode());z.SetZoneName(old.GetNetname()+' top stitching');z.SetLocalClearance(p.FromMM(.25));z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetMinThickness(p.FromMM(.2));z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
 source=old.Outline().COutline(0);poly=z.Outline();poly.NewOutline()
 for i in range(source.PointCount()):v=source.CPoint(i);poly.Append(v.x,v.y)
 b.Add(z)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(R/'artifacts/local/R1-ground-bridged.kicad_pcb'),b)
print('With top ground',b.GetConnectivity().GetUnconnectedCount(False),'native unrouted')
