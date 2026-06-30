#!/usr/bin/env python3
"""Fill copper zones on the saved board.

Separate pass (in-memory Fill during board construction segfaults; filling a loaded
board is safe).

Stackup zones (created in gen_pcb.py):
  In1.Cu = GND plane, In2.Cu = -VDC plane, B.Cu = +VDC pour (so the third supply rail also
  has a low-impedance copper area without the router threading pad-to-pad +VDC tracks).
Here we additionally add an F.Cu **GND** ground-fill (priority 2, above any other zone) so
stray F.Cu GND pads tie to ground around the routed traces. B.Cu's +VDC pour (priority 1)
carries the +VDC rail; signal/GND tracks on B.Cu carve isolation gaps in it. FULL pad
connection on all zones keeps the planes low-Z (no starved-thermal spokes).

  "C:/Program Files/KiCad/10.0/bin/python.exe" fill_zones.py
"""
import os, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pcb")

def main():
    b = pcbnew.LoadBoard(PCB)
    gnd = b.FindNet("GND")
    bb = b.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    m = pcbnew.FromMM(0.6)   # >= board copper_edge_clearance (0.5 mm) so the outer fill clears the edge
    have = {(z.GetLayer(), z.GetNetname()) for z in b.Zones()}
    # F.Cu GND ground-fill (top outer): highest priority so it wins over any other top zone.
    if gnd and (pcbnew.F_Cu, "GND") not in have:
        z = pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNetCode(gnd.GetNetCode())
        z.SetAssignedPriority(2)
        ch = z.Outline(); ch.NewOutline()
        for (px, py) in [(x0 + m, y0 + m), (x1 - m, y0 + m), (x1 - m, y1 - m), (x0 + m, y1 - m)]:
            ch.Append(px, py)
        b.Add(z)
    n = len(list(b.Zones()))
    for z in b.Zones():                       # solid pad connection on planes (low-Z,
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # avoids starved-thermal spokes)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print("filled %d zone(s) (GND In1 + F.Cu fill, -VDC In2, +VDC B.Cu)" % n)

if __name__ == "__main__":
    main()
