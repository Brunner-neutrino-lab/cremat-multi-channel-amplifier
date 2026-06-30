#!/usr/bin/env python3
"""Generate the TWELVE-CHANNEL board schematic (Phase C, track C1 board-design).

=========================  R1: SINGLE SOURCE OF TRUTH  =========================
The 12 channels are GENERATED COPIES of the ONE frozen single channel. This script
**imports the single-channel channel-block builder** -- it does NOT re-declare the
per-channel circuit. The channel topology + parts live in exactly one place:

    integration/single-channel/design/gen_sch.py   (build_spec(), PARTS, SYMSRC, ...)

We import that module and call `sc.build_spec()` 12x, suffixing every per-channel net
and reference with `_ch01 ... _ch12` (shared rails +VDC/-VDC/GND stay global power
symbols). Edit a value/part/topology in the single-channel `build_spec()`/`PARTS`,
re-run THIS script, and all 12 channels change. The propagation path is demonstrated
in design/reports/propagation_demo.txt and described in ../INTERFACE.md.

This is the same net-label replication pattern as hardware/gen_sch.py, but the channel
definition is reused from the frozen Phase-B cell instead of re-typed here.

=========================  R2: SCHEMATIC-PARITY-CLEAN  =========================
This script also emits, for every symbol, the **lib-qualified Footprint field** and the
**MPN/Manufacturer/Distributor PN** properties. gen_pcb.py then writes lib-qualified
footprint FPIDs and copies those fields into the footprints, so
`kicad-cli pcb drc --schematic-parity --severity-warning` reports 0 parity items
(mounting holes get real schematic symbols too, so there are no extra_footprints).

Method (docs/KICAD_WITH_CLAUDE_CODE.md): place every symbol at rotation 0; connect pins
by dropping a net label (signal) or power symbol (rail) at the exact pin coordinate; no
routed wires. Connectivity is by net name + coincident pins; ERC proves it. UUIDs are
deterministic (uuid5) so re-runs reproduce the file.

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_sch.py
Validate: kicad-cli sch erc multi-channel-cremat-amplifier.kicad_sch
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
# ---- R1: import the FROZEN single-channel channel-block builder (the one source) ----
SC_DESIGN = os.path.abspath(os.path.join(HERE, "..", "..", "..",
                                         "integration", "single-channel", "design"))
sys.path.insert(0, SC_DESIGN)
import gen_sch as sc          # noqa: E402  -- the single-channel generator module

PROJ = "multi-channel-cremat-amplifier"
NS = uuid.UUID("c1d2e3f4-0000-4000-8000-000000000000")   # C1-namespaced (distinct from A/B)
VERSION = "20260306"
NCH = 12

# Reuse the single-channel helpers/metadata verbatim (R1: one definition).
G = sc.G
PARTS = sc.PARTS
SYMSRC = sc.SYMSRC
pins_of = sc.pins_of
indent = sc.indent
prefix_of = sc.prefix_of

# We must additionally place MountingHole symbols on the schematic so the 4 PCB mounting
# holes are NOT extra_footprints (R2). Register the symbol source in the imported module's
# SYMSRC so it is emitted in lib_symbols and pins_of works (MountingHole has no pins).
STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/symbols"
SYMSRC.setdefault("Mechanical:MountingHole",
                  (f"{STOCK}/Mechanical.kicad_sym", "MountingHole"))
FP_MOUNT = "MountingHole:MountingHole_3.2mm_M3"

def uid(*p): return str(uuid.uuid5(NS, ":".join(str(x) for x in p)))

# Shared (board-global) nets: stay as power symbols, NOT suffixed per channel.
GLOBAL_NETS = {"+VDC", "-VDC", "GND"}
# Roles in the single-channel spec that are BOARD-LEVEL shared, not per-channel: the standalone
# channel carries its own power entry, but the 12-channel board has ONE screw terminal. Drop it
# from the per-channel replication and emit it once below (R1: still the same PARTS["J_PWR"]).
BOARD_LEVEL_ROLES = {"J_PWR"}
# Per-channel filtered supply nets that need a PWR_FLAG so ERC sees a source through the 4.7R.
FILT_NETS = ["+VS_F", "-VS_F", "SHVP", "SHVN", "BLVP", "BLVN", "BVP", "BVN"]


def suffix_net(net, n):
    """Per-channel net name. Global rails unchanged; everything else gets _chNN."""
    if net in GLOBAL_NETS or net == "NC":
        return net
    return "%s_ch%02d" % (net, n)


def lib_symbols_block():
    return sc.lib_symbols_block()


# ----- emitters: thin wrappers around the single-channel emitters, but with our PROJ -----
def prop(name, val, x, y, hide=False, rot=0):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)%s\n'
            '\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)' % (name, val, x, y, rot, h))


def sym_instance(lib_id, ref, value, fp, dnp, x, y, paths, inst_uuid, extra=None):
    pathlines = "\n".join(
        '\t\t\t\t(path "%s" (reference "%s") (unit 1))' % (path, r) for path, r in paths)
    extralines = ""
    if extra:
        extralines = "\n" + "\n".join(prop(n, v, x, y, hide=True) for n, v in extra)
    return ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp %s)\n\t\t(uuid "%s")\n%s\n%s\n%s%s\n'
            '\t\t(instances\n\t\t\t(project "%s"\n%s\n\t\t\t)\n\t\t)\n\t)' % (
        lib_id, x, y, "yes" if dnp else "no", inst_uuid,
        prop("Reference", ref, x + 2, y - 2),
        prop("Value", value, x + 2, y + 2),
        prop("Footprint", fp, x, y, hide=True),
        extralines,
        PROJ, pathlines))


def label(net, x, y, key):
    return ('\t(label "%s"\n\t\t(at %s %s 0)\n\t\t(effects (font (size 1.27 1.27)) (justify left bottom))\n'
            '\t\t(uuid "%s")\n\t)' % (net, x, y, uid(key, "label", net, x, y)))


def power_sym(net, x, y, key):
    iu = uid(key, "pwr", net, x, y)
    return ('\t(symbol\n\t\t(lib_id "power:%s")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp no)\n\t\t(uuid "%s")\n'
            '\t\t(property "Reference" "#PWR" (at %s %s 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "%s" (at %s %s 0) (effects (font (size 1.27 1.27))))\n'
            '\t\t(pin "1" (uuid "%s"))\n'
            '\t\t(instances (project "%s" (path "/%s" (reference "#PWR?") (unit 1))))\n\t)' % (
        net, x, y, iu, x, y - 3, net, x, y + 3, uid(iu, "pin"), PROJ, key))


def pwrflag(net, x, y, root_uuid, ref):
    iu = uid(root_uuid, "flag", net, ref)
    return ('\t(symbol\n\t\t(lib_id "power:PWR_FLAG")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp no)\n\t\t(uuid "%s")\n'
            '\t\t(property "Reference" "%s" (at %s %s 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "PWR_FLAG" (at %s %s 0) (effects (font (size 1.27 1.27))))\n'
            '\t\t(pin "1" (uuid "%s"))\n'
            '\t\t(instances (project "%s" (path "/%s" (reference "%s") (unit 1))))\n\t)' % (
        x, y, iu, ref, x, y - 3, x, y + 3, uid(iu, "pin"), PROJ, root_uuid, ref))


def build():
    full_spec = sc.build_spec()  # R1: the ONE channel definition, imported.
    # Per-channel spec = the channel cell minus the board-level shared parts (screw terminal).
    spec = [row for row in full_spec if row[0] not in BOARD_LEVEL_ROLES]
    root = uid("board-root")

    # global per-prefix reference counter so every channel's refs are unique across the board
    cnt = {}
    nodes = []

    # Lay the 12 channel blocks out in a 12-row stack (schematic readability only; PCB
    # placement is independent in gen_pcb.py). Each channel's spec coords span ~0..335 in x
    # and ~9..155 in y; we offset each channel down by CH_DY and keep x as-is.
    CH_DY = 175.0

    refmap_per_ch = []           # list of {role: ref} for the netlist/PCB to follow
    for n in range(1, NCH + 1):
        y_off = (n - 1) * CH_DY
        refmap = {}
        for role, *_ in spec:
            pfx = prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1
            refmap[role] = "%s%d" % (pfx, cnt[pfx])
        refmap_per_ch.append(refmap)

        for role, lib_id, value, fp, dnp, (x, y), netmap in spec:
            gx, gy = G(x), G(y + y_off)
            iu = uid("sym", n, role)
            extra = None
            if role in PARTS:
                _v, mpn, mfr, dkpn = PARTS[role]
                extra = [("MPN", mpn), ("Manufacturer", mfr), ("Distributor PN", dkpn)]
            nodes.append(sym_instance(lib_id, refmap[role], value, fp, dnp, gx, gy,
                                      [("/" + root, refmap[role])], iu, extra=extra))
            pn = pins_of(lib_id)
            for p, net in netmap.items():
                px, py = pn[p]; ax, ay = G(gx + px), G(gy - py)
                if net == "NC":
                    nodes.append('\t(no_connect (at %s %s) (uuid "%s"))' % (ax, ay, uid("nc", n, role, p)))
                    continue
                if net in GLOBAL_NETS:
                    nodes.append(power_sym(net, ax, ay, "ch%02d:%s:%s" % (n, role, p)))
                else:
                    nodes.append(label(suffix_net(net, n), ax, ay, "ch%02d" % n))

        # per-channel PWR_FLAG on each filtered supply node (post-4.7R: ERC can't see the
        # passive-fed power_in pins driven, so flag them -- same trick as the single channel).
        fpx, fpy = pins_of("power:PWR_FLAG")["1"]
        fy = G(160 + y_off); fxs = G(40)
        for i, net in enumerate(FILT_NETS):
            ax, ay = G(fxs + i * 14), fy
            nodes.append(label(suffix_net(net, n), ax, ay, "ch%02d" % n))
            nodes.append(pwrflag(suffix_net(net, n), G(ax - fpx), G(ay + fpy), root,
                                 "#FLGF_%02d_%d" % (n, i)))

    # ===================== SHARED BOARD-LEVEL PARTS (one set, all channels) =====================
    # Power entry: ONE 3-pos screw terminal for the whole board (+12V/GND/-12V), placed at the
    # bottom. (Per-channel rail decoupling/bulk already live INSIDE each channel copy via the
    # reused spec -- C2 may add extra board bulk in Round 2.)
    bx, by = G(40), G((NCH) * CH_DY + 20)
    cnt["J"] = cnt.get("J", 0) + 1
    jpwr_ref = "J%d" % cnt["J"]
    jiu = uid("sym", "JPWR")
    jp_part = PARTS["J_PWR"]
    nodes.append(sym_instance(
        "Connector:Screw_Terminal_01x03", jpwr_ref, jp_part[0],
        "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal",
        False, bx, by, [("/" + root, jpwr_ref)], jiu,
        extra=[("MPN", jp_part[1]), ("Manufacturer", jp_part[2]), ("Distributor PN", jp_part[3])]))
    jp = pins_of("Connector:Screw_Terminal_01x03")
    fpx, fpy = pins_of("power:PWR_FLAG")["1"]
    for i, (p, net) in enumerate({"1": "+VDC", "2": "GND", "3": "-VDC"}.items(), 1):
        px, py = jp[p]; ax, ay = G(bx + px), G(by - py)
        nodes.append(power_sym(net, ax, ay, "JPWR:%s" % p))
        nodes.append(pwrflag(net, G(ax - fpx), G(ay + fpy), root, "#FLG%d" % i))

    # Central rail-entry bulk reservoir pair (board-shared, C2 real-parts gate 2026-06-28):
    # Nichicon UVR1V471MPD 470uF/35V radial THT, near J_PWR. Backs the 12x distributed 100uF.
    # CBULK_P: +VDC <-> GND ; CBULK_N: GND <-> -VDC (correct polarity: pin1=+ for C_Polarized).
    FP_CRAD = "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm"
    CBULK = ("470uF 35V", "UVR1V471MPD", "Nichicon", "493-1084-ND")
    cbulk_spec = [
        ("CBULK_P", {"1": "+VDC", "2": "GND"}, G(bx + 25)),
        ("CBULK_N", {"1": "GND", "2": "-VDC"}, G(bx + 40)),
    ]
    cpins = pins_of("Device:C_Polarized")
    for role, netmap, cx in cbulk_spec:
        cnt["C"] = cnt.get("C", 0) + 1
        cref = "C%d" % cnt["C"]
        ciu = uid("sym", role)
        nodes.append(sym_instance("Device:C_Polarized", cref, CBULK[0], FP_CRAD, False,
                                  cx, by, [("/" + root, cref)], ciu,
                                  extra=[("MPN", CBULK[1]), ("Manufacturer", CBULK[2]),
                                         ("Distributor PN", CBULK[3])]))
        for p, net in netmap.items():
            px, py = cpins[p]; ax, ay = G(cx + px), G(by - py)
            nodes.append(power_sym(net, ax, ay, "%s:%s" % (role, p)))

    # ===================== MOUNTING HOLES (R2: real symbols -> no extra_footprints) ===========
    # 4x M3 mounting holes as schematic symbols (no pins, off-BOM is fine but in_bom=yes ok).
    mhx, mhy = G(120), G((NCH) * CH_DY + 20)
    for i in range(1, 5):
        cnt["H"] = cnt.get("H", 0) + 1
        href = "H%d" % cnt["H"]
        miu = uid("sym", "MH", i)
        nodes.append(sym_instance("Mechanical:MountingHole", href, "MountingHole_3.2mm_M3",
                                  FP_MOUNT, False, G(mhx + (i - 1) * 12), mhy,
                                  [("/" + root, href)], miu))

    si = '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)'
    out = ('(kicad_sch\n\t(version %s)\n\t(generator "gen_sch.py")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "A2")\n'
           '\t(title_block\n\t\t(title "Multi-channel SiPM CSP+shaper+buffer (12 channel)")\n'
           '\t\t(company "Yale / Brunner Neutrino Lab")\n\t)\n%s\n%s\n%s\n\t(embedded_fonts no)\n)\n' % (
        VERSION, root, lib_symbols_block(), "\n".join(nodes), si))
    out_path = os.path.join(HERE, PROJ + ".kicad_sch")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote %s.kicad_sch: %d channels x %d roles = %d channel symbols (+ shared parts)" % (
        PROJ, NCH, len(spec), NCH * len(spec)))
    return refmap_per_ch


if __name__ == "__main__":
    build()
