#!/usr/bin/env python3
"""PHASE 1 of the tile-and-replicate layout (Phase C, track C1): build the ONE channel TILE.

User-directed strategy (replaces all-12 autorouting): route ONE channel as a compact stackable
tile, then replicate it x12 (replicate_tile.py) and route only the shared circuits. Result: all
12 channels get BYTE-IDENTICAL layout (matched parasitics) with far less routing.

This script builds `tile.kicad_pcb`: channel ch01's 45 footprints placed in the compact band
layout (shared from gen_layout.LAYOUT/JACK_EDGE), 4 MCX cutouts on Edge.Cuts at the tile L/R
edges, tile-local 4-layer plane zones (GND In1 / -VDC In2 / +VDC B.Cu) so each channel's rails
via straight to the planes inside the tile, and the L/R outline edges ONLY (no top/bottom edge
-- those become internal when tiles stack; the outer perimeter is added in the final board).

Tile = full board WIDTH (235mm) x one band (~TILE_H mm). The signal flows L->R; BIAS/SIPM jacks
on the left edge, OUT_50/TEST_IN on the right edge, slots OUTBOARD so pad 1 escapes inward.

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_tile.py
Then: export tile.dsn -> FreeRouting -> tile.ses -> import -> tile is the routed source.
"""
import os, re, json
import pcbnew
import gen_layout as L          # shared geometry + netlist parse + field helpers (R1 single source)

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(HERE, "multi-channel-cremat-amplifier.net")
TILE = os.path.join(HERE, "tile.kicad_pcb")
TILE_PRO = os.path.join(HERE, "tile.kicad_pro")

def mm(v): return pcbnew.FromMM(float(v))
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

def main():
    comps, nets = L.parse_netlist(NET)
    ref_role, role_refs, spec = L.build_ref_role_maps()

    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(4)
    try:
        b.SetLayerName(pcbnew.In1_Cu, "GND.Cu"); b.SetLayerName(pcbnew.In2_Cu, "PWR.Cu")
    except Exception as e:
        print("layer name:", e)

    # only the nets present in channel 1 (per-channel _ch01 nets + shared rails) -> tile netlist
    netmap = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); netmap[name] = ni
    pad_net = {}
    for name, nodes in nets.items():
        for ref, pad in nodes:
            pad_net[(ref, pad)] = name

    # place channel 1 only, but at a tile-local band centered in TILE_H
    n = 1
    dnp_refs = {role_refs[(n, r)] for r in L.DNP_ROLES if (n, r) in role_refs}
    placed = 0
    for role, *_ in spec:
        ref = role_refs[(n, role)]
        val, fpid = comps.get(ref, ("", ""))
        if ":" not in fpid:
            continue
        nick, fname = fpid.split(":", 1)
        fp = pcbnew.FootprintLoad(L.fp_dir(nick), fname)
        if fp is None:
            print("MISS", fpid, ref); continue
        L.set_fp_fields(fp, nick, fname, ref, val, role)
        if ref in dnp_refs:
            try: fp.SetDNP(True)
            except Exception: pass
        L.place_tile(b, fp, role, netmap, pad_net)
        placed += 1
    print("tile: placed %d footprints (channel 1)" % placed)

    # Tile outline = full closed rectangle on Edge.Cuts for STANDALONE routing/DRC of the tile.
    # (When replicated, the replicator drops the top/bottom edges so adjacent tiles merge; only
    # the L/R edges + the 4 MCX slots carry into the final board's profile.) The 4 MCX slots are
    # already on Edge.Cuts via their footprints.
    for (ax, ay), (bx, by) in [((0, 0), (L.W, 0)), ((L.W, 0), (L.W, L.TILE_H)),
                               ((L.W, L.TILE_H), (0, L.TILE_H)), ((0, L.TILE_H), (0, 0))]:
        seg = pcbnew.PCB_SHAPE(b); seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(mm(0.1)); b.Add(seg)

    # tile-local plane zones (full tile rect minus a small inset)
    def add_plane(net_name, layer, prio=None):
        ni = netmap.get(net_name)
        if not ni:
            return
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(ni.GetNetCode()); z.SetIsFilled(True)
        if prio is not None: z.SetAssignedPriority(prio)
        ch = z.Outline(); ch.NewOutline()
        for (px, py) in [(0.3, 0.3), (L.W - 0.3, 0.3), (L.W - 0.3, L.TILE_H - 0.3), (0.3, L.TILE_H - 0.3)]:
            ch.Append(mm(px), mm(py))
        b.Add(z)
    add_plane("GND", pcbnew.In1_Cu)
    add_plane("-VDC", pcbnew.In2_Cu)
    add_plane("+VDC", pcbnew.B_Cu, prio=1)

    pcbnew.SaveBoard(TILE, b)
    print("saved", TILE, "(%.0f x %.1f mm tile)" % (L.W, L.TILE_H))
    L.write_netclasses(TILE_PRO)
    L.write_dru(os.path.join(HERE, "tile.kicad_dru"))

if __name__ == "__main__":
    main()
