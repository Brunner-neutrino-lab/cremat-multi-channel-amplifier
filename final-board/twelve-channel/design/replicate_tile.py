#!/usr/bin/env python3
"""PHASE 2 of tile-and-replicate (Phase C, track C1): clone the routed TILE x12 + commons.

Loads the routed, DRC-clean `tile.kicad_pcb` (channel ch01: footprints + tracks + vias + local
zones) and stamps it 12x into the final board, each copy translated by one ROW_PITCH and with
its refs/nets remapped ch01 -> chNN. Shared rails (+VDC/-VDC/GND) stay global. Then places the
common parts (screw terminal, 2x bulk, 4x M3) and adds the outer board outline. Result: 12
geometrically IDENTICAL channel blocks (matched parasitics), NO per-channel autorouting -- only
the shared power circuit is routed afterward.

R1: the channel TILE is the single layout source; editing gen_layout/the tile and regenerating
restamps all 12 identically.

Run AFTER gen_tile + tile route/fill:
  "C:/Program Files/KiCad/10.0/bin/python.exe" replicate_tile.py
"""
import os, re
import pcbnew
import gen_layout as L

HERE = os.path.dirname(os.path.abspath(__file__))
TILE = os.path.join(HERE, "tile.kicad_pcb")
PCB = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pcb")
PRO = os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_pro")

def mm(v): return pcbnew.FromMM(float(v))
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

PER_CH_SUFFIX = re.compile(r"_ch01\b")

def dup(item):
    """Duplicate a BOARD_ITEM across the FOOTPRINT (Duplicate(bool)) vs track/zone (Duplicate())
    signature split in the KiCad 10 SWIG bindings, returning the Cast() concrete type."""
    try:
        d = item.Duplicate(False)          # FOOTPRINT.Duplicate(addToParentGroup)
    except TypeError:
        d = item.Duplicate()               # TRACK/VIA/ZONE.Duplicate()
    try:
        d = d.Cast()
    except Exception:
        pass
    return d

def remap_net(name, n):
    """ch01 per-channel net -> chNN; shared rails unchanged."""
    if name in ("+VDC", "-VDC", "GND", ""):
        return name
    # netlist names are like /BIAS_IN_ch01 ; bump the suffix
    return name.replace("_ch01", "_ch%02d" % n)

def main():
    ref_role, role_refs, spec = L.build_ref_role_maps()
    # tile ref -> role (channel-1 refs)
    tile_ref_role = {role_refs[(1, role)]: role for role, *_ in spec}
    # full netlist (ref,pad)->net so we can re-assign per-channel NC pins (unconnected-(...))
    _, all_nets = L.parse_netlist(os.path.join(HERE, "multi-channel-cremat-amplifier.net"))
    pad_to_net = {}
    for nm, nodes in all_nets.items():
        for ref, pad in nodes:
            pad_to_net[(ref, pad)] = nm

    tile = pcbnew.LoadBoard(TILE)
    out = pcbnew.CreateEmptyBoard()
    out.SetCopperLayerCount(4)
    try:
        out.SetLayerName(pcbnew.In1_Cu, "GND.Cu"); out.SetLayerName(pcbnew.In2_Cu, "PWR.Cu")
    except Exception as e:
        print("layer name:", e)

    # --- net table: all 12 channels' nets + shared rails (built from the tile's net names) ---
    tile_net_names = set()
    for it in list(tile.GetTracks()):
        tile_net_names.add(it.GetNetname())
    for f in tile.GetFootprints():
        for p in f.Pads():
            tile_net_names.add(p.GetNetname())
    for z in tile.Zones():
        tile_net_names.add(z.GetNetname())
    tile_net_names.discard("")

    netmap = {}
    def ensure_net(name):
        if name not in netmap:
            ni = pcbnew.NETINFO_ITEM(out, name); out.Add(ni); netmap[name] = ni
        return netmap[name]
    ensure_net("+VDC"); ensure_net("-VDC"); ensure_net("GND")
    for n in range(1, L.NCH + 1):
        for nm in tile_net_names:
            ensure_net(remap_net(nm, n))

    per_ch_stats = []
    # --- clone the tile x12 ---
    for n in range(1, L.NCH + 1):
        dy = L.BOARD_TOP + (n - 1) * L.ROW_PITCH        # translate the tile's top to this row
        offset = V(0, dy)
        nt = nv = nf = nz = 0
        # footprints
        for f in tile.GetFootprints():
            role = tile_ref_role.get(f.GetReference())
            nf_new = dup(f)
            out.Add(nf_new)
            nf_new.Move(offset)
            new_ref = role_refs[(n, role)] if role is not None else nf_new.GetReference()
            if role is not None:
                nf_new.SetReference(new_ref)
            for pad in nf_new.Pads():
                cur = pad.GetNetname()
                if cur.startswith("unconnected-") or not cur:
                    # NC pin: take the per-channel unconnected-(...) net from the netlist (keyed
                    # by the REMAPPED ref) so each channel's NC pad is its own single-node net.
                    nm = pad_to_net.get((new_ref, pad.GetNumber()), "")
                else:
                    nm = remap_net(cur, n)
                if nm:
                    pad.SetNet(ensure_net(nm))
            nf += 1
        # tracks + vias
        for t in tile.GetTracks():
            is_via = (t.GetClass() == "PCB_VIA")
            nt_new = dup(t)
            out.Add(nt_new)
            nt_new.Move(offset)
            nt_new.SetNet(ensure_net(remap_net(t.GetNetname(), n)))
            if is_via: nv += 1
            else: nt += 1
        # NOTE: the tile's 3 plane zones (GND In1 / -VDC In2 / +VDC B.Cu) are NOT cloned -- they
        # would tile into 12 same-net zones that intersect each other + the board-wide planes
        # (zones_intersect). The board-wide planes (add_board_planes) cover the whole board and
        # the per-channel rail vias tie straight into them, so the channels need no local zones.
        nz = 0
        per_ch_stats.append((nf, nt, nv, nz))
    print("replicated tile x%d: per-channel = %s" % (L.NCH, per_ch_stats[0]))
    assert all(s == per_ch_stats[0] for s in per_ch_stats), "channels NOT identical!"
    print("ALL 12 channel blocks identical:", per_ch_stats[0])

    place_commons(out, role_refs, netmap, ensure_net)
    add_outline(out)
    add_board_planes(out, netmap)

    pcbnew.SaveBoard(PCB, out)
    print("saved", PCB, "(%.0f x %.0f mm)" % (L.W, L.H))
    L.write_netclasses(PRO)
    L.write_dru(os.path.join(HERE, "multi-channel-cremat-amplifier.kicad_dru"))

def _load_fp(fpid):
    nick, fname = fpid.split(":", 1)
    return pcbnew.FootprintLoad(L.fp_dir(nick), fname), nick, fname

def place_commons(b, role_refs, netmap, ensure_net):
    comps, nets = L.parse_netlist(os.path.join(HERE, "multi-channel-cremat-amplifier.net"))
    pad_net = {}
    for name, nodes in nets.items():
        for ref, pad in nodes:
            pad_net[(ref, pad)] = name
    # screw terminal (top-center strip)
    jpwr = role_refs[(0, "J_PWR")]; val, fpid = comps[jpwr]
    fp, nick, fname = _load_fp(fpid); L.set_fp_fields(fp, nick, fname, jpwr, val, "J_PWR")
    fp.SetPosition(V(0, 0)); Lx, Rx, Tx, Bx = L.bbox_mm(fp)
    fp.SetPosition(V(L.W / 2.0 - (Lx + Rx) / 2.0, 3.0 - (Tx + Bx) / 2.0)); b.Add(fp)
    for pad in fp.Pads():
        if (jpwr, pad.GetNumber()) in pad_net:
            pad.SetNet(ensure_net(pad_net[(jpwr, pad.GetNumber())]))
    # central bulk caps in the top strip
    for role, (cx, cy) in (("CBULK_P", (196.0, 3.0)), ("CBULK_N", (208.0, 3.0))):
        cref = role_refs[(0, role)]; val, fpid = comps[cref]
        fp, nick, fname = _load_fp(fpid); L.set_fp_fields(fp, nick, fname, cref, val, role)
        fp.SetPosition(V(0, 0)); Lx, Rx, Tx, Bx = L.bbox_mm(fp)
        fp.SetPosition(V(cx - (Lx + Rx) / 2.0, cy - (Tx + Bx) / 2.0)); b.Add(fp)
        for pad in fp.Pads():
            if (cref, pad.GetNumber()) in pad_net:
                pad.SetNet(ensure_net(pad_net[(cref, pad.GetNumber())]))
    # 4x M3 mounting holes (top strip corners + bottom strip corners)
    mh_xy = [(15, 3), (L.W - 15, 3), (15, L.H - 3), (L.W - 15, L.H - 3)]
    for i, (hx, hy) in enumerate(mh_xy, 1):
        href = "H%d" % i; val, fpid = comps.get(href, ("MountingHole_3.2mm_M3", "MountingHole:MountingHole_3.2mm_M3"))
        fp, nick, fname = _load_fp(fpid)
        fp.SetFPID(pcbnew.LIB_ID(nick, fname)); fp.SetReference(href); fp.SetValue(val)
        try: fp.SetExcludedFromBOM(False); fp.SetExcludedFromPosFiles(False)
        except Exception: pass
        fp.SetPosition(V(hx, hy)); b.Add(fp)
    print("placed common parts: screw terminal, 2x bulk, 4x M3")

def add_outline(b):
    pts = [(0, 0), (L.W, 0), (L.W, L.H), (0, L.H), (0, 0)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(b); seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1)); b.Add(seg)

def add_board_planes(b, netmap):
    # board-wide planes (the per-channel tile zones tie into these via shared net codes)
    def add_plane(net_name, layer, prio=None):
        ni = netmap.get(net_name)
        if not ni: return
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(ni.GetNetCode()); z.SetIsFilled(True)
        if prio is not None: z.SetAssignedPriority(prio)
        ch = z.Outline(); ch.NewOutline()
        for (px, py) in [(1.5, 1.5), (L.W - 1.5, 1.5), (L.W - 1.5, L.H - 1.5), (1.5, L.H - 1.5)]:
            ch.Append(mm(px), mm(py))
        b.Add(z)
    add_plane("GND", pcbnew.In1_Cu)            # inner GND plane
    add_plane("-VDC", pcbnew.In2_Cu)           # inner -VDC plane
    add_plane("+VDC", pcbnew.B_Cu, prio=1)     # +VDC pour on B.Cu
    add_plane("GND", pcbnew.F_Cu, prio=0)      # F.Cu GND fill (carves around the cloned tracks)

if __name__ == "__main__":
    main()
