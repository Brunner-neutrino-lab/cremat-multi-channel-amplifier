#!/usr/bin/env python3
"""Build the 12-channel PCB by TILE-AND-REPLICATE (the user's brief: duplicate the routed
single-channel layout x12 so the autorouter barely works; only the shared power is new).

  * TILE  = the routed single-channel channel row (integration/single-channel/design/
    channel.kicad_pcb) MINUS its COM row. Its 38 footprints + all channel-region tracks/vias
    are cloned x12, translated by PITCH in Y, refs re-mapped via ROLE (ch1->chNN), nets
    re-mapped /X -> /chNN/X (rails +VDC/-VDC/GND stay global).
  * COMMON = one power section at the top: J_PWR (in) + J_DAISY (board-to-board daisy out) on
    the raw rails, UP-RATED reverse-polarity block (PTC 1.1A / SS24) + 470uF bulk. Only these
    ~4 short pre-plane nets are hand-routed; every channel rail via drops into board-wide plane
    pours (In1 GND / In2 -VDC / B.Cu +VDC / F.Cu GND) exactly as in the single channel.

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py
Then: fill_zones.py ; kicad-cli pcb drc --schematic-parity twelve-channel.kicad_pcb
"""
import os, re, importlib.util
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
SC_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "integration", "single-channel", "design"))
SC_PCB = os.path.join(SC_DIR, "channel.kicad_pcb")
TW_NET = os.path.join(HERE, "twelve-channel.net")
PCB = os.path.join(HERE, "twelve-channel.kicad_pcb")
DRU = os.path.join(HERE, "twelve-channel.kicad_dru")

# ---- import the 12-ch schematic generator for the role/ref/net maps --------------------
_spec = importlib.util.spec_from_file_location("tw_gen_sch", os.path.join(HERE, "gen_sch.py"))
g12 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(g12)
sc = g12.sc
NCH = g12.NCH
CH_ROLES = set(g12.CH_ROLES)
CH_BASE_REF = g12.CH_BASE_REF
SC_REFMAP, _ = g12.build_refmap(sc.ROLES)          # role -> single-channel ref
SC_ROLE = {v: k for k, v in SC_REFMAP.items()}     # single-channel ref -> role
DNP_ROLES = {r for r in CH_ROLES if sc.SPEC[r][2]}
MCX_ROLES = {"J_BIAS", "J_SIPM", "J_TEST", "J_OUT50"}
RIGHT_MCX = {"J_OUT50", "J_BIAS"}          # output-side jacks -> shift out to the widened right edge
def chref(role, n): return g12.stride_ref(CH_BASE_REF[role], n)

PITCH = 25.0            # per-channel vertical pitch (single-channel row ~24.6 mm tall)
YSPLIT = 20.0           # tracks with min-y >= this belong to the channel (COM row is above it)
# Board width: SLOT-THROUGH scheme (2026-07-11, user decision). Each front/rear panel of the
# Hammond RM1U1908 gets a milled slot (~340 x 7 mm) and the BOARD PASSES THROUGH, protruding
# 5.0 mm past each panel OUTER face -> the MCX faces sit ~8.6 mm proud (face is ~3.6 mm past
# the board edge), snap-on fully in the open, and the slot absorbs all hole-alignment tolerance.
#   W = external case depth 203.20 + 2 x 5.0 protrusion = 213.2 mm
# (internal depth 196.85 / panels 3.2 - factory drawing, verified 2026-07-11)
W = 213.2               # 12-ch board width (was 180 = flush-inside; 138 = single-channel cell)
W_CELL = 138.0          # single-channel tile width (unchanged); board grows on the OUTPUT (right) side
DW = W - W_CELL         # right-edge extension: output MCX move out, their signal traces extend

def mm(v): return pcbnew.FromMM(float(v))
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

def parse_netlist(path):
    t = open(path, encoding="utf-8").read()
    comps = {}
    for cm in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)(?=\(comp\s|\(libparts)', t, re.S):
        ref, body = cm.group(1), cm.group(2)
        fp = re.search(r'\(footprint "([^"]*)"\)', body)
        m36 = re.search(r'\(tstamps "([0-9a-fA-F-]{36})"\)', body)     # component (symbol) tstamp
        msp = re.search(r'\(tstamps "(/[0-9a-fA-F/-]*)"\)', body)      # sheetpath tstamps (root-omitted, ends '/')
        # FULL hierarchical symbol path = sheetpath + symbol uuid. This MUST match the schematic or KiCad
        # can't link footprint<->symbol: parity storms, and "Update PCB from Schematic" duplicates the whole
        # board. The child sheet is instantiated 12x sharing ONE symbol uuid per role, so the per-channel
        # sheet prefix is what makes each of the 12 instances unique -- the symbol uuid alone collides.
        path = ((msp.group(1) if msp else "/") + m36.group(1)) if m36 else None
        val = re.search(r'\(value "([^"]*)"\)', body)
        fields = dict(re.findall(r'\(field\s+\(name "([^"]+)"\)\s*"([^"]*)"\)', body))
        comps[ref] = (fp.group(1) if fp else "", path,
                      val.group(1) if val else "", fields)
    pad_net = {}
    sec = t[t.index("(nets"):]
    for nb in re.split(r'\n\s*\(net\b', sec)[1:]:
        nm = re.search(r'\(name "([^"]+)"', nb)
        if not nm: continue
        for ref, pad in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', nb):
            pad_net[(ref, pad)] = nm.group(1)
    return comps, pad_net

TW_COMPS, TW_PADNET = parse_netlist(TW_NET)

def remap_net(net, n):
    if net in ("+VDC", "-VDC", "GND", ""): return net
    if net.startswith("unconnected-"): return None
    if net.startswith("/"): return "/ch%02d/%s" % (n, net[1:])
    return net

_netcache = {}
def ensure_net(board, name):
    if not name: return None
    if name in _netcache: return _netcache[name]
    ni = board.FindNet(name)
    if ni is None:
        ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni)
    _netcache[name] = ni
    return ni

def dup(item):
    try: d = item.Duplicate(False)
    except TypeError: d = item.Duplicate()
    try: d = d.Cast()
    except Exception: pass
    return d

def track_bbox_y(t):
    bb = t.GetBoundingBox()
    return bb.GetTop() / 1e6, bb.GetBottom() / 1e6

# =====================================================================================
def main():
    src = pcbnew.LoadBoard(SC_PCB)
    # channel-vs-COM classification
    chan_fps = [fp for fp in src.GetFootprints() if SC_ROLE.get(fp.GetReference()) in CH_ROLES]
    assert len(chan_fps) == len(CH_ROLES), "channel fp count %d != %d" % (len(chan_fps), len(CH_ROLES))
    chan_trk, com_trk, straddle = [], [], 0
    for t in src.GetTracks():
        top, bot = track_bbox_y(t)
        if top >= YSPLIT: chan_trk.append(t)
        elif bot <= YSPLIT: com_trk.append(t)
        else: straddle += 1
    print("channel fps=%d  channel tracks/vias=%d  COM tracks=%d  straddling=%d"
          % (len(chan_fps), len(chan_trk), len(com_trk), straddle))
    assert straddle == 0, "tracks straddle the COM/channel split - adjust YSPLIT"

    # output board = fresh 4-layer board (same stackup as the single channel; netclasses come
    # from twelve-channel.kicad_pro at DRC time). Building fresh avoids SWIG state corruption
    # from clearing a loaded board.
    out = pcbnew.CreateEmptyBoard()
    out.SetCopperLayerCount(4)
    try:
        out.SetLayerName(pcbnew.In1_Cu, "GND.Cu")
        out.SetLayerName(pcbnew.In2_Cu, "PWR.Cu")
    except Exception as e:
        print("layer name:", e)

    # ---- clone channels ----
    # Each tiled MCX carries its edge cutout on Dwgs.User (the single channel already demoted it,
    # since a closed rect straddling the outline is malformed). Read the notch back from each and
    # CUT it into the board outline (add_outline) -- keep the footprint cutout on Dwgs.User.
    EPS = 0.05
    notches = []   # (edge 'L'/'R', y0, y1, depth), absolute board coords
    for n in range(1, NCH + 1):
        dy = (n - 1) * PITCH
        off = V(0, dy)
        for fp in chan_fps:
            role = SC_ROLE[fp.GetReference()]; nref = chref(role, n)
            d = dup(fp); out.Add(d); d.Move(off)
            d.SetReference(nref)
            sym_path = TW_COMPS.get(nref, ("", None, "", {}))[1]
            if sym_path: d.SetPath(pcbnew.KIID_PATH(sym_path))   # full /sheet/symbol path (already root-omitted)
            try: d.SetDNP(role in DNP_ROLES)
            except Exception: pass
            for pad in d.Pads():
                nm = TW_PADNET.get((nref, pad.GetNumber()))
                if nm: pad.SetNet(ensure_net(out, nm))
            fld = TW_COMPS.get(nref, ("", None, "", {}))[3]     # add BOM fields from the netlist (the
            for k in ("MPN", "Manufacturer", "Distributor PN"):  # regenerated single channel drops them
                if fld.get(k):
                    try: d.SetField(k, fld[k])
                    except Exception: pass
            if role in MCX_ROLES:                       # read the edge notch (cutout stays on Dwgs.User)
                if role in RIGHT_MCX and DW:            # move the output jack to the new right edge and
                    p = next((q for q in d.Pads() if q.GetNumber() == "1"), None)   # extend its signal trace
                    old = (p.GetPosition().x / 1e6, p.GetPosition().y / 1e6) if p else None
                    d.Move(V(DW, 0))
                    p = next((q for q in d.Pads() if q.GetNumber() == "1"), None)
                    new = (p.GetPosition().x / 1e6, p.GetPosition().y / 1e6) if p else None
                    nm = TW_PADNET.get((nref, "1"))
                    if old and new and nm:              # start 1 mm left of the old pad so it laps the routed trace
                        _track(out, nm, pcbnew.F_Cu, [(old[0] - 1.0, old[1]), new], width=0.4)
                ex, ey = [], []
                for it in d.GraphicalItems():
                    if it.GetLayer() == pcbnew.Dwgs_User:
                        for p in (it.GetStart(), it.GetEnd()):
                            ex.append(pcbnew.ToMM(p.x)); ey.append(pcbnew.ToMM(p.y))
                if ex:
                    xlo, xhi, ylo, yhi = min(ex), max(ex), min(ey), max(ey)
                    if abs(xlo) < EPS:       notches.append(('L', ylo, yhi, xhi))       # opens through x=0
                    elif abs(xhi - W) < EPS: notches.append(('R', ylo, yhi, W - xlo))   # opens through x=W
        for t in chan_trk:
            d = dup(t); out.Add(d); d.Move(off)
            nm = remap_net(t.GetNetname(), n)
            if nm: d.SetNet(ensure_net(out, nm))

    H = max(fp.GetBoundingBox(False, False).GetBottom() for fp in out.GetFootprints()) / 1e6 + 11.0
    H = round(H, 1)
    print("cloned %d channels; board = %.1f x %.1f mm" % (NCH, W, H))

    place_common(out, H)
    add_planes(out, H)
    add_outline(out, H, notches)
    write_dru()
    pcbnew.SaveBoard(PCB, out)
    # Re-assert the project netclasses AFTER SaveBoard: an open KiCad GUI session (or SaveBoard
    # itself) can rewrite twelve-channel.kicad_pro with the netclasses FLATTENED, which silently
    # disables the hv_bias 0.6 mm DRC rule (bit us twice on 2026-07-11).
    g12.build_pro()
    print("saved", PCB)

# ---- common power section: J_PWR + J_DAISY + up-rated PTC/Schottky + 470uF bulk ----
COMMON_PLACE = {   # ref: (x, y, rot)  -- top strip, generous spacing (terminals 16 mm wide)
    "J_PWR":   (24.0, 10.0, 180),      # rot 180: wire funnels face the top/rear edge (out), like J5
    "J_DAISY": (48.0, 10.0, 180),
    # orientations chosen so each PTC's _F pad faces its Schottky's _F pad at the SAME y (straight
    # trace), the _IN pad points toward its bus, and the rail pad takes a plane via.
    "F_P": (64.0, 6.0, 270), "D_RP": (70.0, 6.0, 270),   # +rail: _F pads both lower, +VDC_IN upper
    "F_N": (64.0, 16.0, 90), "D_RN": (70.0, 16.0, 270),  # -rail: _F pads both upper, -VDC_IN lower
    "C_BULKP": (90.0, 10.0, 0), "C_BULKN": (112.0, 10.0, 0),
}
COMMON_ROLES = ["J_PWR", "J_DAISY", "F_P", "D_RP", "F_N", "D_RN", "C_BULKP", "C_BULKN"]

def _load_fp(fpid):
    nick, fname = fpid.split(":", 1)
    STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
    d = os.path.join(HERE, "lib", "cremat.pretty") if nick == "cremat" else "%s/%s.pretty" % (STOCK, nick)
    return pcbnew.FootprintLoad(d, fname)

def _pad_xy(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            return p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
    return None

def _set_model(fp, path):
    try: fp.Models().clear()
    except Exception: pass
    m = pcbnew.FP_3DMODEL(); m.m_Filename = path; m.m_Show = True
    fp.Models().push_back(m)

def place_common(b, H):
    # up-rated part refs come from the 12-ch netlist (J49/J50/F1/F2/D1/D2/C133/C134)
    jn = NCH * g12.PREFIX_COUNT["J"]; cn = NCH * g12.PREFIX_COUNT["C"]
    REF = {"J_PWR": "J%d" % (jn + 1), "J_DAISY": "J%d" % (jn + 2),
           "F_P": "F1", "F_N": "F2", "D_RP": "D1", "D_RN": "D2",
           "C_BULKP": "C%d" % (cn + 1), "C_BULKN": "C%d" % (cn + 2)}
    fps = {}
    for role in COMMON_ROLES:
        ref = REF[role]; fpid, uid, val, fields = TW_COMPS[ref]
        fp = _load_fp(fpid); assert fp, "missing common fp %s %s" % (ref, fpid)
        nick, fname = fpid.split(":", 1)
        try: fp.SetFPID(pcbnew.LIB_ID(nick, fname))     # keep library nickname (schematic-parity)
        except Exception: pass
        x, y, rot = COMMON_PLACE[role]
        fp.SetReference(ref); fp.SetValue(val)          # value + BOM fields from the netlist (= schematic)
        for k in ("MPN", "Manufacturer", "Distributor PN"):
            if fields.get(k):
                try: fp.SetField(k, fields[k])
                except Exception: pass
        if rot: fp.SetOrientationDegrees(rot)
        fp.SetPosition(V(0, 0))
        bb = fp.GetBoundingBox(False, False)
        cx = (bb.GetLeft() + bb.GetRight()) / 2e6; cy = (bb.GetTop() + bb.GetBottom()) / 2e6
        fp.SetPosition(V(x - cx, y - cy))
        if uid: fp.SetPath(pcbnew.KIID_PATH(uid))               # full path from netlist (root-level: "/" + symbol)
        if role in ("F_P", "F_N"):                      # KiCad ships no Fuse_1812 3D model; a PTC
            _set_model(fp, "${KICAD10_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_1812_4532Metric.step")  # is a 1812 chip
        b.Add(fp)
        for pad in fp.Pads():
            nm = TW_PADNET.get((ref, pad.GetNumber()))
            if nm: pad.SetNet(ensure_net(b, nm))
        fps[role] = fp
    # mounting holes: top strip (above ch1) + bottom strip (below ch12), clear of the edge MCX
    for i, (hx, hy) in enumerate([(8, 5), (W - 8, 5), (8, H - 5), (W - 8, H - 5)], 1):
        h = _load_fp("MountingHole:MountingHole_3.2mm_M3")
        if h:
            h.SetReference("H%d" % i); h.SetPosition(V(hx, hy)); h.Reference().SetVisible(False)
            try: h.SetBoardOnly(True)
            except Exception: pass
            b.Add(h)
    route_common(b, fps)

def _track(b, net, layer, pts, width=0.5):
    ni = ensure_net(b, net)
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c))
        t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNet(ni); b.Add(t)

def _via(b, net, xy, plane_layer):
    ni = ensure_net(b, net)
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(*xy)); v.SetDrill(mm(0.4)); v.SetWidth(mm(0.8))
    v.SetNet(ni); v.SetLayerPair(pcbnew.F_Cu, plane_layer); b.Add(v)

def _bus(b, net, layer, pads, bus_y):
    """Stub each pad vertically to a horizontal bus at bus_y (pins never cross their neighbours)."""
    xs = sorted(p[0] for p in pads)
    for p in pads:
        _track(b, net, layer, [p, (p[0], bus_y)])
    _track(b, net, layer, [(xs[0], bus_y), (xs[-1], bus_y)])

def _lroute(b, net, layer, a, c):
    _track(b, net, layer, [a, (c[0], a[1]), c])

def route_common(b, fps):
    P = lambda role, num: _pad_xy(fps[role], num)
    F = pcbnew.F_Cu
    # +VDC_IN carried on a bus ABOVE the parts, -VDC_IN on a bus BELOW: the vertical stub off the
    # outer terminal pin (pin1 / pin3) and off F_x.1 never crosses a neighbouring pad.
    _bus(b, "/+VDC_IN", F, [P("J_PWR", "1"), P("J_DAISY", "1"), P("F_P", "1")], 3.0)
    _bus(b, "/-VDC_IN", F, [P("J_PWR", "3"), P("J_DAISY", "3"), P("F_N", "1")], 21.0)
    # PTC out -> Schottky in: _F pads are placed at the same y -> straight trace, no pad crossed
    _lroute(b, "/+VDC_F", F, P("F_P", "2"), P("D_RP", "2"))
    _lroute(b, "/-VDC_F", F, P("F_N", "2"), P("D_RN", "1"))
    # rails to planes: Schottky outputs + SMD bulk rail pads each drop a via (screw-terminal GND is THT)
    _via(b, "+VDC", P("D_RP", "1"), pcbnew.B_Cu);  _via(b, "+VDC", P("C_BULKP", "1"), pcbnew.B_Cu)
    _via(b, "-VDC", P("D_RN", "2"), pcbnew.In2_Cu); _via(b, "-VDC", P("C_BULKN", "2"), pcbnew.In2_Cu)

# ---- board-wide plane pours (filled by fill_zones.py) ----
def add_planes(b, H):
    def add(net, layer, prio=None):
        ni = b.FindNet(net)
        if ni is None: print("no net", net); return
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(ni.GetNetCode()); z.SetIsFilled(True)
        if prio is not None: z.SetAssignedPriority(prio)
        o = z.Outline(); o.NewOutline()
        for px, py in [(1.5, 1.5), (W - 1.5, 1.5), (W - 1.5, H - 1.5), (1.5, H - 1.5)]:
            o.Append(mm(px), mm(py))
        b.Add(z)
    add("GND", pcbnew.In1_Cu)
    add("-VDC", pcbnew.In2_Cu)
    add("+VDC", pcbnew.B_Cu, prio=1)

def add_outline(b, H, notches):
    # rectangle W x H with the MCX edge notches cut in (24 per long edge). Same builder as the
    # single channel: walk top -> right (notch in to W-d) -> bottom -> left (notch in to d).
    Ln = sorted([n for n in notches if n[0] == 'L'], key=lambda n: n[1])
    Rn = sorted([n for n in notches if n[0] == 'R'], key=lambda n: n[1])
    pts = [(0, 0), (W, 0)]
    for _, y0, y1, d in Rn:
        pts += [(W, y0), (W - d, y0), (W - d, y1), (W, y1)]
    pts += [(W, H), (0, H)]
    for _, y0, y1, d in reversed(Ln):
        pts += [(0, y1), (d, y1), (d, y0), (0, y0)]
    pts += [(0, 0)]
    for a, c in zip(pts, pts[1:]):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
    print("outline: %d MCX edge notches (%dL / %dR)" % (len(notches), len(Ln), len(Rn)))

def write_dru():
    open(DRU, "w", encoding="utf-8").write(
        '(version 1)\n'
        '(rule "MCX edge-mount shield pad straddles its slot by design"\n'
        '   (constraint edge_clearance (min -2mm))\n'
        '   (condition "A.Library_Link == \'cremat:MCX_CONMCX013-T\'"))\n')

if __name__ == "__main__":
    main()
