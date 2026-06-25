#!/usr/bin/env python3
"""Build the PCB from the schematic netlist using the pcbnew Python API.

Headless scope (pcbnew has NO autorouter): create the board, load + place every
footprint, assign nets from the netlist, draw the board outline + M3 holes, set the
net classes, and POUR the GND zone (routes the ground net via copper). Signal/power
trace routing is the GUI interactive router or FreeRouting (DSN/SES) -- not scriptable.

Run with KiCad's bundled python:
  "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/gen_pcb.py
Gate: kicad-cli pcb drc hardware/multi-channel-cremat-amplifier.kicad_pcb
"""
import os, re, sys
import pcbnew
import gen_sch   # reuse the channel spec + reference-assignment logic

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(HERE, "..", "sim", "netlists", "board.net")
PCB = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pcb")
STOCK_FP = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
CREMAT_FP = os.path.join(HERE, "lib", "cremat.pretty")

def mm(v): return pcbnew.FromMM(float(v))
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

def fp_dir(nick):
    return CREMAT_FP if nick == "cremat" else "%s/%s.pretty" % (STOCK_FP, nick)

# ---- parse netlist: components (ref -> footprint lib_id) and nets (name -> [(ref,pad)]) ----
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
    for nb in re.split(r'\n\t\t\(net\b', sec)[1:]:
        nm = re.search(r'\(name "([^"]+)"', nb)
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', nb)
        if nm:
            nets[nm.group(1)] = nodes
    return comps, nets

def main():
    comps, nets = parse_netlist(NET)
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(4)   # F.Cu / In1.Cu(GND plane) / In2.Cu / B.Cu -> routing room

    # nets
    netmap = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(b, name)
        b.Add(ni)
        netmap[name] = ni
    pad_net = {}                      # (ref, pad) -> netname
    for name, nodes in nets.items():
        for ref, pad in nodes:
            pad_net[(ref, pad)] = name

    # --- per-channel ROW placement (bounding-box packed -> guaranteed no overlap) ---
    # (n, role) -> reference, replaying gen_sch's ref assignment, then pack each channel
    # left->right by real footprint extents (signal flows along the strip).
    cnt = {}; cr2ref = {}
    for n in range(12):
        for role, *_ in gen_sch.CH:
            pfx = gen_sch.prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1
            cr2ref[(n, role)] = "%s%d" % (pfx, cnt[pfx])
    MCX_ROLES = ("J_BIAS", "J_SIPM", "J_OUT")
    PITCH, TOP, LEFT, GAP = 16.0, 20.0, 8.0, 1.6   # PITCH > tallest courtyard (MCX ~11.4)

    def bbox_mm(fp):
        try: bb = fp.GetBoundingBox(False, False)   # exclude text
        except TypeError: bb = fp.GetBoundingBox()
        return (bb.GetLeft() / 1e6, bb.GetRight() / 1e6, bb.GetTop() / 1e6, bb.GetBottom() / 1e6)

    SIP_ROLES = ("U_CSP", "U_SHAPER", "U_BLR")   # 21mm-tall SIP-8 -> rotate flat into the row

    def place(fp, role, x, row_y):
        """Place fp so its bbox left edge sits at x (vertically centered on row_y); return new x."""
        if role in SIP_ROLES:
            fp.SetOrientationDegrees(90)          # lay the SIP module horizontal (21mm wide)
        fp.SetPosition(V(0, 0))
        L, R, T, B = bbox_mm(fp)
        fp.SetPosition(V(x - L, row_y - (T + B) / 2.0))
        if role in MCX_ROLES:                # move the MCX Edge.Cuts cutout to Dwgs.User so
            for it in fp.GraphicalItems():   # the outline stays one clean rectangle (re-cut
                if it.GetLayer() == pcbnew.Edge_Cuts:   # edges in GUI when placing jacks).
                    it.SetLayer(pcbnew.Dwgs_User)
        return x + (R - L) + GAP

    def add_with_nets(fp, ref):
        b.Add(fp)
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in pad_net:
                pad.SetNet(netmap[pad_net[key]])

    placed = miss = 0; maxx = 0.0
    for n in range(12):
        row_y, x = TOP + n * PITCH, LEFT
        for role, *_ in gen_sch.CH:
            ref = cr2ref[(n, role)]; val, fpid = comps.get(ref, ("", ""))
            if ":" not in fpid: miss += 1; continue
            nick, fname = fpid.split(":", 1)
            fp = pcbnew.FootprintLoad(fp_dir(nick), fname)
            if fp is None: miss += 1; print("MISS", fpid, ref); continue
            fp.SetReference(ref); fp.SetValue(val)
            x = place(fp, role, x, row_y)
            add_with_nets(fp, ref)
            placed += 1
        maxx = max(maxx, x)
    # parts not in any channel (J_PWR) -> a clear row below the array
    done = set(cr2ref.values()); px = LEFT
    for ref in sorted(comps):
        if ref in done: continue
        val, fpid = comps[ref]
        if ":" not in fpid: miss += 1; continue
        nick, fname = fpid.split(":", 1)
        fp = pcbnew.FootprintLoad(fp_dir(nick), fname)
        if fp is None: miss += 1; continue
        fp.SetReference(ref); fp.SetValue(val)
        px = place(fp, None, px, TOP + 12 * PITCH + 8)
        add_with_nets(fp, ref)
        placed += 1
    print("placed %d footprints, %d missing; channel-strip width ~%.0f mm" % (placed, miss, maxx))

    # board outline 225 x 235 mm (rectangle on Edge.Cuts)
    W, H = 225.0, 235.0
    pts = [(0, 0), (W, 0), (W, H), (0, H), (0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(b)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1))
        b.Add(seg)

    # 4x M3 mounting holes
    try:
        for i, (hx, hy) in enumerate([(6, 6), (W - 6, 6), (6, H - 6), (W - 6, H - 6)], 1):
            h = pcbnew.FootprintLoad("%s/MountingHole.pretty" % STOCK_FP, "MountingHole_3.2mm_M3")
            if h:
                h.SetReference("H%d" % i); h.SetPosition(V(hx, hy)); b.Add(h)
    except Exception as e:
        print("mounting holes:", e)

    # Plane pours: GND on In1.Cu, -VDC on In2.Cu (both are large nets -> give them planes
    # so the autorouter only has to route signals + the +VDC tree on F.Cu/B.Cu).
    def add_plane(net_name, layer):
        ni = netmap.get(net_name)
        if not ni:
            return
        zc = pcbnew.ZONE(b)
        zc.SetLayer(layer)
        zc.SetNetCode(ni.GetNetCode())
        zc.SetIsFilled(True)
        ch = zc.Outline(); ch.NewOutline()
        for (px, py) in [(2, 2), (W - 2, 2), (W - 2, H - 2), (2, H - 2)]:
            ch.Append(mm(px), mm(py))
        b.Add(zc)
        print("%s plane added on layer %d (fill via fill_zones.py)" % (net_name, layer))
    try:
        add_plane("GND", pcbnew.In1_Cu)
        add_plane("-VDC", pcbnew.In2_Cu)
    except Exception as e:
        print("zone:", e)

    pcbnew.SaveBoard(PCB, b)
    print("saved", PCB)
    write_netclasses()

def write_netclasses():
    """Re-apply the project net classes (pcbnew's save resets net_settings to Default)."""
    import json
    pro = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pro")
    if not os.path.exists(pro):
        return
    d = json.load(open(pro, encoding="utf-8"))
    ns = d.setdefault("net_settings", {})
    # hv_bias clearance 0.6mm: IPC-2221 external-uncoated creepage for <=60V, and >=0805
    # pad-gap (~0.9mm) so the bias-filter / AC-coupling 0805s don't self-violate. (The
    # coupling cap Cc bridges HV->amp across its own 0.9mm; its 100V rating provides that
    # isolation, not PCB creepage.) Add conformal coating for extra margin.
    ns["classes"] = [
        {"name": "Default", "clearance": 0.2, "track_width": 0.2032, "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "power",   "clearance": 0.2, "track_width": 0.5,    "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "hv_bias", "clearance": 0.6, "track_width": 0.4,    "via_diameter": 0.9, "via_drill": 0.4},
        {"name": "signal",  "clearance": 0.2, "track_width": 0.33,   "via_diameter": 0.8, "via_drill": 0.4},
    ]
    ns["netclass_patterns"] = [
        {"netclass": "hv_bias", "pattern": "*BIAS*"}, {"netclass": "hv_bias", "pattern": "*SIPM*"},
        {"netclass": "hv_bias", "pattern": "*FE*"},   {"netclass": "signal",  "pattern": "*OUT*"},
        {"netclass": "power", "pattern": "GND"}, {"netclass": "power", "pattern": "+VDC"},
        {"netclass": "power", "pattern": "-VDC"},
    ]
    json.dump(d, open(pro, "w", encoding="utf-8"), indent=2)
    dru = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_dru")
    if os.path.exists(dru):
        os.remove(dru)   # the 1.0mm custom rule is superseded by the 0.6mm netclass
    print("re-applied net classes (.kicad_pro)")

if __name__ == "__main__":
    main()
