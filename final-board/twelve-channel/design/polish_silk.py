#!/usr/bin/env python3
"""Silk-screen polish for the dense 12-channel board: move every footprint's Reference (and any
Value) from F.Silkscreen to F.Fab. On a board this tightly tiled the refdes silk clips the board
edge / overlaps neighbours / sits over pads (all cosmetic DRC). The refs stay fully legible on the
F.Fab assembly layer. Run after gen_pcb.py, before the final DRC.

  "C:/Program Files/KiCad/10.0/bin/python.exe" polish_silk.py
"""
import os, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "twelve-channel.kicad_pcb")

def main():
    b = pcbnew.LoadBoard(PCB)
    n = 0
    for fp in b.GetFootprints():
        for f in fp.GetFields():                 # Reference, Value, MPN, Manufacturer, Distributor PN
            if f.GetLayer() == pcbnew.F_SilkS:
                f.SetLayer(pcbnew.F_Fab); n += 1
    pcbnew.SaveBoard(PCB, b)
    print("moved %d footprint text fields F.Silkscreen -> F.Fab" % n)

if __name__ == "__main__":
    main()
