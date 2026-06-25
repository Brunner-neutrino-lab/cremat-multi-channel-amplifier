#!/usr/bin/env python3
"""Build the standalone shaper PCB from the gen_sch spec using the pcbnew API.

Headless scope (pcbnew has NO autorouter): create a 4-layer board, place + net every
footprint, draw the outline + M3 holes, set the net classes, and add GND (In1) + -VDC
(In2) plane pours. Signal/+VDC routing is done by FreeRouting (export_dsn -> jar ->
import_ses); zones fill in a separate pass (fill_zones).

Placement is explicit per role (no overlap): a left->right signal-flow main row at y=ROW_Y,
with each module's decoupling stacked directly above (+rail) and below (-rail) it.

Milestone follows gen_sch (env SHAPER_MS, default M2).

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py
      SHAPER_MS=M1 "C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py
Gate: kicad-cli pcb drc shaper.kicad_pcb
"""
import os, pcbnew
import gen_sch   # reuse the spec + reference assignment

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "shaper.kicad_pcb")
STOCK_FP = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
CREMAT_FP = os.path.join(HERE, "lib", "cremat.pretty")
MS = gen_sch.MS

def mm(v): return pcbnew.FromMM(float(v))
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def fp_dir(nick):
    return CREMAT_FP if nick == "cremat" else "%s/%s.pretty" % (STOCK_FP, nick)

SIP_ROLES  = ("U_SH", "U_BLR")            # 21mm SIP-8 laid flat
EDGE_ROLES = ("J_IN", "J_OUT")            # MCX jacks: park Edge.Cuts cutout off the outline

# explicit board coordinates (mm) per role -> (x_center, y_center, rotation)
# signal row at y=35; +rail decoupling at y=14; -rail decoupling at y=56; power bottom-left.
PLACE = {
    "J_IN":   (14,  35,  0),
    "U_SH":   (45,  35, 90),
    "RV_PZ":  (45,  68,  0),
    "U_BLR":  (95,  35, 90),
    "R_OUT":  (135, 35,  0),
    "J_OUT":  (152, 35,  0),
    "JP_BLR": (95,  68,  0),
    # CR-200 decoupling
    "R_SHP":  (33,  14,  0), "C_SHPb": (40, 14, 0), "C_SHPh": (47, 14, 0),
    "R_SHN":  (33,  56,  0), "C_SHNb": (40, 56, 0), "C_SHNh": (47, 56, 0),
    # CR-210 decoupling
    "R_BLP":  (83,  14,  0), "C_BLPb": (90, 14, 0), "C_BLPh": (97, 14, 0),
    "R_BLN":  (83,  56,  0), "C_BLNb": (90, 56, 0), "C_BLNh": (97, 56, 0),
    # board bulk electrolytics (100uF/rail) + power entry, bottom-left away from signal row
    "C_BULKP":(125, 68,  0), "C_BULKN": (140, 68, 0),
    "J_PWR":  (30,  70,  0),
}
W, H = 168.0, 80.0   # board outline

def main():
    spec = gen_sch.build_spec(MS)
    refmap = {}; cnt = {}
    for role, *_ in spec:
        pfx = gen_sch.prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1
        refmap[role] = "%s%d" % (pfx, cnt[pfx])

    pad_net = {}; netnames = {"GND", "+VDC", "-VDC"}
    for role, lib_id, value, fp, dnp, pos, netmap in spec:
        for pad, net in netmap.items():
            pad_net[(refmap[role], pad)] = net; netnames.add(net)

    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(4)

    netio = {}
    for name in sorted(netnames):
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); netio[name] = ni

    def bbox_mm(fp):
        try: bb = fp.GetBoundingBox(False, False)
        except TypeError: bb = fp.GetBoundingBox()
        return (bb.GetLeft()/1e6, bb.GetRight()/1e6, bb.GetTop()/1e6, bb.GetBottom()/1e6)

    placed = miss = 0
    for role, lib_id, value, fp, dnp, pos, netmap in spec:
        nick, fname = fp.split(":", 1)
        f = pcbnew.FootprintLoad(fp_dir(nick), fname)
        if f is None: miss += 1; print("MISS", fp, role); continue
        f.SetReference(refmap[role]); f.SetValue(value)
        if dnp:
            try: f.SetDNP(True)
            except Exception: pass
        cx, cy, rot = PLACE[role]
        if rot: f.SetOrientationDegrees(rot)
        # center the footprint bbox on (cx, cy)
        f.SetPosition(V(0, 0)); L, R, T, Bt = bbox_mm(f)
        f.SetPosition(V(cx - (L + R)/2.0, cy - (T + Bt)/2.0))
        if role in EDGE_ROLES:
            for it in f.GraphicalItems():
                if it.GetLayer() == pcbnew.Edge_Cuts:
                    it.SetLayer(pcbnew.Dwgs_User)
        b.Add(f)
        for pad in f.Pads():
            key = (refmap[role], pad.GetNumber())
            if key in pad_net: pad.SetNet(netio[pad_net[key]])
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
        for i, (hx, hy) in enumerate([(5, 5), (W-5, 5), (5, H-5), (W-5, H-5)], 1):
            h = pcbnew.FootprintLoad("%s/MountingHole.pretty" % STOCK_FP, "MountingHole_3.2mm_M3")
            if h: h.SetReference("H%d" % i); h.SetPosition(V(hx, hy)); b.Add(h)
    except Exception as e:
        print("mounting holes:", e)

    # plane pours: GND on In1.Cu, -VDC on In2.Cu (outer layers free for routing)
    def add_plane(net_name, layer):
        ni = netio.get(net_name)
        if not ni: return
        zc = pcbnew.ZONE(b); zc.SetLayer(layer); zc.SetNetCode(ni.GetNetCode())
        zc.SetIsFilled(True)
        ch = zc.Outline(); ch.NewOutline()
        for (px, py) in [(2, 2), (W-2, 2), (W-2, H-2), (2, H-2)]:
            ch.Append(mm(px), mm(py))
        b.Add(zc); print("%s plane on layer %d" % (net_name, layer))
    try:
        add_plane("GND", pcbnew.In1_Cu)
        add_plane("-VDC", pcbnew.In2_Cu)
    except Exception as e:
        print("zone:", e)

    pcbnew.SaveBoard(PCB, b)
    print("saved", PCB)
    write_netclasses()

def write_netclasses():
    import json
    pro = os.path.join(HERE, "shaper.kicad_pro")
    if not os.path.exists(pro): return
    d = json.load(open(pro, encoding="utf-8"))
    ns = d.setdefault("net_settings", {})
    ns["classes"] = [
        {"name": "Default", "clearance": 0.2, "track_width": 0.2032, "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "power",   "clearance": 0.2, "track_width": 0.5,    "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "signal",  "clearance": 0.2, "track_width": 0.33,   "via_diameter": 0.8, "via_drill": 0.4},
    ]
    ns["netclass_patterns"] = [
        {"netclass": "signal", "pattern": "*OUT*"},
        {"netclass": "signal", "pattern": "SH_IN"},
        {"netclass": "power", "pattern": "GND"},
        {"netclass": "power", "pattern": "+VDC"},
        {"netclass": "power", "pattern": "-VDC"},
    ]
    json.dump(d, open(pro, "w", encoding="utf-8"), indent=2)
    print("re-applied net classes (.kicad_pro)")

if __name__ == "__main__":
    main()
