#!/usr/bin/env python3
"""Build the CR-112 CSP eval board PCB from the schematic netlist (track A1).

4-layer board: F.Cu / In1.Cu(GND plane) / In2.Cu(-VDC plane) / B.Cu. Places every
footprint with an explicit, DRC-clean layout (signal flows left->right; MCX jacks on
the board edges; CR-112 SIP-8 laid flat; decoupling clustered at the module), assigns
nets, draws the board outline + M3 holes, sets net classes, and adds the GND/-VDC
plane zones (filled in a separate fill_zones.py pass).

Routing is FreeRouting (DSN/SES) per docs/FREEROUTING.md.

Run: "C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py
Gate: kicad-cli pcb drc csp-cr112.kicad_pcb
"""
import os, re, json
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(HERE, "csp-cr112.net")
PCB = os.path.join(HERE, "csp-cr112.kicad_pcb")
PRO = os.path.join(HERE, "csp-cr112.kicad_pro")
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
        comps[ref] = (val.group(1) if val else "", fp.group(1) if fp else "")
    nets = {}
    sec = t[t.index("(nets"):]
    for nb in re.split(r'\n\s*\(net\b', sec)[1:]:
        nm = re.search(r'\(name "([^"]+)"', nb)
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', nb)
        if nm:
            nets[nm.group(1)] = nodes
    return comps, nets

# Board geometry
W, H = 90.0, 72.0          # mm; comfortable single-channel board

# Explicit placement: ref -> (x_mm, y_mm, rotation_deg). Hand-laid for a clean DRC.
# Signal flows left (bias/test inputs) -> right (CSP_OUT). MCX jacks hug board edges.
# Courtyards (mm): MCX 9.9x11.5, screw-term 16.1x10.9, SIP-8 3.6x21.4, 1206 4.7x2.4.
PLACE = {
    # left edge: bias + test inputs (MCX)
    "J1": (10.0, 16.0, 0),     # BIAS_IN  (left edge, upper)
    "J3": (10.0, 40.0, 0),     # TEST_IN  (left edge, lower)
    # bias filter chain  BIAS_IN -> Rf1/0R -> Cf -> Rf2/0R -> FE
    "R1": (26.0, 14.0, 0),     # Rf1 10k
    "R2": (26.0, 18.0, 0),     # JP_Rf1 0R (DNP, parallel)
    "C1": (33.0, 22.0, 90),    # Cf 100nF/100V -> GND
    "R3": (40.0, 14.0, 0),     # Rf2 10k
    "R4": (40.0, 18.0, 0),     # JP_Rf2 0R (DNP, parallel)
    # SIPM jack (DC-coupled to FE) on the top edge
    "J2": (48.0, 8.5, 180),    # SIPM MCX (top edge)
    # AC-coupling + test injection into CSP_IN
    "C2": (48.0, 20.0, 0),     # Cc 0.22uF/100V (FE -> CSP_IN)
    "R5": (28.0, 40.0, 0),     # R_test 47
    "C3": (42.0, 40.0, 0),     # C_test 1pF (TEST_N -> CSP_IN)
    # CR-112 module (SIP-8) + output
    "U1": (62.0, 24.0, 0),     # CR-112 (pins span y ~13..35)
    "J4": (80.0, 16.0, 0),     # CSP_OUT MCX (right edge)
    # per-rail decoupling clustered at the module (CR-150-R5)
    "R6": (52.0, 48.0, 0),     # 4.7 series +VDC->+VS_F
    "C4": (60.0, 48.0, 0),     # 10uF +VS_F
    "C5": (66.0, 48.0, 0),     # 0.1uF +VS_F
    "R7": (52.0, 56.0, 0),     # 4.7 series -VDC->-VS_F
    "C6": (60.0, 56.0, 0),     # 10uF -VS_F
    "C7": (66.0, 56.0, 0),     # 0.1uF -VS_F
    # power entry: screw terminal bottom-left (body centered ~12,63 -> spans x4..20,y57.5..68.5)
    "J5": (13.0, 63.0, 0),     # +Vs/GND/-Vs
    # board rail-entry bulk: 100uF radial electrolytics (D6.3mm, ~6.8mm courtyard, THT pads
    # at x=0 & x=2.5). Spaced clear of J5 (right edge ~20) and each other, below the
    # decoupling cluster. Pad1 (+) origin; courtyard circle centered at (x+1.25, y).
    "C8": (33.0, 61.0, 0),     # 100uF +VDC entry bulk
    "C9": (44.0, 61.0, 0),     # 100uF -VDC entry bulk
}
MCX_REFS = ("J1", "J2", "J3", "J4")

def main():
    comps, nets = parse_netlist(NET)
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(4)
    # name inner layers for clarity
    try:
        b.SetLayerName(pcbnew.In1_Cu, "GND.Cu")
        b.SetLayerName(pcbnew.In2_Cu, "PWR.Cu")
    except Exception as e:
        print("layer name:", e)

    netmap = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(b, name)
        b.Add(ni)
        netmap[name] = ni
    pad_net = {}
    for name, nodes in nets.items():
        for ref, pad in nodes:
            pad_net[(ref, pad)] = name

    placed = miss = 0
    for ref in sorted(comps):
        val, fpid = comps[ref]
        if ":" not in fpid:
            miss += 1; print("no footprint id:", ref); continue
        nick, fname = fpid.split(":", 1)
        fp = pcbnew.FootprintLoad(fp_dir(nick), fname)
        if fp is None:
            miss += 1; print("MISS", fpid, ref); continue
        fp.SetReference(ref); fp.SetValue(val)
        x, y, rot = PLACE.get(ref, (5.0 + placed * 3.0, 68.0, 0))
        fp.SetPosition(V(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        if ref in MCX_REFS:
            # keep the board outline a single clean rectangle for routing: move each MCX
            # Edge.Cuts cutout to Dwgs.User (restore in GUI when jacks go at the edge).
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

    # board outline (rectangle on Edge.Cuts)
    pts = [(0, 0), (W, 0), (W, H), (0, H), (0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(b)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1))
        b.Add(seg)

    # 4x M3 mounting holes (inset enough that their silk reference clears the board edge)
    try:
        for i, (hx, hy) in enumerate([(5.5, 5.5), (W - 5.5, 5.5), (5.5, H - 5.5), (W - 5.5, H - 5.5)], 1):
            h = pcbnew.FootprintLoad("%s/MountingHole.pretty" % STOCK_FP, "MountingHole_3.2mm_M3")
            if h:
                h.SetReference("H%d" % i); h.SetPosition(V(hx, hy))
                h.Reference().SetVisible(False)   # silk ref not needed on a mounting hole
                b.Add(h)
    except Exception as e:
        print("mounting holes:", e)

    # plane pours: GND on In1.Cu, -VDC on In2.Cu (both large nets -> planes; outer layers free)
    def add_plane(net_name, layer):
        ni = netmap.get(net_name)
        if not ni:
            print("no net for plane:", net_name); return
        z = pcbnew.ZONE(b)
        z.SetLayer(layer); z.SetNetCode(ni.GetNetCode()); z.SetIsFilled(True)
        ch = z.Outline(); ch.NewOutline()
        for (px, py) in [(1.5, 1.5), (W - 1.5, 1.5), (W - 1.5, H - 1.5), (1.5, H - 1.5)]:
            ch.Append(mm(px), mm(py))
        b.Add(z)
        print("%s plane on layer %d (fill via fill_zones.py)" % (net_name, layer))
    try:
        add_plane("GND", pcbnew.In1_Cu)
        add_plane("-VDC", pcbnew.In2_Cu)
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
    # hv_bias clearance 0.6mm (IPC-2221 external creepage for <=60V + >=0805 pad gap);
    # the AC-coupling cap Cc bridges HV->amp across its own body (its 100V rating provides
    # isolation, not PCB creepage). signal 0.33mm; power 0.5mm.
    ns["classes"] = [
        {"name": "Default", "clearance": 0.2, "track_width": 0.2032, "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "power",   "clearance": 0.2, "track_width": 0.5,    "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "hv_bias", "clearance": 0.6, "track_width": 0.4,    "via_diameter": 0.9, "via_drill": 0.4},
        {"name": "signal",  "clearance": 0.2, "track_width": 0.33,   "via_diameter": 0.8, "via_drill": 0.4},
    ]
    ns["netclass_patterns"] = [
        {"netclass": "hv_bias", "pattern": "*BIAS*"}, {"netclass": "hv_bias", "pattern": "*SIPM*"},
        {"netclass": "hv_bias", "pattern": "*FE*"},
        {"netclass": "signal",  "pattern": "*CSP_OUT*"}, {"netclass": "signal", "pattern": "*CSP_IN*"},
        {"netclass": "power", "pattern": "GND"}, {"netclass": "power", "pattern": "+VDC"},
        {"netclass": "power", "pattern": "-VDC"},
        {"netclass": "power", "pattern": "*VS_F*"},
    ]
    json.dump(d, open(PRO, "w", encoding="utf-8"), indent=2)
    print("re-applied net classes (.kicad_pro)")

if __name__ == "__main__":
    main()
