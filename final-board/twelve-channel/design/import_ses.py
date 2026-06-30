#!/usr/bin/env python3
"""Import a FreeRouting Specctra session (.ses) back into the PCB (the routed tracks).

  "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/import_ses.py [path/to/file.ses]
default ses = hardware/multi-channel-cremat-amplifier.ses ; writes the routed .kicad_pcb.
"""
import os, sys, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pcb")
SES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "multi-channel-cremat-amplifier.ses")

b = pcbnew.LoadBoard(PCB)
try:
    ok = pcbnew.ImportSpecctraSES(b, SES)
except TypeError:
    ok = pcbnew.ImportSpecctraSES(SES)
pcbnew.SaveBoard(PCB, b)
print("SES import %s from %s ; saved routed board" % ("OK" if ok else "FAILED", SES))
