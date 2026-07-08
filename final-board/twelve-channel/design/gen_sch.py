#!/usr/bin/env python3
"""Generate the 12-channel board schematic as a KiCad HIERARCHICAL design.

Single source of truth = the reviewed single-channel cell
(../../../integration/single-channel/design/gen_sch.py). This script:

  * CHILD  channel.kicad_sch : the single channel MINUS the board-level power entry
    (roles J_PWR, F_P/D_RP/F_N/D_RN, C_BULKP/C_BULKN dropped). Every symbol is placed
    ONCE but carries a 12-path (instances) block with strided refs, so KiCad expands it
    into 12 channels. The channel is self-contained (its MCX jacks are inside it; only
    +VDC/-VDC/GND cross the boundary as GLOBAL power) -> NO hierarchical pins needed,
    exactly like reference/cremat-x6-board. Local nets auto-scope to /chNN/<net>.
  * ROOT   twelve-channel.kicad_sch : 12 (sheet) instances (ch01..ch12) + ONE common
    power section shared by all channels:
      - power IN  (J_PWR)  and a board-to-board DAISY out (J_DAISY), both on the RAW
        rails {+VDC_IN,GND,-VDC_IN} so the supply feeds this board AND passes through to
        a second stacked 12-ch board; each board self-protects.
      - reverse-polarity + fault-interrupt block UP-RATED for 12x current: PTC (F_P/F_N,
        ~1.1 A hold) + series Schottky (D_RP/D_RN, 2 A SMA) -> board rails; central bulk
        (C_BULKP/C_BULKN, 470 uF) backs the 12x distributed 10 uF.

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_sch.py
Validate: kicad-cli sch erc twelve-channel.kicad_sch ; kicad-cli sch export netlist ...
"""
import os, sys, re, uuid, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
SC_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "integration", "single-channel", "design"))

# import the single-channel generator under a distinct module name
_spec = importlib.util.spec_from_file_location("sc_gen_sch", os.path.join(SC_DIR, "gen_sch.py"))
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)

PROJ = "twelve-channel"
NCH = 12
NS = uuid.UUID("c1d2e3f4-0000-4000-8000-000000000000")     # C-phase namespace (distinct from A/B)
def uid(*p): return str(uuid.uuid5(NS, ":".join(str(x) for x in p)))
ROOT_UUID = uid("root")
CHILD_UUID = uid("child")
SHEET = [uid("sheet", n) for n in range(NCH)]               # (sheet) block uuid per channel

# ---- which single-channel roles are BOARD-LEVEL (emitted once on the root, not per channel)
BOARD_ROLES = ["J_PWR", "F_P", "D_RP", "F_N", "D_RN", "C_BULKP", "C_BULKN"]
CH_ROLES = [r for r in sc.ROLES if r not in BOARD_ROLES]

def build_refmap(roles):
    cnt, rm = {}, {}
    for r in roles:
        p = sc.prefix_of(r); cnt[p] = cnt.get(p, 0) + 1
        rm[r] = "%s%d" % (p, cnt[p])
    return rm, cnt

CH_BASE_REF, PREFIX_COUNT = build_refmap(CH_ROLES)          # ch1 refs + per-channel prefix counts

def stride_ref(ref, n):                                     # n = 1..NCH
    m = re.match(r'^([A-Za-z#]+?)(\d+)$', ref)
    pfx, num = m.group(1), int(m.group(2))
    return "%s%d" % (pfx, num + (n - 1) * PREFIX_COUNT[pfx])

# =====================================================================================
#  multi-instance emitters (for the CHILD sheet)  -- monkeypatched into sc
# =====================================================================================
def _paths(refs):
    return "\n".join('\t\t\t\t(path "/%s/%s" (reference "%s") (unit 1))'
                     % (ROOT_UUID, SHEET[n], refs[n]) for n in range(NCH))

def instances_multi(refs):
    return '\t\t(instances\n\t\t\t(project "%s"\n%s\n\t\t\t)\n\t\t)' % (PROJ, _paths(refs))

_orig_sym = sc.sym_instance
def sym_instance_multi(lib_id, ref, value, fp, dnp, x, y, rot, root, iu, extra=None, hide_val=False):
    s = _orig_sym(lib_id, ref, value, fp, dnp, x, y, rot, ROOT_UUID, iu, extra, hide_val)
    i = s.rindex("\t\t(instances")
    refs = [stride_ref(ref, n) for n in range(1, NCH + 1)]
    return s[:i] + instances_multi(refs) + "\n\t)"

PWRCTR = [0]; FLGCTR = [0]
def _alloc(ctr):
    base = ctr[0]; ctr[0] += NCH
    return [base + 1 + i for i in range(NCH)]

def power_sym_multi(net, x, y, key, rot=0):
    refs = _alloc(PWRCTR); prefs = ["#PWR%d" % r for r in refs]
    iu = uid("pwr", net, x, y, refs[0])
    return ('\t(symbol\n\t\t(lib_id "power:%s")\n\t\t(at %s %s %d)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp no)\n\t\t(uuid "%s")\n'
            '\t\t(property "Reference" "%s" (at %s %s 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "%s" (at %s %s 0) (effects (font (size 1.27 1.27))))\n'
            '\t\t(pin "1" (uuid "%s"))\n'
            '%s\n\t)' % (net, x, y, rot, iu, prefs[0], x, y - 3, net, x, y + 3,
                         uid(iu, "pin"), instances_multi(prefs)))

def pwrflag_multi(net, x, y, ref, rot=0):
    refs = _alloc(FLGCTR); frefs = ["#FLG%d" % r for r in refs]
    iu = uid("flag", net, refs[0])
    return ('\t(symbol\n\t\t(lib_id "power:PWR_FLAG")\n\t\t(at %s %s %d)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp no)\n\t\t(uuid "%s")\n'
            '\t\t(property "Reference" "%s" (at %s %s 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "PWR_FLAG" (at %s %s 0) (hide yes) (effects (font (size 1 1))))\n'
            '\t\t(pin "1" (uuid "%s"))\n'
            '%s\n\t)' % (x, y, rot, iu, ref, x, y - 3, x, y + 3,
                         uid(iu, "pin"), instances_multi(frefs)))

# CONCRETE single-instance power symbol for the ROOT sheet (refs offset ABOVE the child's #PWR
# range so nothing collides and the whole design is fully annotated -> no annotate prompt on
# Update-from-Schematic). Signature matches sc.power_sym (net, x, y, key, rot).
ROOT_PWRN = [0]
def root_power_sym(net, x, y, key, rot=0):
    ROOT_PWRN[0] += 1
    pref = "#PWR%d" % (PWRCTR[0] + 200 + ROOT_PWRN[0])
    iu = uid("rootpwr", net, x, y, pref)
    inst = ('\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "/%s" (reference "%s") (unit 1))\n'
            '\t\t\t)\n\t\t)' % (PROJ, ROOT_UUID, pref))
    return ('\t(symbol\n\t\t(lib_id "power:%s")\n\t\t(at %s %s %d)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp no)\n\t\t(uuid "%s")\n'
            '\t\t(property "Reference" "%s" (at %s %s 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "%s" (at %s %s 0) (effects (font (size 1.27 1.27))))\n'
            '\t\t(pin "1" (uuid "%s"))\n%s\n\t)' % (
        net, x, y, rot, iu, pref, x, y - 3, net, x, y + 3, uid(iu, "pin"), inst))

# =====================================================================================
#  header / footer helpers
# =====================================================================================
def sheet_file(file_uuid, paper, nodes):
    return ('(kicad_sch\n\t(version 20260306)\n\t(generator "gen_sch.py")\n\t(generator_version "10.0")\n'
            '\t(uuid "%s")\n\t(paper "%s")\n'
            '\t(title_block\n\t\t(title "12-channel SiPM CSP+shaper+buffer")\n'
            '\t\t(company "Yale / Brunner Neutrino Lab")\n\t)\n%s\n%s\n\t(embedded_fonts no)\n)\n'
            % (file_uuid, paper, sc.lib_symbols_block(),
               "\n".join(nodes) + '\n\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)'))

# =====================================================================================
#  CHILD  channel.kicad_sch
# =====================================================================================
def build_child():
    sc.sym_instance = sym_instance_multi
    sc.power_sym = power_sym_multi
    sc.pwrflag = pwrflag_multi
    sc.ROLES = CH_ROLES
    sc.ROOT = ROOT_UUID                        # power_sym/pwrflag helpers read sc.ROOT indirectly
    sc.NODES[:] = []; sc.SEGS[:] = []; sc.COVER.clear(); sc.FLAGN[0] = 0
    for role in CH_ROLES:
        extra = None
        if role in sc.PARTS:
            _v, mpn, mfr, dkpn = sc.PARTS[role]
            extra = [("MPN", mpn), ("Manufacturer", mfr), ("Distributor PN", dkpn)]
        sc.place(role, CH_BASE_REF[role], extra)
    sc.layout_channel()
    sc.auto_junctions()
    # coverage self-check on channel pins
    missing = [ "%s.%s" % (CH_BASE_REF[r], p)
                for r in CH_ROLES for p in sc.SPEC[r][3] if sc.P(r, p) not in sc.COVER ]
    if missing: print("WARNING child: %d uncovered pins: %s" % (len(missing), missing[:8]))
    open(os.path.join(HERE, "channel.kicad_sch"), "w", encoding="utf-8").write(
        sheet_file(CHILD_UUID, "A3", list(sc.NODES)))
    print("wrote channel.kicad_sch: %d channel symbols x%d, %d wire segs" % (len(CH_ROLES), NCH, len(sc.SEGS)))

# =====================================================================================
#  ROOT  twelve-channel.kicad_sch  (12 sheet instances + common power section)
# =====================================================================================
# up-rated board-level part metadata (override the single-channel values for 12x current)
# MPNs verified in-stock 2026-07-08 (see models-bom/SOURCING-VERIFICATION); all three provisional
# picks were rejected (obsolete / wrong package / fictional) and replaced.
UPRATED = {
    "F_P":    ("PTC 1.1A 24V",  "1812L110/24DR", "Littelfuse",       "F5632CT-ND"),
    "F_N":    ("PTC 1.1A 24V",  "1812L110/24DR", "Littelfuse",       "F5632CT-ND"),
    "D_RP":   ("SSA24",         "SSA24",         "onsemi",           "SSA24CT-ND"),
    "D_RN":   ("SSA24",         "SSA24",         "onsemi",           "SSA24CT-ND"),
    "C_BULKP":("470uF 35V",     "EEE-FN1V471UP", "Panasonic",        "10-EEE-FN1V471UPCT-ND"),
    "C_BULKN":("470uF 35V",     "EEE-FN1V471UP", "Panasonic",        "10-EEE-FN1V471UPCT-ND"),
    "J_DAISY":("Screw terminal 3-pos 5.08mm", "1715734", "Phoenix Contact", "277-1264-ND"),
}
FP_PTC_BIG   = "Fuse:Fuse_1812_4532Metric"
FP_CPELEC_BIG= "Capacitor_SMD:CP_Elec_10x10.5"

def build_root():
    # restore single-instance emitters
    sc.sym_instance = _orig_sym
    sc.power_sym = root_power_sym                # concrete #PWR refs (no "?" -> no annotate prompt)
    sc.pwrflag = sc._pwrflag_orig
    sc.ROOT = ROOT_UUID; sc.PROJ = PROJ

    # up-rate board-level part values + footprints, and add the DAISY connector to SPEC
    for role, meta in UPRATED.items():
        sc.PARTS[role] = meta
    lib, fp, dnp, nm, at = sc.SPEC["F_P"]; sc.SPEC["F_P"] = (lib, FP_PTC_BIG, dnp, nm, at)
    lib, fp, dnp, nm, at = sc.SPEC["F_N"]; sc.SPEC["F_N"] = (lib, FP_PTC_BIG, dnp, nm, at)
    lib, fp, dnp, nm, at = sc.SPEC["C_BULKP"]; sc.SPEC["C_BULKP"] = (lib, FP_CPELEC_BIG, dnp, nm, at)
    lib, fp, dnp, nm, at = sc.SPEC["C_BULKN"]; sc.SPEC["C_BULKN"] = (lib, FP_CPELEC_BIG, dnp, nm, at)
    # DAISY screw terminal: parallel to J_PWR on the RAW rails, placed just below it
    sc.SPEC["J_DAISY"] = ("Connector:Screw_Terminal_01x03", sc.FP_SCREW, False,
                          {"1": "+VDC_IN", "2": "GND", "3": "-VDC_IN"}, (50.80, 226.06, 0))

    ROOT_ROLES = ["J_PWR", "J_DAISY", "F_P", "D_RP", "F_N", "D_RN", "C_BULKP", "C_BULKN"]
    jn = NCH * PREFIX_COUNT["J"]; cn = NCH * PREFIX_COUNT["C"]
    ROOT_REF = {"J_PWR": "J%d" % (jn + 1), "J_DAISY": "J%d" % (jn + 2),
                "F_P": "F1", "F_N": "F2", "D_RP": "D1", "D_RN": "D2",
                "C_BULKP": "C%d" % (cn + 1), "C_BULKN": "C%d" % (cn + 2)}

    sc.NODES[:] = []; sc.SEGS[:] = []; sc.COVER.clear(); sc.FLAGN[0] = FLGCTR[0] + 100   # root #FLG above child range
    sc.ROLES = ROOT_ROLES
    for role in ROOT_ROLES:
        _v, mpn, mfr, dkpn = sc.PARTS[role]
        sc.place(role, ROOT_REF[role], [("MPN", mpn), ("Manufacturer", mfr), ("Distributor PN", dkpn)])
    sc.layout_power()
    # DAISY out to the stacked 2nd board: parallel tap on the RAW rails (label-connected to the
    # same +VDC_IN/GND/-VDC_IN nets J_PWR drives). A short stub off each pin carries the label.
    for dp, net, j in [("1", "+VDC_IN", "right bottom"), ("3", "-VDC_IN", "right bottom")]:
        a = sc.P("J_DAISY", dp); sc.W(a, (a[0] - 6.35, a[1])); sc.lbl(net, (a[0] - 6.35, a[1]), j=j)
    g = sc.P("J_DAISY", "2"); sc.W(g, (g[0] - 6.35, g[1])); sc.pwr("GND", (g[0] - 6.35, g[1]))
    sc.auto_junctions()

    nodes = list(sc.NODES)
    # ---- 12 sheet instances: 2 columns x 6 rows ----
    SW, SHH = 46.0, 26.0
    COLX = [150.0, 205.0]; ROWY = [20.0 + r * 32.0 for r in range(6)]
    for n in range(NCH):
        col, row = n // 6, n % 6
        x, y = COLX[col], ROWY[row]
        nodes.append(
            '\t(sheet\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n'
            '\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n'
            '\t\t(stroke (width 0.1524) (type solid))\n\t\t(fill (color 0 0 0 0.0000))\n\t\t(uuid "%s")\n'
            '\t\t(property "Sheetname" "ch%02d" (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left bottom)))\n'
            '\t\t(property "Sheetfile" "channel.kicad_sch" (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left top)))\n'
            '\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "/%s" (page "%d"))\n\t\t\t)\n\t\t)\n\t)'
            % (x, y, SW, SHH, SHEET[n], n + 1, x, y - 0.7, x, y + SHH + 0.5, PROJ, ROOT_UUID, n + 2))
    open(os.path.join(HERE, "%s.kicad_sch" % PROJ), "w", encoding="utf-8").write(
        sheet_file(ROOT_UUID, "A2", nodes))
    print("wrote %s.kicad_sch: %d sheet instances + %d common-power parts" % (PROJ, NCH, len(ROOT_ROLES)))

# =====================================================================================
#  PROJECT FILE  twelve-channel.kicad_pro  (inherit single-channel settings; fix net-class
#  patterns for the hierarchical /chNN/<net> names; list the 13 sheets)
# =====================================================================================
# (netclass, pattern) -- globbed so a pattern matches the same net in every channel instance
NETCLASS_PATTERNS = [
    ("hv_bias", "*BIAS*"), ("hv_bias", "*SIPM*"), ("hv_bias", "*/FE"), ("hv_bias", "*/N_filt"),
    ("signal", "*CSP_OUT*"), ("signal", "*CSP_IN*"), ("signal", "*/SH_OUT"),
    ("signal", "*/SHAPER_OUT"), ("signal", "*OUT_50*"), ("signal", "*/BUF_FB"), ("signal", "*/BUF_OUT"),
    ("power", "GND"), ("power", "+VDC"), ("power", "-VDC"), ("power", "*VDC_IN*"), ("power", "*VDC_F*"),
    ("power", "*VS_F*"), ("power", "*/SHVP"), ("power", "*/SHVN"), ("power", "*/BLVP"),
    ("power", "*/BLVN"), ("power", "*/BVP"), ("power", "*/BVN"),
]

def build_pro():
    import json
    d = json.load(open(os.path.join(SC_DIR, "channel.kicad_pro"), encoding="utf-8"))
    d["meta"]["filename"] = "%s.kicad_pro" % PROJ
    d.setdefault("net_settings", {})["netclass_patterns"] = [
        {"netclass": nc, "pattern": p} for nc, p in NETCLASS_PATTERNS]
    d["sheets"] = [[ROOT_UUID, PROJ]] + [[SHEET[n], "ch%02d" % (n + 1)] for n in range(NCH)]
    json.dump(d, open(os.path.join(HERE, "%s.kicad_pro" % PROJ), "w", encoding="utf-8"), indent=2)
    print("wrote %s.kicad_pro (%d net-class patterns, %d sheets)" % (PROJ, len(NETCLASS_PATTERNS), NCH + 1))

if __name__ == "__main__":
    # stash pristine single-instance power emitters before any patching
    sc._power_sym_orig = sc.power_sym
    sc._pwrflag_orig = sc.pwrflag
    build_child()
    build_root()
    build_pro()
