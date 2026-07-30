#!/usr/bin/env python3
"""2D mechanical drawings for stacking two 12-channel boards in a Hammond RM2U1908VBK 2U box.
Generates 5 dimensioned, to-scale SVGs (+ PNGs). Run:  python gen_drawings.py <png_out_dir>
All dimensions in mm. Geometry derived from the routed board + the Hammond drawing (interior
84.53 H x 415.30 W x 196.85 D)."""
import sys, fitz
OUT = "."                                   # SVGs next to this script (mechanical/)
PNG = sys.argv[1] if len(sys.argv) > 1 else "."

# ---------- geometry ----------
BOX_W, BOX_D, BOX_H = 415.30, 196.85, 84.53     # box interior W(x) D(y) H(z)
BOARD_D, BOARD_W, T = 213.30, 334.80, 1.6       # board depth(x, connectors) width(y) thick
WMARG, PROT = 40.25, 8.225                       # width margin each side ; depth protrusion each side
H1, H2, H3 = 12.7, 25.4, 43.23                   # bottom standoff / inter-board standoff / top air
Zb1 = (H1, H1 + T)                               # board1 bottom,top Z
Zb2 = (H1 + T + H2, H1 + T + H2 + T)             # board2 bottom,top Z
Zb1m = sum(Zb1) / 2                              # 13.5  connector plane
Zb2m = sum(Zb2) / 2                              # 40.5
HOLES = [(45.25, -0.23), (369.95, -0.23), (45.25, 196.97), (369.95, 196.97)]  # box X,Y
CONN = (69.2, 356.2)                             # connector-row X extent (24 MCX)
SOX = (45.25, 369.95)                            # standoff X positions
MODH, MODBENT = 26.5, 10.0                       # module standing / bent height above board
SLOTH = 8.0                                      # panel connector-slot height

class D:
    def __init__(s, W, H, sc, ox, oy, flipy=False, title=""):
        s.sc, s.ox, s.oy, s.fy = sc, ox, oy, flipy
        s.e = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Segoe UI,Arial">',
               f'<rect width="{W}" height="{H}" fill="#fcfcf9"/>',
               f'<text x="14" y="26" font-size="18" font-weight="800" fill="#12233a">{title}</text>']
    def X(s, x): return s.ox + x * s.sc
    def Y(s, y): return (s.oy - y * s.sc) if s.fy else (s.oy + y * s.sc)
    def rect(s, x, y, w, h, fill="none", stroke="#333", sw=1.3, dash=""):
        X0 = s.X(x); Y0 = s.Y(y + h) if s.fy else s.Y(y)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        s.e.append(f'<rect x="{X0:.1f}" y="{Y0:.1f}" width="{w*s.sc:.1f}" height="{h*s.sc:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{da}/>')
    def hole(s, x, y, r=1.6, col="#b03030"):
        s.e.append(f'<circle cx="{s.X(x):.1f}" cy="{s.Y(y):.1f}" r="{r*s.sc:.1f}" fill="none" stroke="{col}" stroke-width="1.5"/>')
        s.e.append(f'<line x1="{s.X(x)-r*s.sc-4:.1f}" y1="{s.Y(y):.1f}" x2="{s.X(x)+r*s.sc+4:.1f}" y2="{s.Y(y):.1f}" stroke="{col}" stroke-width="0.6"/>')
        s.e.append(f'<line x1="{s.X(x):.1f}" y1="{s.Y(y)-r*s.sc-4:.1f}" x2="{s.X(x):.1f}" y2="{s.Y(y)+r*s.sc+4:.1f}" stroke="{col}" stroke-width="0.6"/>')
    def line(s, x1, y1, x2, y2, stroke="#333", sw=1.2, dash=""):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        s.e.append(f'<line x1="{s.X(x1):.1f}" y1="{s.Y(y1):.1f}" x2="{s.X(x2):.1f}" y2="{s.Y(y2):.1f}" stroke="{stroke}" stroke-width="{sw}"{da}/>')
    def txt(s, x, y, t, anc="middle", fs=11, col="#111", px=0, py=0, w="400"):
        s.e.append(f'<text x="{s.X(x)+px:.1f}" y="{s.Y(y)+py:.1f}" text-anchor="{anc}" font-size="{fs}" font-weight="{w}" fill="{col}">{t}</text>')
    def dimh(s, x1, x2, ypx, label):
        X1, X2 = s.X(x1), s.X(x2)
        s.e.append(f'<line x1="{X1}" y1="{ypx}" x2="{X2}" y2="{ypx}" stroke="#245" stroke-width="0.9"/>')
        for X in (X1, X2): s.e.append(f'<line x1="{X}" y1="{ypx-4}" x2="{X}" y2="{ypx+4}" stroke="#245" stroke-width="0.9"/>')
        s.e.append(f'<text x="{(X1+X2)/2}" y="{ypx-3}" text-anchor="middle" font-size="11" fill="#245">{label}</text>')
    def dimv(s, y1, y2, xpx, label):
        Y1, Y2 = s.Y(y1), s.Y(y2)
        s.e.append(f'<line x1="{xpx}" y1="{Y1}" x2="{xpx}" y2="{Y2}" stroke="#245" stroke-width="0.9"/>')
        for Y in (Y1, Y2): s.e.append(f'<line x1="{xpx-4}" y1="{Y}" x2="{xpx+4}" y2="{Y}" stroke="#245" stroke-width="0.9"/>')
        s.e.append(f'<text x="{xpx+5}" y="{(Y1+Y2)/2+4}" text-anchor="start" font-size="11" fill="#245">{label}</text>')
    def note(s, xpx, ypx, lines, col="#7a2a12"):
        for i, l in enumerate(lines):
            s.e.append(f'<text x="{xpx}" y="{ypx+i*15}" font-size="11" fill="{col}">{l}</text>')
    def save(s, name):
        s.e.append('</svg>')
        open(f"{OUT}/{name}.svg", "w", encoding="utf-8").write("".join(s.e))
        fitz.open(f"{OUT}/{name}.svg")[0].get_pixmap(matrix=fitz.Matrix(1.7, 1.7)).save(f"{PNG}/{name}.png")
        return name

made = []

# ============ 1) TOP VIEW ============
sc = 1.5; d = D(820, 510, sc, 100, 96, title="1  TOP VIEW - boards in 2U box (looking down)")
d.rect(0, 0, BOX_W, BOX_D, fill="#eef3ee", stroke="#556", sw=1.6)
d.rect(WMARG, -PROT, BOARD_W, BOARD_D, fill="#cfe0f5", stroke="#1f57b0", sw=1.5)
d.txt(WMARG + BOARD_W / 2, BOARD_D / 2, "PCB  213.3 x 334.8", fs=13, w="700", col="#1f3a6b")
d.line(0, 0, BOX_W, 0, stroke="#c0392b", sw=2.4); d.txt(BOX_W / 2, 0, "FRONT panel (Y=0)", py=15, fs=11, col="#c0392b")
d.line(0, BOX_D, BOX_W, BOX_D, stroke="#c0392b", sw=2.4); d.txt(BOX_W / 2, BOX_D, "REAR panel", py=-6, fs=11, col="#c0392b")
for cy in (6.3 - PROT, 206.9 - PROT):
    d.line(CONN[0], cy, CONN[1], cy, stroke="#0a7d3a", sw=3)
d.txt((CONN[0] + CONN[1]) / 2, 6.3 - PROT, "24 MCX row (proud through panel slot)", py=13, fs=10, col="#0a7d3a")
for hx, hy in HOLES: d.hole(hx, hy)
d.dimh(0, WMARG, d.Y(BOX_D) + 40, "40.25"); d.dimh(WMARG + BOARD_W, BOX_W, d.Y(BOX_D) + 40, "40.25")
d.dimh(SOX[0], SOX[1], d.Y(-PROT) - 14, "324.7  (hole rectangle width)")
d.dimv(-PROT, 0, d.X(BOX_W) + 20, "8.2 proud"); d.dimv(BOX_D, BOARD_D - PROT, d.X(BOX_W) + 20, "8.2")
d.txt(SOX[0], -PROT, "M3 hole", py=-8, fs=9, col="#b03030")
d.note(95, 430, ["Board centered in width (40.25 mm each side). Board is 16.45 mm deeper than the box",
                 "-> protrudes 8.2 mm past each panel; the 24+24 MCX sit proud through the front/rear slots.",
                 "4x M3 corner holes: X = 45.25 / 369.95, Y ~ 0 / 196.85 (i.e. on the panel lines)."])
made.append(d.save("1-top-view"))

# ============ 2) SIDE VIEW ============
sc = 1.95; d = D(760, 450, sc, 130, 372, flipy=True, title="2  SIDE VIEW - board stack (Z up, front at left)")
d.rect(0, 0, BOX_D, BOX_H, fill="#f5f7f5", stroke="#556", sw=1.6)
d.line(0, 0, 0, BOX_H, stroke="#c0392b", sw=2.6); d.txt(0, BOX_H, "FRONT", py=-6, fs=10, col="#c0392b")
d.line(BOX_D, 0, BOX_D, BOX_H, stroke="#c0392b", sw=2.6); d.txt(BOX_D, BOX_H, "REAR", py=-6, fs=10, col="#c0392b")
d.txt(BOX_D / 2, 0, "bottom cover", py=15, fs=10, col="#556")
for (zb, zt), lbl, (mode, mh) in ((Zb1, "BOARD 1", ("bent", MODBENT)), (Zb2, "BOARD 2", ("upright", MODH))):
    d.rect(-PROT, zb, BOARD_D, zt - zb, fill="#1f57b0", stroke="#0d2f66", sw=1)
    d.txt(BOARD_D / 2 - PROT, zb, lbl, py=13, fs=10, col="#0d2f66", w="700")
    d.rect(23.8, zt, 50, mh, fill="#e8c15a" if mode == "upright" else "#d9a441", stroke="#7a5c00", sw=1)
    d.txt(48, zt + mh, f"modules ({mode})", py=-4, fs=9, col="#5a4300")
for hy in (0.0, BOX_D):
    d.rect(hy - 2, 0, 4, H1, fill="#c9c9c9", stroke="#555", sw=0.8)
    d.rect(hy - 2, Zb1[1], 4, H2, fill="#a9a9a9", stroke="#555", sw=0.8)
for cm in (Zb1m, Zb2m):
    d.line(-PROT - 7, cm, -PROT, cm, stroke="#0a7d3a", sw=3)
    d.line(BOARD_D - PROT, cm, BOARD_D - PROT + 7, cm, stroke="#0a7d3a", sw=3)
d.dimv(0, H1, d.X(BOX_D) + 22, "12.7 (1/2in)"); d.dimv(Zb1[1], Zb2[0], d.X(BOX_D) + 22, "25.4 (1in)")
d.dimv(Zb2[1], BOX_H, d.X(BOX_D) + 22, "43.2 air"); d.dimv(0, BOX_H, d.X(BOX_D) + 92, "84.53 interior")
d.txt(-PROT, Zb1m, "Z=13.5", anc="end", px=-9, fs=9, col="#0a7d3a")
d.txt(BOARD_D - PROT, Zb2m, "Z=40.5", anc="start", px=9, fs=9, col="#0a7d3a")
d.note(130, 412, ["12.7 + 1.6 + 25.4(1in) + 1.6 + 43.2 = 84.53 mm.  Standoffs: 4x 1/2in (bottom) + 4x 1in (inter-board).",
                  "Board 1 modules (26.5 mm) BEND to clear the 25.4 mm gap; board 2 modules stand.",
                  "Standoff columns are at Y~0 / 196.85 (the panel lines) -> front/rear panels need corner relief."])
made.append(d.save("2-side-view"))

# ============ 3 & 4) FRONT / REAR PANELS ============
def panel(name, title, labels):
    sc = 1.5; d = D(770, 430, sc, 95, 215, flipy=True, title=title)
    d.rect(0, 0, BOX_W, BOX_H, fill="#f6f6f2", stroke="#333", sw=1.6)                 # panel outline (interior)
    for z, who in ((Zb1m, "board 1"), (Zb2m, "board 2")):                            # connector slots
        d.rect(CONN[0], z - SLOTH / 2, CONN[1] - CONN[0], SLOTH, fill="#d8f0e0", stroke="#0a7d3a", sw=1.4)
        d.txt((CONN[0] + CONN[1]) / 2, z, f"{who} MCX slot ({labels})", fs=10, col="#0a5a2a", py=4)
        d.dimv(z - SLOTH / 2, z + SLOTH / 2, d.X(CONN[1]) + 16, "8")
        d.txt(CONN[1], z, f"Z={z:.1f}", anc="start", px=54, fs=9, col="#0a7d3a")
    for x in SOX:                                                                     # standoff relief
        d.rect(x - 4, 0, 8, Zb2[1] + 0.5, fill="#f2d9d9", stroke="#b03030", sw=1.2, dash="4 3")
        d.txt(x, Zb2[1], "standoff relief", py=-4, fs=8, col="#b03030")
    d.dimh(CONN[0], CONN[1], d.Y(0) + 20, "287 (slot length: X 69.2 -> 356.2)")
    d.dimh(0, SOX[0], d.Y(BOX_H) - 12, "45.25"); d.dimh(SOX[1], BOX_W, d.Y(BOX_H) - 12, "45.35")
    d.dimv(0, BOX_H, d.X(0) - 16, "84.53"); d.dimh(0, BOX_W, d.Y(0) + 44, "415.30 (interior width)")
    d.note(95, 330, ["Two horizontal slots (~8 mm tall) at Z=13.5 (board 1) and Z=40.5 (board 2), X 69.2->356.2.",
                     "Two standoff-relief cutouts (~8 mm wide) at X=45.25 / 369.95, from the bottom up to Z~42",
                     "(the board holes land on the panel line, so the corner standoffs pass through here)."])
    return d.save(name)
made.append(panel("3-front-panel", "3  FRONT PANEL (inside face) - FE / TEST inputs edge", "FE + TEST"))
made.append(panel("4-rear-panel", "4  REAR PANEL (inside face) - BIAS / OUT edge", "BIAS + OUT"))

# ============ 5) BOTTOM PANEL / COVER ============
sc = 1.5; d = D(770, 470, sc, 95, 70, title="5  BOTTOM COVER - standoff drill pattern (looking down)")
d.rect(0, 0, BOX_W, BOX_D, fill="#f4f4ee", stroke="#333", sw=1.6)
d.line(0, 0, BOX_W, 0, stroke="#c0392b", sw=1.6, dash="6 4"); d.txt(BOX_W / 2, 0, "front panel line", py=-5, fs=9, col="#c0392b")
d.line(0, BOX_D, BOX_W, BOX_D, stroke="#c0392b", sw=1.6, dash="6 4"); d.txt(BOX_W / 2, BOX_D, "rear panel line", py=14, fs=9, col="#c0392b")
bh = [(45.25, 0.0), (369.95, 0.0), (45.25, BOX_D), (369.95, BOX_D)]
for hx, hy in bh: d.hole(hx, hy, r=2.0)
d.txt(bh[0][0], bh[0][1], "4x M3 (drill 3.3, tap M3 or clear 3.4)", anc="start", px=14, py=-8, fs=10, col="#b03030")
d.dimh(0, SOX[0], d.Y(BOX_D) + 28, "45.25"); d.dimh(SOX[0], SOX[1], d.Y(BOX_D) + 28, "324.70"); d.dimh(SOX[1], BOX_W, d.Y(BOX_D) + 28, "45.35")
d.dimv(0, BOX_D, d.X(BOX_W) + 18, "196.85 (= hole Y span, at the panel lines)")
d.note(95, 400, ["Holes match the PCB's 4 M3 corner holes. X = 45.25 / 369.95 from the left interior wall;",
                 "Y ~ 0 / 196.85 (front/rear) - the hole rectangle (197.2) is 0.35 mm wider than the 196.85 interior,",
                 "so the holes sit right at the front/rear edges of the cover (against the panels)."])
made.append(d.save("5-bottom-cover"))

print("made:", made)
