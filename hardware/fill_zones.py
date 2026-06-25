#!/usr/bin/env python3
"""Fill copper zones on the saved board (separate pass: in-memory Fill during board
construction segfaults; filling a loaded board is safe).

  "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/fill_zones.py
"""
import os, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
n = len(list(b.Zones()))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print("filled %d zone(s)" % n)
