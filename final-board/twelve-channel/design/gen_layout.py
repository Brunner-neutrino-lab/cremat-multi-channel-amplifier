#!/usr/bin/env python3
"""Shared layout constants + helpers for the tile-and-replicate pipeline (Phase C, track C1).

The ONE channel layout lives here (LAYOUT / JACK_EDGE / band geometry) and is used by:
  * gen_tile.py       -- build the single channel TILE (ch01), then FreeRoute it.
  * replicate_tile.py -- clone the routed tile x12 + place common parts + route shared nets.
R1: the channel circuit is the imported single-channel cell (via gen_sch -> netlist); the
channel LAYOUT is defined once here and replicated, so editing it once changes all 12.
"""
import os, re, json
import importlib.util, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
SC_DESIGN = os.path.abspath(os.path.join(HERE, "..", "..", "..",
                                         "integration", "single-channel", "design"))
STOCK_FP = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
CREMAT_FP = os.path.join(HERE, "lib", "cremat.pretty")
NCH = 12

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m

sc = _load("sc_gen_sch", os.path.join(SC_DESIGN, "gen_sch.py"))           # frozen single channel (R1)
board_sch = _load("board_gen_sch", os.path.join(HERE, "gen_sch.py"))      # this board's replicator

def mm(v): return pcbnew.FromMM(float(v))
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def fp_dir(nick):
    return CREMAT_FP if nick == "cremat" else "%s/%s.pretty" % (STOCK_FP, nick)

# ============================ board + tile geometry ============================
W = 235.0                # board width (= tile width); channels stack vertically
TILE_H = 21.0            # one channel band height; 12 * 21 = 252 + top/bottom strips
ROW_PITCH = TILE_H       # vertical pitch between replicated channel tiles
BOARD_TOP = 6.0          # first tile's top y (leaves a top strip for power + mtg holes)
H = BOARD_TOP + NCH * TILE_H + 6.0    # 6 + 252 + 6 = 264 mm board height
EDGE_IN_X = 0.0
EDGE_OUT_X = W
# within a tile, the band centerline and the 2 jack slots (BIAS/SIPM left, OUT/TEST right):
TILE_BAND_CY = TILE_H / 2.0          # band centerline within the tile
JACK_DY = 5.3                        # +-offset of the two jacks (10.6mm apart > 9.91 courtyard)

SIG = 0.0
DUP = -6.3
DDN = +6.3
LAYOUT = {
    "Rf1":   (22.0, -3.0, 0), "JP_Rf1": (22.0, +1.0, 0),
    "Cf":    (27.0, +5.0, 90),
    "Rf2":   (32.0, -3.0, 0), "JP_Rf2": (32.0, +1.0, 0),
    "Cc":    (40.0, -3.0, 0),
    "R_test":(22.0, +6.0, 0), "C_test": (32.0, +6.0, 0),
    "U_CSP": (62.0, SIG, 90),
    "R_dvp": (52.0, DUP, 0), "Cp1": (57.0, DUP, 0), "Cp2": (62.0, DUP, 0),
    "R_dvn": (52.0, DDN, 0), "Cn1": (57.0, DDN, 0), "Cn2": (62.0, DDN, 0),
    "U_SH":  (92.0, SIG, 90),
    "RV_PZ": (94.0, DDN + 1.0, 0),    # trim below CR-200, pulled in so it clears the tile bottom
    "R_SHP": (82.0, DUP, 0), "C_SHPb": (87.0, DUP, 0), "C_SHPh": (97.0, DUP, 0),
    "R_SHN": (78.0, DDN, 0), "C_SHNb": (103.0, DDN, 0), "C_SHNh": (107.5, DDN, 0),
    "U_BLR": (124.0, SIG, 90),
    "R_BLP": (114.0, DUP, 0), "C_BLPb": (119.0, DUP, 0), "C_BLPh": (129.0, DUP, 0),
    "R_BLN": (116.0, DDN, 0), "C_BLNb": (121.0, DDN, 0), "C_BLNh": (129.0, DDN, 0),
    "JP_BLR":(140.0, SIG, 0),
    "U_BUF": (158.0, SIG, 0),
    "R_FB":  (150.0, DDN, 0), "R_GAIN": (156.0, DDN, 0), "R_BSER": (168.0, SIG, 0),
    "R_BVP": (146.0, DUP, 0), "C_BVPb": (151.0, DUP, 0), "C_BVPh": (156.0, DUP, 0),
    "R_BVN": (162.0, DUP, 0), "C_BVNb": (167.0, DUP, 0), "C_BVNh": (172.0, DUP, 0),
    "C_BULKP": (188.0, DUP, 0), "C_BULKN": (188.0, DDN, 0),
}
# Edge jacks: (edge_x, dy_sign, rot). Slot OUTBOARD (left rot -90, right rot +90) so signal pad 1
# escapes inward. BIAS upper / SIPM lower on the left; OUT_50 upper / TEST_IN lower on the right.
JACK_EDGE = {
    "J_BIAS":  (EDGE_IN_X,  -1, -90),
    "J_SIPM":  (EDGE_IN_X,  +1, -90),
    "J_OUT50": (EDGE_OUT_X, -1, 90),
    "J_TEST":  (EDGE_OUT_X, +1, 90),
}
MCX_ROLES = ("J_BIAS", "J_SIPM", "J_TEST", "J_OUT50")
SIP_ROLES = ("U_CSP", "U_SH", "U_BLR")
SLOT_DEPTH = 6.3
SLOT_EDGE_GAP = 0.6

SHARED_PARTS = {
    "CBULK_P": ("470uF 35V", "UVR1V471MPD", "Nichicon", "493-1084-ND"),
    "CBULK_N": ("470uF 35V", "UVR1V471MPD", "Nichicon", "493-1084-ND"),
}
DNP_ROLES = {role for role, *rest in sc.build_spec() if rest[3]}

# ============================ netlist + ref maps ============================
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

def build_ref_role_maps():
    full_spec = sc.build_spec()
    spec = [r for r in full_spec if r[0] not in board_sch.BOARD_LEVEL_ROLES]
    cnt = {}; ref_role = {}; role_refs = {}
    for n in range(1, NCH + 1):
        for role, *_ in spec:
            pfx = board_sch.prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1
            ref = "%s%d" % (pfx, cnt[pfx]); ref_role[ref] = (n, role); role_refs[(n, role)] = ref
    cnt["J"] = cnt.get("J", 0) + 1
    jpwr = "J%d" % cnt["J"]; ref_role[jpwr] = (0, "J_PWR"); role_refs[(0, "J_PWR")] = jpwr
    for role in ("CBULK_P", "CBULK_N"):
        cnt["C"] = cnt.get("C", 0) + 1
        cref = "C%d" % cnt["C"]; ref_role[cref] = (0, role); role_refs[(0, role)] = cref
    for i in range(1, 5):
        cnt["H"] = cnt.get("H", 0) + 1
        href = "H%d" % cnt["H"]; ref_role[href] = (0, "MH"); role_refs[(0, "MH")] = href
    return ref_role, role_refs, spec

# ============================ footprint helpers ============================
def bbox_mm(fp):
    try: bb = fp.GetBoundingBox(False, False)
    except TypeError: bb = fp.GetBoundingBox()
    return (bb.GetLeft() / 1e6, bb.GetRight() / 1e6, bb.GetTop() / 1e6, bb.GetBottom() / 1e6)

def set_fp_fields(fp, nick, fname, ref, val, role):
    fp.SetFPID(pcbnew.LIB_ID(nick, fname))
    fp.SetReference(ref); fp.SetValue(val)
    meta = sc.PARTS.get(role) or SHARED_PARTS.get(role)
    if meta:
        _v, mpn, mfr, dkpn = meta
        for k, v in (("MPN", mpn), ("Manufacturer", mfr), ("Distributor PN", dkpn)):
            try: fp.SetField(k, v)
            except Exception:
                try:
                    pf = pcbnew.PCB_FIELD(fp, fp.GetFieldCount(), k); pf.SetText(v); fp.Add(pf)
                except Exception: pass

def place_tile(b, fp, role, netmap, pad_net):
    """Place one footprint in the TILE (band centered at TILE_BAND_CY)."""
    if role in JACK_EDGE:
        ex, dysign, rot = JACK_EDGE[role]
        fp.SetOrientationDegrees(rot)
        jy = TILE_BAND_CY + dysign * JACK_DY
        ox = (SLOT_EDGE_GAP + SLOT_DEPTH) if ex == EDGE_IN_X else (W - SLOT_EDGE_GAP - SLOT_DEPTH)
        fp.SetPosition(V(ox, jy))
    else:
        dx, dy, rot = LAYOUT[role]
        if role in SIP_ROLES: rot = 90
        if rot: fp.SetOrientationDegrees(rot)
        fp.SetPosition(V(0, 0)); Lx, Rx, Tx, Bx = bbox_mm(fp)
        fp.SetPosition(V(dx - (Lx + Rx) / 2.0, TILE_BAND_CY + dy - (Tx + Bx) / 2.0))
    b.Add(fp)
    for pad in fp.Pads():
        key = (fp.GetReference(), pad.GetNumber())
        if key in pad_net:
            pad.SetNet(netmap[pad_net[key]])

# ============================ project settings ============================
def write_netclasses(pro_path):
    if not os.path.exists(pro_path):
        return
    d = json.load(open(pro_path, encoding="utf-8"))
    ns = d.setdefault("net_settings", {})
    ns["classes"] = [
        {"name": "Default", "clearance": 0.2, "track_width": 0.2032, "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "power",   "clearance": 0.2, "track_width": 0.5,    "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "hv_bias", "clearance": 0.6, "track_width": 0.4,    "via_diameter": 0.9, "via_drill": 0.4},
        {"name": "signal",  "clearance": 0.2, "track_width": 0.33,   "via_diameter": 0.8, "via_drill": 0.4},
    ]
    ns["netclass_patterns"] = [
        {"netclass": "hv_bias", "pattern": "*BIAS*"}, {"netclass": "hv_bias", "pattern": "*SIPM*"},
        {"netclass": "hv_bias", "pattern": "*FE*"},   {"netclass": "hv_bias", "pattern": "*N_filt*"},
        {"netclass": "signal",  "pattern": "*CSP_OUT*"}, {"netclass": "signal", "pattern": "*CSP_IN*"},
        {"netclass": "signal",  "pattern": "*SH_OUT*"}, {"netclass": "signal", "pattern": "*SHAPER_OUT*"},
        {"netclass": "signal",  "pattern": "*OUT_50*"}, {"netclass": "signal", "pattern": "*BUF_*"},
        {"netclass": "power", "pattern": "GND"}, {"netclass": "power", "pattern": "+VDC"},
        {"netclass": "power", "pattern": "-VDC"}, {"netclass": "power", "pattern": "*VS_F*"},
        {"netclass": "power", "pattern": "*SHVP*"}, {"netclass": "power", "pattern": "*SHVN*"},
        {"netclass": "power", "pattern": "*BLVP*"}, {"netclass": "power", "pattern": "*BLVN*"},
        {"netclass": "power", "pattern": "*BVP*"}, {"netclass": "power", "pattern": "*BVN*"},
    ]
    json.dump(d, open(pro_path, "w", encoding="utf-8"), indent=2)

def write_dru(dru_path):
    with open(dru_path, "w", encoding="utf-8") as f:
        f.write('(version 1)\n\n'
                '(rule "MCX edge-mount shield pad straddles its slot by design"\n'
                '   (constraint edge_clearance (min -2mm))\n'
                '   (condition "A.Library_Link == \'cremat:MCX_CONMCX013_EdgeMount\'"))\n')
