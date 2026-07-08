#!/usr/bin/env python3
"""Generate a dimensionally-reasonable STEP model for the Linx/TE CONMCX013 edge-mount MCX jack.
Dims from the KiCad footprint (body 6.7 mm wide x 6.3 mm on-board deep; courtyard reaches
-4.82 mm on the mating side) + standard MCX barrel geometry (OD ~5 mm, coupling ~6.7 mm).

Footprint frame: +Y (footprint, downward) = on-board housing; -Y = mating side / board edge.
KiCad 3D flips Y (model +Y = footprint -Y), so in MODEL coords the barrel protrudes +Y (edge)
and the base extends -Y (on-board). Verified against the board render.
"""
import sys
import cadquery as cq

OUT = sys.argv[1]

BW, BD, BH = 6.7, 6.3, 1.4          # base plate: width(x), on-board depth(y), height(z)
BAR_OD, BAR_LEN = 5.0, 5.2          # coax barrel: OD, protrusion off the edge (+Y)
CUP_OD, CUP_LEN = 6.7, 1.2          # snap-on coupling ring at the mating face
PIN_OD = 1.0
AXIS_Z = 2.9                        # coax axis height above the board

# base plate (on-board, model -Y), resting on the board (z 0..BH)
base = cq.Workplane("XY").box(BW, BD, BH).translate((0, -BD / 2.0, BH / 2.0))
# a short riser blends the round barrel down onto the flat base
riser = cq.Workplane("XY").box(BW, 2.6, AXIS_Z + BAR_OD / 2.0).translate((0, -1.3, (AXIS_Z + BAR_OD / 2.0) / 2.0))

def ycyl(dia, y0, y1, z):
    L = y1 - y0
    c = cq.Workplane("XY").cylinder(L, dia / 2.0)          # axis along Z, centered
    c = c.rotate((0, 0, 0), (1, 0, 0), -90)                # -> axis along Y
    return c.translate((0, y0 + L / 2.0, z))

barrel = ycyl(BAR_OD, 0.0, BAR_LEN, AXIS_Z)                # protrudes +Y off the edge
coupling = ycyl(CUP_OD, BAR_LEN, BAR_LEN + CUP_LEN, AXIS_Z)
pin = ycyl(PIN_OD, -2.0, BAR_LEN + CUP_LEN + 0.6, AXIS_Z)  # center conductor tip

body = base.union(riser).union(barrel).union(coupling).union(pin)
# KiCad applies NO Y-flip (model +Y == footprint +Y). The footprint's mating side / signal pad /
# board edge is at footprint -Y, so the barrel must protrude toward -Y: flip 180 deg about Z.
body = body.rotate((0, 0, 0), (0, 0, 1), 180)
cq.exporters.export(body, OUT)
print("wrote", OUT)
