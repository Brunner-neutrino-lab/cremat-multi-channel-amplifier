#!/usr/bin/env python3
"""Fill copper zones on the saved board, and ensure GND ground-fill on the outer layers.

Separate pass (in-memory Fill during board construction segfaults; filling a loaded
board is safe). Adds an F.Cu and B.Cu GND pour (priority 0) if absent so stray THT GND
pads tie to ground even where the inner GND plane is locally fragmented by routing.

  "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/fill_zones.py
"""
import os, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "csp-cr112.kicad_pcb")

def main():
    b = pcbnew.LoadBoard(PCB)
    gnd = b.FindNet("GND")
    bb = b.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    m = pcbnew.FromMM(0.3)
    have = {(z.GetLayer(), z.GetNetname()) for z in b.Zones()}
    if gnd:
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if (layer, "GND") in have:
                continue
            z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(gnd.GetNetCode())
            z.SetAssignedPriority(0)
            ch = z.Outline(); ch.NewOutline()
            for (px, py) in [(x0 + m, y0 + m), (x1 - m, y0 + m), (x1 - m, y1 - m), (x0 + m, y1 - m)]:
                ch.Append(px, py)
            b.Add(z)
    n = len(list(b.Zones()))
    for z in b.Zones():                       # solid pad connection on planes (low-Z,
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # avoids starved-thermal spokes)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print("filled %d zone(s) (incl. outer GND ground-fill)" % n)

if __name__ == "__main__":
    main()
