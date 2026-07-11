#!/usr/bin/env python3
"""Build the single-channel PCB from the schematic netlist (track B1 chan-design).

4-layer board: F.Cu / In1.Cu(GND plane) / In2.Cu(-VDC plane) / B.Cu. Places every footprint
with an explicit, DRC-clean layout (signal flows left->right: bias/test inputs -> CR-112 ->
CR-200 -> CR-210 -> output buffer -> OUT_50), assigns nets from the netlist, draws the board
outline + M3 holes, sets net classes (incl. hv_bias 0.6mm), and adds GND/-VDC plane zones
(filled in a separate fill_zones.py pass). Routing is FreeRouting (DSN/SES) per docs/FREEROUTING.md.

The three SIP-8 Cremat modules are laid flat (rot 90, spanning x). MCX jacks are placed by
their footprint ORIGIN at the board edges (left end rot 270, right end rot 90) so the
edge-mount Edge.Cuts notch opens through the true board edge -- no GUI restore step needed.

Run: "C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py
Gate: kicad-cli pcb drc channel.kicad_pcb
"""
import os, re, json
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(HERE, "channel.net")
PCB = os.path.join(HERE, "channel.kicad_pcb")
PRO = os.path.join(HERE, "channel.kicad_pro")
DRU = os.path.join(HERE, "channel.kicad_dru")
STOCK_FP = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
CREMAT_FP = os.path.join(HERE, "lib", "cremat.pretty")

def mm(v): return pcbnew.FromMM(float(v))
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def fp_dir(nick):
    return CREMAT_FP if nick == "cremat" else "%s/%s.pretty" % (STOCK_FP, nick)

def parse_netlist(path):
    t = open(path, encoding="utf-8").read()
    comps = {}
    for cm in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)(?=\(comp\s|\(libparts)', t, re.S):
        ref, body = cm.group(1), cm.group(2)
        val = re.search(r'\(value "([^"]*)"\)', body)
        fp = re.search(r'\(footprint "([^"]*)"\)', body)
        uid = re.search(r'\(tstamps "([0-9a-fA-F-]{36})"\)', body)   # schematic symbol UUID
        comps[ref] = (val.group(1) if val else "", fp.group(1) if fp else "", uid.group(1) if uid else None)
    nets = {}
    sec = t[t.index("(nets"):]
    for nb in re.split(r'\n\s*\(net\b', sec)[1:]:
        nm = re.search(r'\(name "([^"]+)"', nb)
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', nb)
        if nm:
            nets[nm.group(1)] = nodes
    return comps, nets

# DNP refs (from the schematic spec: JP_Rf1, JP_Rf2, JP_BLR). Resolved by ref below.
def dnp_refs(comps):
    # match by value "0R" AND being a jumper -> the three 0R bypass jumpers are DNP-by-default.
    # JP_Rf1/JP_Rf2 (CSP front-end bypass) + JP_BLR (shaper BLR bypass). Identify by netlist role
    # is hard from .net; instead hardcode the role->ref mapping discovered from gen_sch ordering.
    return DNP_BY_REF

# ============================================================================================
# Board geometry: THIN, tile-able CHANNEL-ROW cell (2026-07). Anticipates the multi-channel
# board: each channel is a horizontal ROW (signal flows left->right), stacked vertically, with
# a shared COM row of common circuitry across the top (power input at the rear/top edge):
#
#     [======= COM row: J5 screw terminal + F1/F2 PTC + D1/D2 Schottky + C10/C11 bulk =======]
#     [SIPM]                                                                        [OUT_50]
#     [TEST]  frontend  CR-112   CR-200   CR-210   THS3491(buffer)  49.9            [BIAS_IN]
#      left-end MCX (IN/TEST)  --------- signal L->R ---------            right-end MCX (OUT/BIAS)
#
# MCX are edge-mount: left edge = SIPM(IN)+TEST, right edge = OUT_50+BIAS. Height is set by two
# stacked MCX per end (courtyard ~10x11.5) => channel row ~24 mm; keep the strip as thin as that.
# Refs (verified against channel.net, 2026-07 rework):
#   U1=CR-112 U2=CR-200 U3=CR-210 U4=THS3491(SOIC-8-1EP)
#   J1=BIAS J2=SIPM J3=TEST J4=OUT_50 J5=screw terminal
#   R1=Rf1 R2=JP_Rf1 R3=Rf2 R4=JP_Rf2 R5=R_test  R6/R7=CSP dec 4.7  R8/R9=CR200 dec  R10/R11=CR210 dec
#   R12=JP_BLR R13=R_FB(976) R14=R_GAIN(976) R15=R_BSER(49.9) R16/R17=buffer dec  R18=JP_BUF(0R,fit)
#   RV1=P/Z trim  C1=Cf C2=Cc C3=C_test  C4/C5=CSP 10uF  C6/C7=CR200 10uF  C8/C9=CR210 10uF
#   C10=C_BULKP C11=C_BULKN (100uF)  C12/C13=buffer 10uF
#   F1/F2=rail PTC (Fuse_1206)  D1/D2=rail Schottky SS14 (D_SMA)
W, H = 138.0, 52.0

# DNP by default (2026-07): bias/BLR bypass jumpers + the whole (bypassed) buffer block.
DNP_BY_REF = {"R2", "R4", "R12",                       # JP_Rf1, JP_Rf2, JP_BLR
              "U4", "R13", "R14", "R16", "R17", "C12", "C13"}   # THS3491 buffer block (JP_BUF R18 = FIT)

COM_Y    = 9.0     # COM row (power entry + protection + bulk) centre, near the rear/top edge
TOPDEC_Y = 26.0    # +rail decoupling row (top of the channel row)
MOD_Y    = 34.0    # module row centre
BOTDEC_Y = 42.0    # -rail decoupling row (bottom of the channel row)
MCX_TOP  = 29.0    # upper MCX (SIPM / OUT_50)
MCX_BOT  = 41.0    # lower MCX (TEST / BIAS)

PLACE = {
    # ===== COM row (shared): power entry -> reverse-polarity protection -> bulk =====
    "J5":  (24.0, COM_Y, 180),      # 3-pos screw terminal; rot 180 faces the wire entry OUT toward
                                    #                       the top edge (was 0 = funnels facing inboard)
    "F1":  (38.0,  6.0, 90), "D1": (44.0,  6.0, 90),   # +rail: PTC -> +VDC_F -> Schottky(cathode->+VDC)
    "F2":  (38.0, 13.0, 90), "D2": (44.0, 13.0, 90),   # -rail: PTC -> -VDC_F -> Schottky(anode->-VDC)
    "C10": (58.0, COM_Y, 0), "C11": (72.0, COM_Y, 0),  # 100uF bulk (+VDC / -VDC)
    # ===== left end: IN (SIPM) + TEST edge-mount MCX =====
    "J2":  (6.3, MCX_TOP, 270),     # SIPM (detector input) -- origin-placed; notch opens through x=0
    "J3":  (6.3, MCX_BOT, 270),     # TEST_IN
    # ===== SiPM bias front-end (near the left/detector end) =====
    "R1":  (19.0, 30.0, 0), "R2": (19.0, 33.0, 0),     # Rf1 / JP_Rf1(DNP)
    "C1":  (24.5, 28.0, 90),                            # Cf -> GND
    "R3":  (19.0, 38.0, 0), "R4": (19.0, 41.0, 0),     # Rf2 / JP_Rf2(DNP)
    "C2":  (24.5, 34.0, 90),                            # Cc (FE -> CSP_IN)
    "R5":  (18.0, 45.5, 0), "C3": (27.0, 45.5, 0),     # R_test(->GND) / C_test(->CSP_IN)
    # ===== CR-112 CSP + decoupling =====
    "U1":  (41.0, MOD_Y, 90),
    "R6":  (35.0, TOPDEC_Y, 0), "C4": (41.0, TOPDEC_Y, 0),   # +VS_F
    "R7":  (35.0, BOTDEC_Y, 0), "C5": (41.0, BOTDEC_Y, 0),   # -VS_F
    # ===== CR-200 shaper + P/Z trim + decoupling =====
    "U2":  (66.0, MOD_Y, 90),
    "RV1": (66.0, 46.0, 0),         # 200k P/Z trim (below CR-200)
    "R8":  (60.0, TOPDEC_Y, 0), "C6": (66.0, TOPDEC_Y, 0),   # SHVP
    "R9":  (60.0, BOTDEC_Y, 0), "C7": (74.0, BOTDEC_Y, 0),   # SHVN (clear of the trim)
    # ===== CR-210 BLR + decoupling + JP_BLR bypass =====
    "U3":  (91.0, MOD_Y, 90),
    "R10": (85.0, TOPDEC_Y, 0), "C8": (91.0, TOPDEC_Y, 0),   # BLVP
    "R11": (85.0, BOTDEC_Y, 0), "C9": (91.0, BOTDEC_Y, 0),   # BLVN
    "R12": (97.0, 46.0, 0),         # JP_BLR (DNP)
    # ===== THS3491 buffer + feedback + 49.9 back-term + JP_BUF + decoupling =====
    "U4":  (112.0, MOD_Y, 0),
    "R13": (108.0, 28.5, 0), "R14": (116.0, 28.5, 0),        # R_FB / R_GAIN (feedback, above amp)
    "R15": (112.0, 39.5, 90),       # 49.9 back-term
    "R18": (118.0, 45.5, 0),        # JP_BUF (0R, FIT)
    "R16": (106.0, TOPDEC_Y, 0), "C12": (112.0, TOPDEC_Y, 0),  # BVP (DNP)
    "R17": (106.0, BOTDEC_Y, 0), "C13": (118.0, BOTDEC_Y, 0),  # BVN (DNP)
    # ===== right end: OUT_50 + BIAS edge-mount MCX =====
    "J4":  (W - 6.3, MCX_TOP, 90),  # OUT_50 -- origin-placed; notch opens through x=W
    "J1":  (W - 6.3, MCX_BOT, 90),  # BIAS_IN (bias supply enters here; routes to the front-end)
}
MCX_REFS = ("J1", "J2", "J3", "J4")

def main():
    comps, nets = parse_netlist(NET)
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(4)
    try:
        b.SetLayerName(pcbnew.In1_Cu, "GND.Cu")
        b.SetLayerName(pcbnew.In2_Cu, "PWR.Cu")
    except Exception as e:
        print("layer name:", e)

    netmap = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(b, name)
        b.Add(ni); netmap[name] = ni
    pad_net = {}
    for name, nodes in nets.items():
        for ref, pad in nodes:
            pad_net[(ref, pad)] = name

    placed = miss = 0
    for ref in sorted(comps, key=lambda r: (r[0], int(re.sub(r'\D', '', r) or 0))):
        val, fpid, uid = comps[ref]
        if ":" not in fpid:
            miss += 1; print("no footprint id:", ref); continue
        nick, fname = fpid.split(":", 1)
        fp = pcbnew.FootprintLoad(fp_dir(nick), fname)
        if fp is None:
            miss += 1; print("MISS", fpid, ref); continue
        fp.SetFPID(pcbnew.LIB_ID(nick, fname))   # keep the library-prefixed FPID (matches 'Update from Sch'
                                                 # + lets DRC rules match A.Library_Link == 'cremat:...')
        fp.SetReference(ref); fp.SetValue(val)
        if uid:                                       # link footprint to its schematic symbol UUID
            fp.SetPath(pcbnew.KIID_PATH("/" + uid))    # so 'Update PCB from Schematic' matches, not re-adds
        if ref in DNP_BY_REF:
            try: fp.SetDNP(True)
            except Exception: pass
        x, y, rot = PLACE.get(ref, (5.0 + placed * 3.0, H - 4.0, 0))
        if rot:
            fp.SetOrientationDegrees(rot)
        if ref in MCX_REFS:
            # edge-mount jacks: place by footprint ORIGIN (pad/cutout are origin-referenced) so the
            # Edge.Cuts notch opens through the board edge, and keep the cutout ON Edge.Cuts.
            fp.SetPosition(V(x, y))
        else:
            # everything else: center the footprint bbox on (x, y)
            fp.SetPosition(V(0, 0))
            try: bb = fp.GetBoundingBox(False, False)
            except TypeError: bb = fp.GetBoundingBox()
            cx = (bb.GetLeft() + bb.GetRight()) / 2e6
            cy = (bb.GetTop() + bb.GetBottom()) / 2e6
            fp.SetPosition(V(x - cx, y - cy))
        b.Add(fp)
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in pad_net:
                pad.SetNet(netmap[pad_net[key]])
        placed += 1
    print("placed %d footprints, %d missing" % (placed, miss))

    # ---- silkscreen cleanup: hide ref labels that clip the board edge or overlap a neighbour
    # (MCX are at the edges; R2/R4 are DNP jumpers stacked under R1/R3; R13 sits over R16's pad).
    # Refs stay in the netlist/fab + assembly drawing; this only clears F.Silk DRC on a dense board.
    HIDE_SILK = {"J1", "J2", "J3", "J4", "R2", "R4", "R13"}
    for fp in b.GetFootprints():
        if fp.GetReference() in HIDE_SILK:
            fp.Reference().SetVisible(False)

    # board outline with edge notches for the edge-mount MCX jacks.  The MCX footprint carries a
    # CLOSED-rectangle Edge.Cuts cutout; a closed rect straddling the outline yields a malformed
    # (self-intersecting) board, so we instead CUT the notch into the outline and demote each
    # footprint's own cutout to Dwgs.User (reference).  Notch geometry is read back from the placed
    # footprints, so the outline always tracks wherever the MCX end up.
    EPS = 0.05
    notches = []   # (edge 'L'/'R', y0, y1, depth)
    for fp in b.GetFootprints():
        if "MCX_CONMCX013" not in str(fp.GetFPID().GetLibItemName()): continue
        ex = []; ey = []
        for it in fp.GraphicalItems():
            if it.GetLayer() == pcbnew.Edge_Cuts:
                for p in (it.GetStart(), it.GetEnd()):
                    ex.append(pcbnew.ToMM(p.x)); ey.append(pcbnew.ToMM(p.y))
                it.SetLayer(pcbnew.Dwgs_User)                       # demote so it can't overlap the outline
        if not ex: continue
        xlo, xhi, ylo, yhi = min(ex), max(ex), min(ey), max(ey)
        if abs(xlo) < EPS:        notches.append(('L', ylo, yhi, xhi))      # opens through x=0
        elif abs(xhi - W) < EPS:  notches.append(('R', ylo, yhi, W - xlo))  # opens through x=W
    Ln = sorted([n for n in notches if n[0] == 'L'], key=lambda n: n[1])
    Rn = sorted([n for n in notches if n[0] == 'R'], key=lambda n: n[1])
    pts = [(0, 0), (W, 0)]                                          # top edge L->R
    for _, y0, y1, d in Rn:                                         # right edge top->bottom, notch in to W-d
        pts += [(W, y0), (W - d, y0), (W - d, y1), (W, y1)]
    pts += [(W, H), (0, H)]                                         # bottom edge R->L
    for _, y0, y1, d in reversed(Ln):                              # left edge bottom->top, notch in to d
        pts += [(0, y1), (d, y1), (d, y0), (0, y0)]
    pts += [(0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(b); seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1)); b.Add(seg)
    print("outline: %d MCX edge notches (%dL / %dR)" % (len(notches), len(Ln), len(Rn)))

    # M3 mounting holes in the COM row (thin channel row has no spare height; corners tile away)
    try:
        for i, (hx, hy) in enumerate([(6.0, 6.0), (W-6.0, 6.0)], 1):
            h = pcbnew.FootprintLoad("%s/MountingHole.pretty" % STOCK_FP, "MountingHole_3.2mm_M3")
            if h:
                h.SetReference("H%d" % i); h.SetPosition(V(hx, hy))
                h.Reference().SetVisible(False)
                try: h.SetBoardOnly(True)              # mechanical: not in schematic (Update-from-Sch ignores it)
                except Exception: pass
                b.Add(h)
    except Exception as e:
        print("mounting holes:", e)

    # plane pours: GND on In1.Cu, -VDC on In2.Cu (outer layers free for routing)
    def add_plane(net_name, layer, prio=None, rect=None):
        ni = netmap.get(net_name)
        if not ni:
            print("no net for plane:", net_name); return
        z = pcbnew.ZONE(b)
        z.SetLayer(layer); z.SetNetCode(ni.GetNetCode()); z.SetIsFilled(True)
        if prio is not None:
            z.SetAssignedPriority(prio)
        ch = z.Outline(); ch.NewOutline()
        r = rect or [(1.5, 1.5), (W-1.5, 1.5), (W-1.5, H-1.5), (1.5, H-1.5)]
        for (px, py) in r:
            ch.Append(mm(px), mm(py))
        b.Add(z)
        print("%s plane on layer %d (fill via fill_zones.py)" % (net_name, layer))
    try:
        # Inner planes: GND (In1) and -VDC (In2). +VDC has no inner plane, so it gets a
        # dedicated B.Cu pour (low priority) -> every +VDC pad ties to copper without the
        # router having to thread pad-to-pad +VDC tracks through the dense bottom strip.
        # GND gets the higher-priority outer fill in fill_zones.py; +VDC pour sits under it
        # where GND isn't, and signal/GND tracks on B.Cu carve around it. This keeps both
        # supply rails low-impedance and routes 100%.
        add_plane("GND", pcbnew.In1_Cu)
        add_plane("-VDC", pcbnew.In2_Cu)
        add_plane("+VDC", pcbnew.B_Cu, prio=1)
    except Exception as e:
        print("zone:", e)

    write_dru()
    pcbnew.SaveBoard(PCB, b)
    print("saved", PCB)
    write_netclasses()

def write_dru():
    # The MCX edge-mount shield pads (pad 2) sit at the slot edge by design (the connector's
    # ground shell nests in the notch), so waive edge-clearance for that footprint only.
    open(DRU, "w", encoding="utf-8").write(
        '(version 1)\n'
        '(rule "MCX edge-mount shield pad straddles its slot by design"\n'
        '   (constraint edge_clearance (min -2mm))\n'
        '   (condition "A.Library_Link == \'cremat:MCX_CONMCX013-T\'"))\n')

def write_netclasses():
    if not os.path.exists(PRO):
        return
    d = json.load(open(PRO, encoding="utf-8"))
    ns = d.setdefault("net_settings", {})
    # hv_bias 0.6mm (IPC-2221 external creepage for <=60V bias) on BIAS/SIPM/FE/N_filt;
    # signal 0.33mm on the amplifier nets; power 0.5mm on rails. (Identical scheme to Phase A.)
    ns["classes"] = [
        {"name": "Default", "clearance": 0.2, "track_width": 0.2032, "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "power",   "clearance": 0.2, "track_width": 0.5,    "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "hv_bias", "clearance": 0.6, "track_width": 0.4,    "via_diameter": 0.9, "via_drill": 0.4},
        {"name": "signal",  "clearance": 0.2, "track_width": 0.33,   "via_diameter": 0.8, "via_drill": 0.4},
    ]
    ns["netclass_patterns"] = [
        {"netclass": "hv_bias", "pattern": "*BIAS*"}, {"netclass": "hv_bias", "pattern": "*SIPM*"},
        {"netclass": "hv_bias", "pattern": "FE"}, {"netclass": "hv_bias", "pattern": "N_filt"},
        {"netclass": "signal",  "pattern": "*CSP_OUT*"}, {"netclass": "signal", "pattern": "*CSP_IN*"},
        {"netclass": "signal",  "pattern": "SH_OUT"}, {"netclass": "signal", "pattern": "BLR_OUT"},
        {"netclass": "signal",  "pattern": "SHAPER_OUT"}, {"netclass": "signal", "pattern": "*OUT_50*"},
        {"netclass": "signal",  "pattern": "BUF_*"},
        {"netclass": "power", "pattern": "GND"}, {"netclass": "power", "pattern": "+VDC"},
        {"netclass": "power", "pattern": "-VDC"},
        {"netclass": "power", "pattern": "*VDC_IN*"}, {"netclass": "power", "pattern": "*VDC_F*"},
        {"netclass": "power", "pattern": "*VS_F*"},
        {"netclass": "power", "pattern": "SHVP"}, {"netclass": "power", "pattern": "SHVN"},
        {"netclass": "power", "pattern": "BLVP"}, {"netclass": "power", "pattern": "BLVN"},
        {"netclass": "power", "pattern": "BVP"}, {"netclass": "power", "pattern": "BVN"},
    ]
    json.dump(d, open(PRO, "w", encoding="utf-8"), indent=2)
    print("re-applied net classes (.kicad_pro)")

if __name__ == "__main__":
    main()
