#!/usr/bin/env python3
"""Cosmetic silkscreen declutter (board is already fab-clean; silk only).

On this dense 571-footprint board the per-channel 0805 decoupling clusters, trimpots, and the
48 edge jacks pack overlapping reference-designator silk. This pass MOVES the refdes text off
F.Silkscreen onto F.Fab (kept for assembly / pick-and-place) for the small/dense classes, and
nudges the one screw-terminal refdes that clipped the top board edge. It does NOT delete the
part-outline silk (those outlines stay useful for hand assembly and are sparse per part).

Measurement caveat: `kicad-cli pcb drc` CAPS each warning check at ~199 items, and the dense
0805 footprints' own silk (lines beside their pads) keeps `silk_over_copper` saturated at the
cap regardless of refdes moves -- so the *reported* silk count barely changes even though the
visible refdes clutter is removed (see the routed render). Fully deleting every footprint's
silk does clear the underlying items but (a) removes assembly-useful outlines and (b) makes
every footprint mismatch its library copy (lib_footprint_mismatch 48 -> ~570) -- a worse trade
-- so we keep the outlines and accept the capped cosmetic silk warnings.

Apply AFTER routing+fill, before the final fab export:
  "C:/Program Files/KiCad/10.0/bin/python.exe" polish_silk.py
Keeps ERC/DRC errors/unconnected/parity at 0 (silk-only edits).
"""
import os, re, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pcb")

# Refdes of these dense/small classes is moved off silk -> F.Fab (declutter; kept for assembly).
TO_FAB = ("C", "R", "RV", "J")

def main():
    b = pcbnew.LoadBoard(PCB)
    moved = nudged = 0
    bb = b.GetBoardEdgesBoundingBox()
    y_top = bb.GetTop() / 1e6
    for f in b.GetFootprints():
        pfx = re.sub(r"\d+$", "", f.GetReference())
        rt = f.Reference()
        if pfx in TO_FAB and rt.GetLayer() in (pcbnew.F_Cu, pcbnew.F_SilkS):
            rt.SetLayer(pcbnew.F_Fab); moved += 1
        # nudge any refdes still on silk whose text sits within 1mm of the top edge inward
        if rt.GetLayer() == pcbnew.F_SilkS:
            p = rt.GetPosition()
            if (p.y / 1e6 - y_top) < 1.5:
                rt.SetPosition(pcbnew.VECTOR2I(p.x, p.y + pcbnew.FromMM(2.5))); nudged += 1
    pcbnew.SaveBoard(PCB, b)
    print("moved %d refdes to F.Fab, nudged %d edge-clipping refdes" % (moved, nudged))

if __name__ == "__main__":
    main()
