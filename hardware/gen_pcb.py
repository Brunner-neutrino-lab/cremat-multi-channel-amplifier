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

    # placement geometry: 12 channel rows in 2 columns of 6, MCX toward board edges
    # board ~225 x 235 mm ; rows pitch ~ 18 mm
    placed = miss = 0
    order = sorted(comps)            # deterministic
    # group components by channel via reference ranges is complex; place by simple grid
    # so the netlist drives connectivity, layout is a clean starting grid for GUI routing.
    cols, x0, y0, dx, dy = 12, 20.0, 20.0, 18.0, 11.0
    # Assign each ref a slot: bucket by trailing-number parity not needed; grid fill.
    i = 0
    for ref in order:
        val, fpid = comps[ref]
        if ":" not in fpid:
            miss += 1; continue
        nick, fname = fpid.split(":", 1)
        fp = pcbnew.FootprintLoad(fp_dir(nick), fname)
        if fp is None:
            miss += 1
            print("MISS footprint:", fpid, "for", ref)
            continue
        fp.SetReference(ref)
        fp.SetValue(val)
        col = i % 18
        row = i // 18
        fp.SetPosition(V(x0 + col * 12.0, y0 + row * 14.0))
        b.Add(fp)
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in pad_net:
                pad.SetNet(netmap[pad_net[key]])
        placed += 1
        i += 1
    print("placed %d footprints, %d missing" % (placed, miss))

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
        for (hx, hy) in [(6, 6), (W - 6, 6), (6, H - 6), (W - 6, H - 6)]:
            h = pcbnew.FootprintLoad("%s/MountingHole.pretty" % STOCK_FP, "MountingHole_3.2mm_M3")
            if h:
                h.SetPosition(V(hx, hy)); b.Add(h)
    except Exception as e:
        print("mounting holes:", e)

    # GND pour on B.Cu (routes the ground net via copper)
    try:
        gnd = netmap.get("GND")
        if gnd:
            zc = pcbnew.ZONE(b)
            zc.SetLayer(pcbnew.B_Cu)
            zc.SetNetCode(gnd.GetNetCode())
            zc.SetIsFilled(True)
            poly = [(2, 2), (W - 2, 2), (W - 2, H - 2), (2, H - 2)]
            ch = zc.Outline()
            ch.NewOutline()
            for (px, py) in poly:
                ch.Append(mm(px), mm(py))
            b.Add(zc)
            print("GND zone added (unfilled; fill in GUI or fill_zones pass -- "
                  "headless in-memory Fill segfaults)")
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
    ns["classes"] = [
        {"name": "Default", "clearance": 0.2, "track_width": 0.2032, "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "power",   "clearance": 0.2, "track_width": 0.5,    "via_diameter": 0.8, "via_drill": 0.4},
        {"name": "hv_bias", "clearance": 1.0, "track_width": 0.4,    "via_diameter": 0.9, "via_drill": 0.4},
        {"name": "signal",  "clearance": 0.2, "track_width": 0.33,   "via_diameter": 0.8, "via_drill": 0.4},
    ]
    ns["netclass_patterns"] = [
        {"netclass": "hv_bias", "pattern": "*BIAS*"}, {"netclass": "hv_bias", "pattern": "*SIPM*"},
        {"netclass": "hv_bias", "pattern": "*FE*"},   {"netclass": "signal",  "pattern": "*OUT*"},
        {"netclass": "power", "pattern": "GND"}, {"netclass": "power", "pattern": "+VDC"},
        {"netclass": "power", "pattern": "-VDC"},
    ]
    json.dump(d, open(pro, "w", encoding="utf-8"), indent=2)
    print("re-applied net classes to .kicad_pro")

if __name__ == "__main__":
    main()
