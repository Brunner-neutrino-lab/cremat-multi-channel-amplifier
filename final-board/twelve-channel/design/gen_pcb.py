#!/usr/bin/env python3
"""Build the TWELVE-CHANNEL PCB from the schematic netlist (Phase C, track C1).

4-layer board: F.Cu / In1.Cu(GND plane) / In2.Cu(-VDC plane) / B.Cu(+VDC pour) -- the
exact proven stackup from the single channel (it routed 100%). Places 12 copies of the
frozen single-channel cell as horizontal bands, signal flowing left->right:

   left edge (input)  : BIAS + SIPM MCX (24 jacks)
   right edge (output): OUT_50 + TEST_IN MCX (24 jacks)         [see TEST_IN note below]
   band interior      : bias filter -> CR-112 -> CR-200 -> CR-210 -> THS3491 buffer

=====================  R1 (single source of truth)  =====================
Placement REPLAYS gen_sch's (channel,role)->ref assignment (which itself iterates the
IMPORTED single-channel spec). The per-channel relative layout LAYOUT[] is the only
PCB-specific data; everything electrical (parts, nets, DNP, footprints) comes from the
single-channel cell via the netlist. Edit the channel cell -> regenerate sch+net -> this
script restamps all 12.

=====================  R2 (schematic-parity-clean)  =====================
For every footprint we (a) set the **lib-qualified FPID** (nick:fname) matching the
symbol Footprint field, and (b) copy the symbol's **MPN / Manufacturer / Distributor PN**
(+ Value) into footprint fields. Mounting holes have real schematic symbols (H1..H4), so
there are no extra_footprints. Result: `kicad-cli pcb drc --schematic-parity
--severity-warning` = 0 parity items.

=====================  TEST_IN / MCX count (FLAGGED)  =====================
The frozen channel cell has 4 MCX (BIAS_IN, SIPM, TEST_IN, OUT_50) -> 48 MCX for 12 ch.
The brief/mechanical.md assume 36 MCX (3/ch, dropping per-channel TEST_IN -> 24 input
jacks on one edge). R1 forbids silently dropping TEST_IN (the 12 must be true copies), so
we KEEP all 48 MCX and balance them 24/24 on the two long edges (BIAS+SIPM left,
OUT_50+TEST_IN right). Coordinator decision pending. See ../INTERFACE.md + SESSION_REPORT.md.

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py
Gate: kicad-cli pcb drc multi-channel-cremat-amplifier.kicad_pcb
"""
import os, re, sys, json, importlib.util
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
SC_DESIGN = os.path.abspath(os.path.join(HERE, "..", "..", "..",
                                         "integration", "single-channel", "design"))

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m

# Both files are literally named gen_sch.py -> load each under a DISTINCT module name so the
# single-channel cell (R1 source) and this board's replicator don't collide in sys.modules.
sc = _load("sc_gen_sch", os.path.join(SC_DESIGN, "gen_sch.py"))            # FROZEN single channel
board_sch = _load("board_gen_sch", os.path.join(HERE, "gen_sch.py"))      # this board's replicator

PROJ = "multi-channel-cremat-amplifier"
NET = os.path.join(HERE, PROJ + ".net")
PCB = os.path.join(HERE, PROJ + ".kicad_pcb")
PRO = os.path.join(HERE, PROJ + ".kicad_pro")
STOCK_FP = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
CREMAT_FP = os.path.join(HERE, "lib", "cremat.pretty")
NCH = 12

def mm(v): return pcbnew.FromMM(float(v))
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def fp_dir(nick):
    return CREMAT_FP if nick == "cremat" else "%s/%s.pretty" % (STOCK_FP, nick)

# ---------- netlist parse: ref -> (value, fpid); net -> [(ref,pad)] ----------
def parse_netlist(path):
    t = open(path, encoding="utf-8").read()
    comps = {}
    for cm in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)(?=\(comp\s|\(libparts)', t, re.S):
        ref, body = cm.group(1), cm.group(2)
        val = re.search(r'\(value "([^"]*)"\)', body)
        fp = re.search(r'\(footprint "([^"]*)"\)', body)
        comps[ref] = (val.group(1) if val else "", fp.group(1) if fp else "")
    nets = {}
    sec = t[t.index("(nets"):]
    for nb in re.split(r'\n\s*\(net\b', sec)[1:]:
        nm = re.search(r'\(name "([^"]+)"', nb)
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', nb)
        if nm:
            nets[nm.group(1)] = nodes
    return comps, nets

# ---------- MPN/field metadata per ref (R2): from the single-channel PARTS, keyed by role ----------
# Build (channel, role) -> ref exactly like board_sch.build() does, so we can map ref -> role
# -> PARTS fields. board_sch iterates the per-channel spec (J_PWR excluded) with a global
# per-prefix counter; then the shared screw terminal; then 4 mounting holes.
def build_ref_role_maps():
    full_spec = sc.build_spec()
    spec = [r for r in full_spec if r[0] not in board_sch.BOARD_LEVEL_ROLES]
    cnt = {}
    ref_role = {}            # ref -> (channel, role)
    role_refs = {}           # (channel, role) -> ref
    for n in range(1, NCH + 1):
        for role, *_ in spec:
            pfx = board_sch.prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1
            ref = "%s%d" % (pfx, cnt[pfx])
            ref_role[ref] = (n, role); role_refs[(n, role)] = ref
    # shared parts, in the SAME emission order as board_sch.build(): screw terminal, then the
    # two central bulk caps (C++), then 4 mounting holes (H++).
    cnt["J"] = cnt.get("J", 0) + 1
    jpwr = "J%d" % cnt["J"]; ref_role[jpwr] = (0, "J_PWR"); role_refs[(0, "J_PWR")] = jpwr
    for role in ("CBULK_P", "CBULK_N"):
        cnt["C"] = cnt.get("C", 0) + 1
        cref = "C%d" % cnt["C"]; ref_role[cref] = (0, role); role_refs[(0, role)] = cref
    for i in range(1, 5):
        cnt["H"] = cnt.get("H", 0) + 1
        href = "H%d" % cnt["H"]; ref_role[href] = (0, "MH"); role_refs[(0, "MH")] = href
    return ref_role, role_refs, spec

# DNP roles in the single-channel cell (populate-or-bypass jumpers): JP_Rf1, JP_Rf2, JP_BLR.
DNP_ROLES = {role for role, *rest in sc.build_spec() if rest[3]}   # rest[3] = dnp flag

# =================================  GEOMETRY  =================================
# Board outline: width carries the L->R signal chain; height stacks 12 channel bands and
# carries 24 edge jacks per long edge (BIAS+SIPM left, OUT_50+TEST right). Each MCX courtyard
# is 9.9mm along the edge, so 24 jacks need >= 24*10.4 ~ 250mm of clean edge; H set to 255mm
# (slightly over mechanical.md's ~235 budget -- the extra is forced by keeping all 48 MCX /
# TEST_IN per R1; flagged for the coordinator). Width 235mm carries the chain + edge jacks.
# NOTE (FLAGGED): keeping all 48 MCX (TEST_IN per R1) puts 24 jacks on each long edge. At
# the MCX 9.91mm courtyard + 0.5mm board-edge clearance, 24 jacks + a power strip need ~250mm
# of height -- ~6mm over mechanical.md's ~244mm tray-depth budget. Dropping TEST_IN (->36 MCX,
# 24 input jacks on ONE edge) brings it back under 244. Coordinator decision pending.
W, H = 235.0, 254.0
EDGE_IN_X = 0.0           # left edge: input jacks (BIAS,SIPM)
EDGE_OUT_X = W           # right edge: output jacks (OUT_50,TEST_IN)
# 24 jack slots per edge, uniform pitch over the usable height; channel n owns slots
# (2n-2, 2n-1). The band centerline is the midpoint of channel n's jack pair. Pitch 10.0 >
# the 9.91mm MCX courtyard -> adjacent jacks clear by ~0.09mm + the 0.1mm DRC margin holds.
JACK_Y0 = 12.0           # first jack slot center (leaves a top strip for power + mtg holes)
JACK_PITCH = 10.0        # 24 slots: 12 + 23*10 = 242 (last slot center); body 9.9 -> clears H
                         # (>=3mm to the bottom edge so autorouted escapes hold 0.5mm edge clr)
def band_center(n):      # n = 1..12
    return JACK_Y0 + (2 * (n - 1) + 0.5) * JACK_PITCH
def jack_slot_y(slot):   # slot = 0..23
    return JACK_Y0 + slot * JACK_PITCH

# Per-channel RELATIVE layout: role -> (dx, dy, rot). dx is x within the band interior
# (signal flows L->R); dy is +-offset from the band centerline; rot in degrees.
# Interior chain occupies x ~ 20..210 (jacks live at the true edges, set separately).
# Two interior tiers: signal devices on the centerline (dy~0), decoupling 0805s on a sub-row
# just above (dy=-6) and below (dy=+6). SIP modules laid flat (rot 90 -> 21.4mm wide, 3.6 tall).
SIG = 0.0
DUP = -6.3   # upper decoupling sub-row
DDN = +6.3   # lower decoupling sub-row
LAYOUT = {
    # bias filter chain (left interior)
    "Rf1":   (22.0, -3.0, 0), "JP_Rf1": (22.0, +1.0, 0),
    "Cf":    (27.0, +5.0, 90),
    "Rf2":   (32.0, -3.0, 0), "JP_Rf2": (32.0, +1.0, 0),
    "Cc":    (40.0, -3.0, 0),
    # test injection (interior, feeds CSP_IN; J_TEST jack itself is on the right edge)
    "R_test":(22.0, +6.0, 0), "C_test": (32.0, +6.0, 0),
    # CR-112 CSP (flat) + decoupling
    "U_CSP": (62.0, SIG, 90),
    "R_dvp": (52.0, DUP, 0), "Cp1": (57.0, DUP, 0), "Cp2": (62.0, DUP, 0),
    "R_dvn": (52.0, DDN, 0), "Cn1": (57.0, DDN, 0), "Cn2": (62.0, DDN, 0),
    # CR-200 shaper (flat) + P/Z trim + decoupling
    "U_SH":  (92.0, SIG, 90),
    "RV_PZ": (92.0, DDN + 2.5, 0),
    "R_SHP": (82.0, DUP, 0), "C_SHPb": (87.0, DUP, 0), "C_SHPh": (92.0, DUP, 0),
    "R_SHN": (78.0, DDN, 0), "C_SHNb": (101.0, DDN, 0), "C_SHNh": (106.0, DDN, 0),
    # CR-210 BLR (flat) + decoupling + bypass jumper
    "U_BLR": (122.0, SIG, 90),
    "R_BLP": (112.0, DUP, 0), "C_BLPb": (117.0, DUP, 0), "C_BLPh": (122.0, DUP, 0),
    "R_BLN": (112.0, DDN, 0), "C_BLNb": (117.0, DDN, 0), "C_BLNh": (122.0, DDN, 0),
    "JP_BLR":(135.0, SIG, 0),
    # output buffer (THS3491) + gain net + 49.9 back-term + decoupling
    "U_BUF": (158.0, SIG, 0),
    "R_FB":  (152.0, DDN, 0), "R_GAIN": (158.0, DDN, 0), "R_BSER": (168.0, SIG, 0),
    "R_BVP": (148.0, DUP, 0), "C_BVPb": (153.0, DUP, 0), "C_BVPh": (158.0, DUP, 0),
    "R_BVN": (164.0, DUP, 0), "C_BVNb": (169.0, DUP, 0), "C_BVNh": (174.0, DUP, 0),
    # per-channel rail bulk (100uF SMD), tucked at the right interior
    "C_BULKP": (185.0, DUP, 0), "C_BULKN": (185.0, DDN, 0),
}
# Edge jacks: (edge_x, slot_within_channel 0|1, rot). The rotation is chosen so the connector
# SLOT faces OUTBOARD (toward the board edge) and the SIGNAL pad 1 faces INBOARD -- this is
# critical: with the slot inboard of pad 1 (the naive rotation) the slot is a routing keepout
# directly across pad 1's escape path and the autorouter strands the BIAS/SIPM nets (34 unrouted
# on 4-layer planes). Left edge -> rot -90 (slot at -x, toward x=0); right edge -> rot +90 (slot
# at +x, toward x=W). Slot ends up a near-edge internal cutout; pad 1 escapes freely.
JACK_EDGE = {
    "J_BIAS":  (EDGE_IN_X,  0, -90),   # left edge, first slot of the pair (slot outboard)
    "J_SIPM":  (EDGE_IN_X,  1, -90),   # left edge, second slot
    "J_OUT50": (EDGE_OUT_X, 0, 90),    # right edge, first slot (slot outboard)
    "J_TEST":  (EDGE_OUT_X, 1, 90),    # right edge, second slot
}
MCX_ROLES = ("J_BIAS", "J_SIPM", "J_TEST", "J_OUT50")
SIP_ROLES = ("U_CSP", "U_SH", "U_BLR")

def bbox_mm(fp):
    try: bb = fp.GetBoundingBox(False, False)
    except TypeError: bb = fp.GetBoundingBox()
    return (bb.GetLeft() / 1e6, bb.GetRight() / 1e6, bb.GetTop() / 1e6, bb.GetBottom() / 1e6)

# Board-shared parts not in the single-channel cell (their MPN fields, mirroring gen_sch).
# Keys match the role names used in placement. (Mounting holes carry no MPN -> none here.)
SHARED_PARTS = {
    "CBULK_P": ("470uF 35V", "UVR1V471MPD", "Nichicon", "493-1084-ND"),
    "CBULK_N": ("470uF 35V", "UVR1V471MPD", "Nichicon", "493-1084-ND"),
}

def set_fp_fields(fp, nick, fname, ref, val, role):
    """R2: lib-qualified FPID + copy MPN/Manufacturer/Distributor PN + Value into the footprint."""
    fp.SetFPID(pcbnew.LIB_ID(nick, fname))
    fp.SetReference(ref); fp.SetValue(val)
    meta = sc.PARTS.get(role) or SHARED_PARTS.get(role)
    if meta:
        _v, mpn, mfr, dkpn = meta
        for k, v in (("MPN", mpn), ("Manufacturer", mfr), ("Distributor PN", dkpn)):
            try:
                fp.SetField(k, v)             # KiCad 8+/9/10 footprint custom field
            except Exception:
                try:
                    pf = pcbnew.PCB_FIELD(fp, fp.GetFieldCount(), k); pf.SetText(v); fp.Add(pf)
                except Exception:
                    pass

# MCX footprint origin geometry. With the slot-OUTBOARD rotations (left=-90, right=+90) the
# slot spans [origin-6.3 .. origin] (left) / [origin .. origin+6.3] (right) and the signal pad 1
# is INBOARD of the slot. SLOT_DEPTH places the slot's OUTER wall ~0.6mm in from the perimeter
# (clears the 0.5mm outline-to-slot rule); the slot is then a near-edge internal cutout and
# pad 1 (a further ~2.7mm inboard) escapes toward the channel with no slot in its path.
SLOT_DEPTH = 6.3        # slot length from the footprint origin (the connector cutout depth)
SLOT_EDGE_GAP = 0.6     # outer slot wall this far in from the board perimeter

def place(b, fp, role, n, netmap, pad_net):
    rot = 0
    if role in JACK_EDGE:
        ex, slot, rot = JACK_EDGE[role]
        fp.SetOrientationDegrees(rot)
        jy = jack_slot_y(2 * (n - 1) + slot)        # absolute Y from the 24-slot edge ladder
        # left (rot -90): slot = [origin-6.3, origin]; put slot outer (origin-6.3) at SLOT_EDGE_GAP
        #   -> origin = SLOT_EDGE_GAP + 6.3. right (rot +90): slot = [origin, origin+6.3]; outer
        #   (origin+6.3) at W-SLOT_EDGE_GAP -> origin = W - SLOT_EDGE_GAP - 6.3.
        if ex == EDGE_IN_X:
            ox = SLOT_EDGE_GAP + SLOT_DEPTH         # left edge
        else:
            ox = W - SLOT_EDGE_GAP - SLOT_DEPTH     # right edge
        fp.SetPosition(V(ox, jy))
    else:
        dx, dy, rot = LAYOUT[role]
        if role in SIP_ROLES:
            rot = 90
        if rot:
            fp.SetOrientationDegrees(rot)
        fp.SetPosition(V(0, 0)); L, R, T, B = bbox_mm(fp)
        cx = (L + R) / 2.0; cy = (T + B) / 2.0
        fp.SetPosition(V(dx - cx, band_center(n) + dy - cy))
    # MCX cutout stays ON Edge.Cuts (an internal slot) so it is part of the fab profile AND the
    # autorouter treats it as a keepout. (No Dwgs.User parking -- that was the old fab blocker.)
    b.Add(fp)
    for pad in fp.Pads():
        key = (fp.GetReference(), pad.GetNumber())
        if key in pad_net:
            pad.SetNet(netmap[pad_net[key]])

def main():
    comps, nets = parse_netlist(NET)
    ref_role, role_refs, spec = build_ref_role_maps()

    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(4)
    try:
        b.SetLayerName(pcbnew.In1_Cu, "GND.Cu")
        b.SetLayerName(pcbnew.In2_Cu, "PWR.Cu")
    except Exception as e:
        print("layer name:", e)

    netmap = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); netmap[name] = ni
    pad_net = {}
    for name, nodes in nets.items():
        for ref, pad in nodes:
            pad_net[(ref, pad)] = name

    placed = miss = 0
    # --- 12 channel bands ---
    for n in range(1, NCH + 1):
        dnp_refs_n = {role_refs[(n, r)] for r in DNP_ROLES if (n, r) in role_refs}
        for role, *_ in spec:
            ref = role_refs[(n, role)]
            val, fpid = comps.get(ref, ("", ""))
            if ":" not in fpid:
                miss += 1; print("no fpid:", ref); continue
            nick, fname = fpid.split(":", 1)
            fp = pcbnew.FootprintLoad(fp_dir(nick), fname)
            if fp is None:
                miss += 1; print("MISS", fpid, ref); continue
            set_fp_fields(fp, nick, fname, ref, val, role)
            if ref in dnp_refs_n:
                try: fp.SetDNP(True)
                except Exception: pass
            place(b, fp, role, n, netmap, pad_net)
            placed += 1

    # --- shared screw terminal (top strip, above channel-1's jack ladder) ---
    jpwr = role_refs[(0, "J_PWR")]
    val, fpid = comps[jpwr]; nick, fname = fpid.split(":", 1)
    fp = pcbnew.FootprintLoad(fp_dir(nick), fname)
    set_fp_fields(fp, nick, fname, jpwr, val, "J_PWR")
    fp.SetPosition(V(0, 0)); L, R, T, B = bbox_mm(fp)
    # top strip, in the x-gap between channel-1's BLR decoupling (ends ~x124) and buffer
    # decoupling (starts ~x146) so it clears band-1's parts.
    fp.SetPosition(V(135.0 - (L + R) / 2.0, 6.5 - (T + B) / 2.0))
    b.Add(fp)
    for pad in fp.Pads():
        key = (jpwr, pad.GetNumber())
        if key in pad_net:
            pad.SetNet(netmap[pad_net[key]])
    placed += 1

    # --- central rail-entry bulk caps CBULK_P/CBULK_N (470uF radial THT, C2 gate). Top strip,
    # right of the per-channel bulk and clear of channel-1's parts + the right-edge jacks. ---
    for role, (cxp, cyp) in (("CBULK_P", (196.0, 9.0)), ("CBULK_N", (208.0, 9.0))):
        cref = role_refs[(0, role)]
        val, fpid = comps[cref]; nick, fname = fpid.split(":", 1)
        cfp = pcbnew.FootprintLoad(fp_dir(nick), fname)
        set_fp_fields(cfp, nick, fname, cref, val, role)
        cfp.SetPosition(V(0, 0)); L, R, T, B = bbox_mm(cfp)
        cfp.SetPosition(V(cxp - (L + R) / 2.0, cyp - (T + B) / 2.0))
        b.Add(cfp)
        for pad in cfp.Pads():
            key = (cref, pad.GetNumber())
            if key in pad_net:
                pad.SetNet(netmap[pad_net[key]])
        placed += 1

    # --- mounting holes (real symbols H1..H4). Top two in the clear top strip; bottom two
    # inset into the left/right interior corridors (between the edge jacks and the chain) near
    # the last band -- the 24-jack ladder leaves no clean bottom strip, so the bottom holes sit
    # ~1cm inboard of the corners (still 4-corner support). ---
    mh_xy = [(18, 6), (W - 18, 6), (17.5, H - 4), (W - 17.5, H - 4)]
    for i, (hx, hy) in enumerate(mh_xy, 1):
        href = "H%d" % i
        val, fpid = comps.get(href, ("MountingHole_3.2mm_M3", "MountingHole:MountingHole_3.2mm_M3"))
        nick, fname = fpid.split(":", 1)
        h = pcbnew.FootprintLoad(fp_dir(nick), fname)
        if h is None:
            print("MISS mounting", fpid); continue
        h.SetFPID(pcbnew.LIB_ID(nick, fname))
        h.SetReference(href); h.SetValue(val)
        try:                                  # R2: match the schematic symbol's BOM/pos flags
            h.SetExcludedFromBOM(False); h.SetExcludedFromPosFiles(False)
        except Exception: pass
        h.SetPosition(V(hx, hy))
        try: h.Reference().SetVisible(True)
        except Exception: pass
        b.Add(h); placed += 1
    print("placed %d footprints, %d missing" % (placed, miss))

    # --- board outline (rectangle on Edge.Cuts) ---
    pts = [(0, 0), (W, 0), (W, H), (0, H), (0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(b); seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1)); b.Add(seg)

    # --- plane pours (proven single-channel stackup): GND In1, -VDC In2, +VDC B.Cu pour ---
    def add_plane(net_name, layer, prio=None):
        ni = netmap.get(net_name)
        if not ni:
            print("no net for plane:", net_name); return
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(ni.GetNetCode()); z.SetIsFilled(True)
        if prio is not None:
            z.SetAssignedPriority(prio)
        ch = z.Outline(); ch.NewOutline()
        for (px, py) in [(1.5, 1.5), (W - 1.5, 1.5), (W - 1.5, H - 1.5), (1.5, H - 1.5)]:
            ch.Append(mm(px), mm(py))
        b.Add(z)
        print("%s plane on layer %d" % (net_name, layer))
    add_plane("GND", pcbnew.In1_Cu)
    add_plane("-VDC", pcbnew.In2_Cu)
    add_plane("+VDC", pcbnew.B_Cu, prio=1)

    pcbnew.SaveBoard(PCB, b)
    print("saved", PCB, "(%.0f x %.0f mm)" % (W, H))
    write_netclasses()
    write_dru()

def write_dru():
    """Custom DRC rule: the CONMCX013 edge-mount jacks' shield pad straddles their Edge.Cuts
    slot cutout BY DESIGN (the shield wraps the connector barrel that passes through the slot),
    so those pads have 0/negative board-edge clearance -- inherent to edge-mount connectors.
    Scope an edge_clearance exemption to ONLY the MCX footprint; the rest of the board keeps the
    strict 0.5mm rule. Without this, restoring the 48 slots onto Edge.Cuts (required for fab so
    the connectors have slots to seat in) throws 144 copper_edge_clearance errors on the jacks'
    own pads. kicad-cli reads <project>.kicad_dru next to the board."""
    dru = os.path.join(HERE, PROJ + ".kicad_dru")
    with open(dru, "w", encoding="utf-8") as f:
        f.write('(version 1)\n\n'
                '(rule "MCX edge-mount shield pad straddles its slot by design"\n'
                '   (constraint edge_clearance (min -2mm))\n'
                '   (condition "A.Library_Link == \'cremat:MCX_CONMCX013_EdgeMount\'"))\n')
    print("wrote", os.path.basename(dru), "(MCX edge-clearance exemption)")

def write_netclasses():
    if not os.path.exists(PRO):
        return
    d = json.load(open(PRO, encoding="utf-8"))
    ns = d.setdefault("net_settings", {})
    ns["classes"] = [
        {"name": "Default", "clearance": 0.2, "track_width": 0.2032, "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "power",   "clearance": 0.2, "track_width": 0.5,    "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "hv_bias", "clearance": 0.6, "track_width": 0.4,    "via_diameter": 0.9, "via_drill": 0.4},
        {"name": "signal",  "clearance": 0.2, "track_width": 0.33,   "via_diameter": 0.8, "via_drill": 0.4},
    ]
    # per-channel-suffixed nets: patterns use wildcards so they catch *_chNN.
    ns["netclass_patterns"] = [
        {"netclass": "hv_bias", "pattern": "*BIAS*"}, {"netclass": "hv_bias", "pattern": "*SIPM*"},
        {"netclass": "hv_bias", "pattern": "*FE*"},   {"netclass": "hv_bias", "pattern": "*N_filt*"},
        {"netclass": "signal",  "pattern": "*CSP_OUT*"}, {"netclass": "signal", "pattern": "*CSP_IN*"},
        {"netclass": "signal",  "pattern": "*SH_OUT*"}, {"netclass": "signal", "pattern": "*SHAPER_OUT*"},
        {"netclass": "signal",  "pattern": "*OUT_50*"}, {"netclass": "signal", "pattern": "*BUF_*"},
        {"netclass": "power", "pattern": "GND"}, {"netclass": "power", "pattern": "+VDC"},
        {"netclass": "power", "pattern": "-VDC"},
        {"netclass": "power", "pattern": "*VS_F*"},
        {"netclass": "power", "pattern": "*SHVP*"}, {"netclass": "power", "pattern": "*SHVN*"},
        {"netclass": "power", "pattern": "*BLVP*"}, {"netclass": "power", "pattern": "*BLVN*"},
        {"netclass": "power", "pattern": "*BVP*"}, {"netclass": "power", "pattern": "*BVN*"},
    ]
    json.dump(d, open(PRO, "w", encoding="utf-8"), indent=2)
    print("re-applied net classes (.kicad_pro)")

if __name__ == "__main__":
    main()
