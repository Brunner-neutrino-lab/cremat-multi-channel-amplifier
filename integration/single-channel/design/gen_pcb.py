#!/usr/bin/env python3
"""Build the single-channel PCB from the schematic netlist (track B1 chan-design).

4-layer board: F.Cu / In1.Cu(GND plane) / In2.Cu(-VDC plane) / B.Cu. Places every footprint
with an explicit, DRC-clean layout (signal flows left->right: bias/test inputs -> CR-112 ->
CR-200 -> CR-210 -> output buffer -> OUT_50), assigns nets from the netlist, draws the board
outline + M3 holes, sets net classes (incl. hv_bias 0.6mm), and adds GND/-VDC plane zones
(filled in a separate fill_zones.py pass). Routing is FreeRouting (DSN/SES) per docs/FREEROUTING.md.

The three SIP-8 Cremat modules are laid flat (rot 90, spanning x). MCX jacks hug the board
edges with their Edge.Cuts cutout parked on Dwgs.User (restore in GUI at the true edge).

Run: "C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py
Gate: kicad-cli pcb drc channel.kicad_pcb
"""
import os, re, json
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(HERE, "channel.net")
PCB = os.path.join(HERE, "channel.kicad_pcb")
PRO = os.path.join(HERE, "channel.kicad_pro")
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
        dnp = "(dnp)" in body or '(exclude_from_bom)' in body  # fallback; real DNP set below
        comps[ref] = (val.group(1) if val else "", fp.group(1) if fp else "")
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

# Board geometry: single-channel cell. Phase C shrinks/tiles; topology is what's reused.
# W=164 gives the OUT_50 jack + its GND routing >=0.5mm board-edge clearance on the right.
W, H = 164.0, 90.0

# Explicit placement: ref -> (x_mm, y_mm, rotation_deg). Hand-laid for a clean DRC.
# Refs follow gen_sch's per-prefix counter assignment (verified against channel.net, Round 2):
#   U1=CR-112  U2=CR-200  U3=CR-210  U4=THS3491 buffer (SOIC-8-1EP)
#   J1=BIAS J2=SIPM J3=TEST J4=OUT_50 J5=PWR
#   R1=Rf1 R2=JP_Rf1 R3=Rf2 R4=JP_Rf2 R5=R_test R6=R_dvp R7=R_dvn
#   R8=R_SHP R9=R_SHN R10=R_BLP R11=R_BLN R12=JP_BLR
#   R13=R_FB(976) R14=R_GAIN(976) R15=R_BSER(49.9 back-term) R16=R_BVP R17=R_BVN
#   RV1=P/Z trim
#   C1=Cf C2=Cc C3=C_test C4=Cp1 C5=Cp2 C6=Cn1 C7=Cn2
#   C8=C_SHPb C9=C_SHPh C10=C_SHNb C11=C_SHNh  C12=C_BLPb C13=C_BLPh C14=C_BLNb C15=C_BLNh
#   C16=C_BULKP C17=C_BULKN (100uF SMD, ONE pair)  C18=C_BVPb C19=C_BVPh C20=C_BVNb C21=C_BVNh
# (Round-2 deltas: removed CSP radial bulk Cb_p/Cb_n + shaper 49.9 R_OUT -> caps/Rs renumbered;
#  buffer is now SOIC-8-1EP not SOT-23-5; Rf/Rg=976R (THS3491 datasheet G=+2 value).)
DNP_BY_REF = {"R2", "R4", "R12"}   # JP_Rf1, JP_Rf2, JP_BLR (populate-XOR bypass jumpers)
MAIN_Y = 45.0      # signal row
TOPDEC_Y = 18.0    # +rail decoupling row
BOTDEC_Y = 72.0    # -rail decoupling row

PLACE = {
    # ----- left edge: bias + test inputs (MCX) -----
    "J1": (9.0,  22.0, 0),     # BIAS_IN  (left edge, upper)
    "J3": (9.0,  68.0, 0),     # TEST_IN  (left edge, lower)
    # ----- bias filter chain: BIAS -> Rf1/0R -> N_filt(-Cf) -> Rf2/0R -> FE -----
    "R1": (24.0, 30.0, 0),     # Rf1 10k
    "R2": (24.0, 34.0, 0),     # JP_Rf1 0R (DNP) parallel
    "C1": (31.0, 38.0, 90),    # Cf 100nF/100V -> GND
    "R3": (38.0, 30.0, 0),     # Rf2 10k
    "R4": (38.0, 34.0, 0),     # JP_Rf2 0R (DNP) parallel
    # SIPM jack (DC-coupled to FE), top edge
    "J2": (46.0, 9.0, 180),    # SIPM MCX (top edge)
    "C2": (46.0, 22.0, 0),     # Cc 0.22uF/100V (FE -> CSP_IN)
    # test injection
    "R5": (24.0, 60.0, 0),     # R_test 47
    "C3": (38.0, 60.0, 0),     # C_test 1pF (TEST_N -> CSP_IN)
    # ----- CR-112 CSP module (SIP-8 flat) + its decoupling -----
    "U1": (60.0, 45.0, 90),    # CR-112 (rot 90: spans x ~49..71 along the row)
    "R6": (54.0, TOPDEC_Y, 0), "C4": (61.0, TOPDEC_Y, 0), "C5": (67.0, TOPDEC_Y, 0),   # +VS_F
    "R7": (54.0, BOTDEC_Y, 0), "C6": (61.0, BOTDEC_Y, 0), "C7": (67.0, BOTDEC_Y, 0),   # -VS_F
    # ----- CR-200 shaper (SIP-8 flat) + P/Z trim + decoupling -----
    "U2": (85.0, 45.0, 90),    # CR-200
    "RV1":(85.0, 62.0, 0),     # 200k P/Z trim (below CR-200)
    "R8": (79.0, TOPDEC_Y, 0), "C8": (86.0, TOPDEC_Y, 0), "C9": (92.0, TOPDEC_Y, 0),   # SHVP
    "R9": (74.0, BOTDEC_Y, 0), "C10":(81.0, BOTDEC_Y, 0), "C11":(95.0, BOTDEC_Y, 0),   # SHVN (flank the trim)
    # ----- CR-210 BLR (SIP-8 flat) + decoupling + JP_BLR bypass -----
    "U3": (108.0, 45.0, 90),   # CR-210 (out = SHAPER_OUT, feeds buffer +IN directly)
    "R10":(102.0, TOPDEC_Y, 0),"C12":(109.0,TOPDEC_Y, 0),"C13":(115.0,TOPDEC_Y, 0),    # BLVP
    "R11":(102.0, BOTDEC_Y, 0),"C14":(109.0,BOTDEC_Y, 0),"C15":(115.0,BOTDEC_Y, 0),    # BLVN
    "R12":(108.0, 60.0, 0),    # JP_BLR 0R (DNP)
    # ----- output buffer (THS3491 SOIC-8-1EP) + gain net + 49.9 back-term + decoupling -----
    "U4": (134.0, 45.0, 0),    # THS3491 buffer (bbox 7.5x5.6)
    "R13":(132.0, 56.0, 0),    # R_FB 976R (OUT -> -IN)
    "R14":(140.0, 56.0, 0),    # R_GAIN 976R (-IN -> GND)
    "R15":(143.0, 45.0, 90),   # R_BSER 49.9 (BUF_OUT -> OUT_50, 50R back-term)
    "R16":(126.0, TOPDEC_Y, 0),"C18":(133.0,TOPDEC_Y, 0),"C19":(139.0,TOPDEC_Y, 0),    # BVP
    "R17":(126.0, BOTDEC_Y, 0),"C20":(133.0,BOTDEC_Y, 0),"C21":(139.0,BOTDEC_Y, 0),    # BVN
    # output jack (right edge); J4 center 152 -> body right ~157, >=2.5mm to the 160 edge
    "J4": (152.0, 45.0, 0),    # OUT_50 MCX (right edge)
    # ----- power entry + rail bulk (bottom strip, y=82, clear of mounting holes at x=5.5/W-5.5) -----
    "J5": (20.0, 82.0, 0),     # +12V/GND/-12V screw terminal (bottom-left, right of H3)
    "C16":(95.0, 82.0, 0),     # C_BULKP 100uF SMD (+VDC)
    "C17":(112.0, 82.0, 0),    # C_BULKN 100uF SMD (-VDC)
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
        val, fpid = comps[ref]
        if ":" not in fpid:
            miss += 1; print("no footprint id:", ref); continue
        nick, fname = fpid.split(":", 1)
        fp = pcbnew.FootprintLoad(fp_dir(nick), fname)
        if fp is None:
            miss += 1; print("MISS", fpid, ref); continue
        fp.SetReference(ref); fp.SetValue(val)
        if ref in DNP_BY_REF:
            try: fp.SetDNP(True)
            except Exception: pass
        x, y, rot = PLACE.get(ref, (5.0 + placed * 3.0, H - 4.0, 0))
        if rot:
            fp.SetOrientationDegrees(rot)
        # center the footprint bbox on (x, y)
        fp.SetPosition(V(0, 0))
        try: bb = fp.GetBoundingBox(False, False)
        except TypeError: bb = fp.GetBoundingBox()
        cx = (bb.GetLeft() + bb.GetRight()) / 2e6
        cy = (bb.GetTop() + bb.GetBottom()) / 2e6
        fp.SetPosition(V(x - cx, y - cy))
        if ref in MCX_REFS:
            for it in fp.GraphicalItems():
                if it.GetLayer() == pcbnew.Edge_Cuts:
                    it.SetLayer(pcbnew.Dwgs_User)
        b.Add(fp)
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in pad_net:
                pad.SetNet(netmap[pad_net[key]])
        placed += 1
    print("placed %d footprints, %d missing" % (placed, miss))

    # board outline
    pts = [(0, 0), (W, 0), (W, H), (0, H), (0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(b); seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1)); b.Add(seg)

    # 4x M3 mounting holes
    try:
        for i, (hx, hy) in enumerate([(5.5, 5.5), (W-5.5, 5.5), (5.5, H-5.5), (W-5.5, H-5.5)], 1):
            h = pcbnew.FootprintLoad("%s/MountingHole.pretty" % STOCK_FP, "MountingHole_3.2mm_M3")
            if h:
                h.SetReference("H%d" % i); h.SetPosition(V(hx, hy))
                h.Reference().SetVisible(False); b.Add(h)
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

    pcbnew.SaveBoard(PCB, b)
    print("saved", PCB)
    write_netclasses()

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
        {"netclass": "power", "pattern": "*VS_F*"},
        {"netclass": "power", "pattern": "SHVP"}, {"netclass": "power", "pattern": "SHVN"},
        {"netclass": "power", "pattern": "BLVP"}, {"netclass": "power", "pattern": "BLVN"},
        {"netclass": "power", "pattern": "BVP"}, {"netclass": "power", "pattern": "BVN"},
    ]
    json.dump(d, open(PRO, "w", encoding="utf-8"), indent=2)
    print("re-applied net classes (.kicad_pro)")

if __name__ == "__main__":
    main()
