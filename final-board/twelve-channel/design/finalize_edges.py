#!/usr/bin/env python3
"""DIAGNOSTIC (the cutout restore is no longer a separate step).

The MCX Edge.Cuts cutouts are now emitted directly by gen_pcb.py: the 48 closed-rectangle
connector slots stay ON Edge.Cuts as internal cutouts, and FreeRouting routes around them as
keepouts (the old "park on Dwgs.User, restore later" trick was the fab blocker and was removed).
A scoped custom rule (multi-channel-cremat-amplifier.kicad_dru) exempts the MCX shield pads,
which straddle their slot by design, from the board-edge-clearance check.

This script just reports whether every MCX cutout is on Edge.Cuts (it should be: 192 segs).

  "C:/Program Files/KiCad/10.0/bin/python.exe" finalize_edges.py
"""
import os, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pcb")

def main():
    b = pcbnew.LoadBoard(PCB)
    edge = dwgs = 0
    for f in b.GetFootprints():
        if "MCX" in str(f.GetFPID().GetLibItemName()):
            for it in f.GraphicalItems():
                if it.GetLayer() == pcbnew.Edge_Cuts:
                    edge += 1
                elif it.GetLayer() == pcbnew.Dwgs_User:
                    dwgs += 1
    print("MCX cutout segments on Edge.Cuts: %d (expect 192 = 48*4) | on Dwgs.User: %d (expect 0)"
          % (edge, dwgs))
    if dwgs:
        print("WARNING: some MCX cutouts are still parked on Dwgs.User -- not fab-ready.")

if __name__ == "__main__":
    main()
