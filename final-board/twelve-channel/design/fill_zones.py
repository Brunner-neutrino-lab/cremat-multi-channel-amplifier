#!/usr/bin/env python3
"""Fill copper zones on the saved 12-channel board (separate pass; in-memory Fill during
construction segfaults). Zones (from gen_pcb.py): In1=GND plane, In2=-VDC plane, B.Cu=+VDC
pour. Adds an F.Cu GND ground-fill (priority 2) so top-side GND ties around the cloned tracks.
FULL pad connection keeps the planes low-Z (no starved-thermal spokes).

  "C:/Program Files/KiCad/10.0/bin/python.exe" fill_zones.py
"""
import os, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "twelve-channel.kicad_pcb")
PRO = os.path.join(HERE, "twelve-channel.kicad_pro")

def ensure_netclasses():
    # Zone fill uses the project netclass clearances (hv_bias = 0.6 mm). A KiCad GUI save can
    # FLATTEN the .kicad_pro (netclasses gone) -> the fill silently violates the HV rule and a
    # subsequent DRC passes vacuously (bit us twice on 2026-07-11). Heal + warn loudly.
    if "hv_bias" in open(PRO, encoding="utf-8").read():
        return
    print("*" * 78)
    print("WARNING: twelve-channel.kicad_pro had NO netclasses (GUI save flattened it?).")
    print("         Restoring from gen_sch.build_pro() before filling. If KiCad has this")
    print("         project open, CLOSE IT WITHOUT SAVING or it will clobber it again.")
    print("*" * 78)
    import importlib.util
    spec = importlib.util.spec_from_file_location("tw_gen_sch", os.path.join(HERE, "gen_sch.py"))
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    g.build_pro()

def main():
    ensure_netclasses()
    b = pcbnew.LoadBoard(PCB)
    gnd = b.FindNet("GND")
    bb = b.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    m = pcbnew.FromMM(0.6)
    have = {(z.GetLayer(), z.GetNetname()) for z in b.Zones()}
    if gnd and (pcbnew.F_Cu, "GND") not in have:
        z = pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNetCode(gnd.GetNetCode())
        z.SetAssignedPriority(2)
        ch = z.Outline(); ch.NewOutline()
        for (px, py) in [(x0 + m, y0 + m), (x1 - m, y0 + m), (x1 - m, y1 - m), (x0 + m, y1 - m)]:
            ch.Append(px, py)
        b.Add(z)
    n = len(list(b.Zones()))
    for z in b.Zones():
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print("filled %d zone(s)" % n)

if __name__ == "__main__":
    main()
