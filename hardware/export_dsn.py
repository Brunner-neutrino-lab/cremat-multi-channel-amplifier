#!/usr/bin/env python3
"""Export the PCB to a Specctra .dsn for autorouting with FreeRouting.

  "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/export_dsn.py
-> hardware/multi-channel-cremat-amplifier.dsn

Then autoroute (see docs/FREEROUTING.md) and bring the result back with import_ses.py.
"""
import os, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pcb")
DSN = os.path.join(HERE, "multi-channel-cremat-amplifier.dsn")

b = pcbnew.LoadBoard(PCB)
try:
    ok = pcbnew.ExportSpecctraDSN(b, DSN)
except TypeError:
    ok = pcbnew.ExportSpecctraDSN(DSN)
print("DSN export %s -> %s" % ("OK" if ok else "FAILED", DSN))
