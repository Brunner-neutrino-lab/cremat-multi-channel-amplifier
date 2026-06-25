#!/usr/bin/env python3
"""Generate the standalone CR-200 shaper eval-board schematic (A4 shaper-design).

Two milestones (env SHAPER_MS, default M2):
  M1 = CR-200 (1us) + pole-zero trim + per-rail decoupling + MCX I/O + screw terminal.
  M2 = M1 + CR-210 baseline restorer (BLR) inserted between CR-200 out and OUT, with the
       JP_BLR 0R bypass (populate-XOR per CR-160-R7 JU1).

Method (see docs/KICAD_WITH_CLAUDE_CODE.md): place every symbol at rotation 0 and connect
pins by dropping a net label (signal) or power symbol (rail) at the *exact* pin coordinate
-- no routed wires. Connectivity is by net name + coincident pins; ERC proves it. UUIDs are
deterministic (uuid5) so re-runs reproduce the file.

Topology basis = reference/cremat-CR-160-R7/CR-160-R7.net:
  CR-200 (U4): 1=in 2=P/Z 3=GND 4=-Vs 5=+Vs 6=GND 7=GND 8=out
    P/Z network = 200k trimpot across in(1)<->P/Z(2), wiper to the input node (R7).
  CR-210 (U5): 1=in 2=GND 3=GND 4=-Vs 5=+Vs 6=GND 7=GND 8=out   (pin2=GND vs CR-200's P/Z)
    JU1 bridges CR-200 out (CR-210 in) <-> CR-210 out  => closing it bypasses the BLR.
  Per-rail decoupling: 4.7 ohm series + 10uF bulk + 0.1uF HF on each supply pin.

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_sch.py        (M2)
      SHAPER_MS=M1 "C:/Program Files/KiCad/10.0/bin/python.exe" gen_sch.py
Validate: kicad-cli sch erc shaper.kicad_sch
"""
import os, re, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
CREMAT_SYM = os.path.join(HERE, "lib", "cremat.kicad_sym")
STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/symbols"
PROJ = "shaper"
NS = uuid.UUID("a4b2c3d4-0000-4000-8000-000000000000")   # A4-namespaced (distinct from hardware/)
VERSION = "20260306"
MS = os.environ.get("SHAPER_MS", "M2").upper()
assert MS in ("M1", "M2"), "SHAPER_MS must be M1 or M2"

def uid(*p): return str(uuid.uuid5(NS, ":".join(str(x) for x in p)))
def G(v): return round(round(float(v) / 1.27) * 1.27, 4)  # snap to 1.27mm connection grid

# ---------- minimal S-expression symbol-library reader ----------
def _match(text, start):
    depth, i, n = 0, start, len(text); in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == '\\': i += 1
            elif c == '"': in_str = False
        elif c == '"': in_str = True
        elif c == '(': depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0: return i + 1
        i += 1
    raise ValueError("unbalanced")

def extract_symbol(libtext, name):
    m = re.search(r'\(symbol\s+"%s"' % re.escape(name), libtext)
    if not m: raise KeyError(name)
    return libtext[m.start():_match(libtext, m.start())]

def pin_coords(block):
    out = {}
    for pm in re.finditer(r'\(pin\b', block):
        s = pm.start(); e = _match(block, s); sub = block[s:e]
        at = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\)', sub)
        num = re.search(r'\(number\s+"([^"]+)"', sub)
        if at and num:
            out[num.group(1)] = (float(at.group(1)), float(at.group(2)))
    return out

_libcache = {}
def lib_text(path):
    if path not in _libcache:
        with open(path, encoding="utf-8") as f: _libcache[path] = f.read()
    return _libcache[path]

SYMSRC = {
    "cremat:CR-200": (CREMAT_SYM, "CR-200"),
    "cremat:CR-210": (CREMAT_SYM, "CR-210"),
    "Device:R": (f"{STOCK}/Device.kicad_sym", "R"),
    "Device:C": (f"{STOCK}/Device.kicad_sym", "C"),
    "Device:C_Polarized": (f"{STOCK}/Device.kicad_sym", "C_Polarized"),
    "Device:R_Potentiometer_Trim_US": (f"{STOCK}/Device.kicad_sym", "R_Potentiometer_Trim_US"),
    "Connector:Conn_Coaxial": (f"{STOCK}/Connector.kicad_sym", "Conn_Coaxial"),
    "Connector:Screw_Terminal_01x03": (f"{STOCK}/Connector.kicad_sym", "Screw_Terminal_01x03"),
    "power:+VDC": (f"{STOCK}/power.kicad_sym", "+VDC"),
    "power:-VDC": (f"{STOCK}/power.kicad_sym", "-VDC"),
    "power:GND": (f"{STOCK}/power.kicad_sym", "GND"),
    "power:PWR_FLAG": (f"{STOCK}/power.kicad_sym", "PWR_FLAG"),
}
_pins = {}
def pins_of(lib_id):
    if lib_id not in _pins:
        f, nm = SYMSRC[lib_id]
        _pins[lib_id] = pin_coords(extract_symbol(lib_text(f), nm))
    return _pins[lib_id]

def lib_symbols_block():
    parts = []
    for lib_id, (f, nm) in SYMSRC.items():
        raw = extract_symbol(lib_text(f), nm)
        raw = raw.replace('(symbol "%s"' % nm, '(symbol "%s"' % lib_id, 1)
        parts.append(raw)
    body = "\n".join(indent(p, 2) for p in parts)
    return "\t(lib_symbols\n%s\n\t)" % body

def indent(s, n):
    pad = "\t" * n
    return "\n".join(pad + ln if ln else ln for ln in s.splitlines())

# ---------- footprints ----------
FP_R     = "Resistor_SMD:R_0805_2012Metric"
FP_C     = "Capacitor_SMD:C_0805_2012Metric"      # 0.1uF HF + 10uF local bulk (A6: Samsung CL21, 0805)
FP_CPELEC= "Capacitor_SMD:CP_Elec_6.3x7.7"        # 100uF board bulk (A6: Nichicon UWT SMD can)
FP_SIP   = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
FP_TRIM  = "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical"
FP_MCX   = "cremat:MCX_CONMCX013_EdgeMount"
FP_SCREW = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal"

# ---------- real-part metadata (A6 Models-BOM, source of truth) ----------
# keyed by spec role -> (Value, MPN, Manufacturer, DigiKey_PN). Swapped 1:1 from generics.
# Value is the human value PLUS the chosen MPN's defining spec (so the BOM Value column is the
# real part). Footprints set per-role in build_spec below (unchanged except 10uF 1206->0805).
PARTS = {
    "U_SH":   ("CR-200-1us-R2.1",     "CR-200-1us-R2.1",   "Cremat Inc",               "N/A (Cremat-direct)"),
    "U_BLR":  ("CR-210-R0",           "CR-210-R0",         "Cremat Inc",               "N/A (Cremat-direct)"),
    "RV_PZ":  ("200k",                "3296W-1-204LF",     "Bourns",                   "3296W-204LF-ND"),
    "R_OUT":  ("49.9",                "RC0805FR-0749R9L",  "Yageo",                    "311-49.9CRCT-ND"),
    "R_SHP":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                    "311-4.7ARCT-ND"),
    "R_SHN":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                    "311-4.7ARCT-ND"),
    "R_BLP":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                    "311-4.7ARCT-ND"),
    "R_BLN":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                    "311-4.7ARCT-ND"),
    "JP_BLR": ("0R",                  "RC0805JR-070RL",    "Yageo",                    "311-0.0ARCT-ND"),
    "C_SHPb": ("10uF",                "CL21A106KAYNNNE",   "Samsung Electro-Mechanics","1276-1037-1-ND"),
    "C_SHNb": ("10uF",                "CL21A106KAYNNNE",   "Samsung Electro-Mechanics","1276-1037-1-ND"),
    "C_BLPb": ("10uF",                "CL21A106KAYNNNE",   "Samsung Electro-Mechanics","1276-1037-1-ND"),
    "C_BLNb": ("10uF",                "CL21A106KAYNNNE",   "Samsung Electro-Mechanics","1276-1037-1-ND"),
    "C_SHPh": ("0.1uF",               "CL21B104KBCNNNC",   "Samsung Electro-Mechanics","1276-1000-1-ND"),
    "C_SHNh": ("0.1uF",               "CL21B104KBCNNNC",   "Samsung Electro-Mechanics","1276-1000-1-ND"),
    "C_BLPh": ("0.1uF",               "CL21B104KBCNNNC",   "Samsung Electro-Mechanics","1276-1000-1-ND"),
    "C_BLNh": ("0.1uF",               "CL21B104KBCNNNC",   "Samsung Electro-Mechanics","1276-1000-1-ND"),
    "C_BULKP":("100uF",               "UWT1V101MCL1GS",    "Nichicon",                 "493-2203-1-ND"),
    "C_BULKN":("100uF",               "UWT1V101MCL1GS",    "Nichicon",                 "493-2203-1-ND"),
    "J_IN":   ("MCX CONMCX013",       "CONMCX013",         "TE Connectivity / Linx",   "343-CONMCX013-ND"),
    "J_OUT":  ("MCX CONMCX013",       "CONMCX013",         "TE Connectivity / Linx",   "343-CONMCX013-ND"),
    "J_PWR":  ("+12V/GND/-12V",       "1715734",           "Phoenix Contact",          "277-1264-ND"),
}

# ---------- netlist spec ----------
# role : (lib_id, value, footprint, dnp, (x,y), {pin#: net})
# nets +VDC/-VDC/GND -> power symbol; anything else -> local label.
def _val(role):
    """Real-part Value string from the A6 PARTS table (falls back to role if absent)."""
    return PARTS[role][0] if role in PARTS else role

def build_spec(ms):
    spec = [
        # ---- input: MCX jack ----
        ("J_IN",  "Connector:Conn_Coaxial", _val("J_IN"), FP_MCX, False, (30, 40),
            {"1": "SH_IN", "2": "GND"}),

        # ---- CR-200 shaper (supply pins retargeted to filtered rails below) ----
        ("U_SH",  "cremat:CR-200", _val("U_SH"), FP_SIP, False, (70, 35),
            {"1": "SH_IN", "2": "PZ", "3": "GND", "4": "SHVN", "5": "SHVP",
             "6": "GND", "7": "GND", "8": "SH_OUT"}),
        # pole-zero trim (200k): across input(1) <-> P/Z(2), wiper to input node (= CR-160-R7 R7).
        # This trimpot ALONE is the CR-200 pole-zero network. (No 100k fixed companion: the
        # CR-160-R7 R9/100k sits in net code 10 -> MAX4649 mux U7.6 + gain/polarity DIP SW1.1,
        # i.e. the buffer/mux section this sub-component excludes -- removed 2026-06-25 reconcile.)
        ("RV_PZ", "Device:R_Potentiometer_Trim_US", _val("RV_PZ"), FP_TRIM, False, (70, 70),
            {"1": "SH_IN", "2": "PZ", "3": "PZ"}),

        # ---- per-rail decoupling at the CR-200: 4.7R series + 10uF bulk + 0.1uF HF ----
        ("R_SHP", "Device:R", _val("R_SHP"), FP_R, False, (52, 18), {"1": "+VDC", "2": "SHVP"}),
        ("C_SHPb","Device:C", _val("C_SHPb"),FP_C, False, (60, 18), {"1": "SHVP", "2": "GND"}),
        ("C_SHPh","Device:C", _val("C_SHPh"),FP_C, False, (66, 18), {"1": "SHVP", "2": "GND"}),
        ("R_SHN", "Device:R", _val("R_SHN"), FP_R, False, (52, 56), {"1": "-VDC", "2": "SHVN"}),
        ("C_SHNb","Device:C", _val("C_SHNb"),FP_C, False, (60, 56), {"1": "SHVN", "2": "GND"}),
        ("C_SHNh","Device:C", _val("C_SHNh"),FP_C, False, (66, 56), {"1": "SHVN", "2": "GND"}),
    ]
    if ms == "M1":
        # output: 49.9R series + OUT jack, straight off the CR-200 output.
        spec += [
            ("R_OUT", "Device:R", _val("R_OUT"), FP_R, False, (150, 35), {"1": "SH_OUT", "2": "OUT"}),
            ("J_OUT", "Connector:Conn_Coaxial", _val("J_OUT"), FP_MCX, False, (170, 40),
                {"1": "OUT", "2": "GND"}),
        ]
    else:  # M2: insert CR-210 between SH_OUT and the OUT jack, with JP_BLR 0R bypass.
        spec += [
            ("U_BLR", "cremat:CR-210", _val("U_BLR"), FP_SIP, False, (110, 35),
                {"1": "SH_OUT", "2": "GND", "3": "GND", "4": "BLVN", "5": "BLVP",
                 "6": "GND", "7": "GND", "8": "BLR_OUT"}),
            # CR-210 per-rail decoupling
            ("R_BLP", "Device:R", _val("R_BLP"), FP_R, False, (92, 18), {"1": "+VDC", "2": "BLVP"}),
            ("C_BLPb","Device:C", _val("C_BLPb"),FP_C, False, (100, 18),{"1": "BLVP", "2": "GND"}),
            ("C_BLPh","Device:C", _val("C_BLPh"),FP_C, False, (106, 18),{"1": "BLVP", "2": "GND"}),
            ("R_BLN", "Device:R", _val("R_BLN"), FP_R, False, (92, 56), {"1": "-VDC", "2": "BLVN"}),
            ("C_BLNb","Device:C", _val("C_BLNb"),FP_C, False, (100, 56),{"1": "BLVN", "2": "GND"}),
            ("C_BLNh","Device:C", _val("C_BLNh"),FP_C, False, (106, 56),{"1": "BLVN", "2": "GND"}),
            # populate-XOR 0R bypass across the CR-210 (in<->out), DNP by default (CR-210 fitted)
            ("JP_BLR","Device:R", _val("JP_BLR"), FP_R, True, (110, 75), {"1": "SH_OUT", "2": "BLR_OUT"}),
            # output series + jack
            ("R_OUT", "Device:R", _val("R_OUT"), FP_R, False, (150, 35), {"1": "BLR_OUT", "2": "OUT"}),
            ("J_OUT", "Connector:Conn_Coaxial", _val("J_OUT"), FP_MCX, False, (170, 40),
                {"1": "OUT", "2": "GND"}),
        ]
    # ---- board-level bulk electrolytics (100uF/rail, = A6 Cbulk_p/Cbulk_n) ----
    # Polarized: pin1 = + (anode), pin2 = - (cathode). +12V rail: +on +VDC.
    # -12V rail: the more-positive node is GND, so +on GND / -on -VDC (correct polarity).
    spec += [
        ("C_BULKP", "Device:C_Polarized", _val("C_BULKP"), FP_CPELEC, False, (130, 60), {"1": "+VDC", "2": "GND"}),
        ("C_BULKN", "Device:C_Polarized", _val("C_BULKN"), FP_CPELEC, False, (145, 60), {"1": "GND", "2": "-VDC"}),
    ]
    # ---- power entry: 3-pos screw terminal ----
    # (kept at (30,95): the PWR_FLAG placement in build() is keyed to this coordinate)
    spec += [
        ("J_PWR", "Connector:Screw_Terminal_01x03", _val("J_PWR"), FP_SCREW, False, (30, 95),
            {"1": "+VDC", "2": "GND", "3": "-VDC"}),
    ]
    return spec

def prefix_of(role):
    if role.startswith("JP"): return "R"
    if role.startswith("RV"): return "RV"
    return role[0]

# ---------- emitters ----------
def prop(name, val, x, y, hide=False, rot=0):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)%s\n'
            '\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)' % (name, val, x, y, rot, h))

def sym_instance(lib_id, ref, value, fp, dnp, x, y, paths, inst_uuid, hide_val=False, extra=None):
    pn = pins_of(lib_id)
    pinlines = "\n".join('\t\t(pin "%s" (uuid "%s"))' % (p, uid(inst_uuid, "pin", p)) for p in pn)
    pathlines = "\n".join(
        '\t\t\t\t(path "%s" (reference "%s") (unit 1))' % (path, r) for path, r in paths)
    # extra = ordered list of (name, value) -> hidden BOM props (MPN/Manufacturer/Distributor PN)
    extralines = ""
    if extra:
        extralines = "\n" + "\n".join(prop(n, v, x, y, hide=True) for n, v in extra)
    return ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp %s)\n\t\t(uuid "%s")\n%s\n%s\n%s%s\n'
            '\t\t(instances\n\t\t\t(project "%s"\n%s\n\t\t\t)\n\t\t)\n\t)' % (
        lib_id, x, y, "yes" if dnp else "no", inst_uuid,
        prop("Reference", ref, x + 2, y - 2),
        prop("Value", value, x + 2, y + 2, hide=hide_val),
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
    spec = build_spec(MS)
    root = uid("shaper-root", MS)
    # assign references (per-prefix counters), stable order
    refmap = {}; cnt = {}
    for role, *_ in spec:
        pfx = prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1
        refmap[role] = "%s%d" % (pfx, cnt[pfx])
    nodes = []
    for role, lib_id, value, fp, dnp, (x, y), netmap in spec:
        x, y = G(x), G(y)
        iu = uid("sym", role)
        extra = None
        if role in PARTS:
            _v, mpn, mfr, dkpn = PARTS[role]
            extra = [("MPN", mpn), ("Manufacturer", mfr), ("Distributor PN", dkpn)]
        nodes.append(sym_instance(lib_id, refmap[role], value, fp, dnp, x, y,
                                  [("/" + root, refmap[role])], iu, extra=extra))
        pn = pins_of(lib_id)
        for p, net in netmap.items():
            px, py = pn[p]; ax, ay = G(x + px), G(y - py)
            if net in ("+VDC", "-VDC", "GND"):
                nodes.append(power_sym(net, ax, ay, "shaper:%s:%s" % (role, p)))
            else:
                nodes.append(label(net, ax, ay, "shaper"))
    # drive each rail once with a PWR_FLAG so ERC sees a source (place at the screw terminal)
    jp = pins_of("Connector:Screw_Terminal_01x03")
    fpx, fpy = pins_of("power:PWR_FLAG")["1"]
    jx, jy = G(30), G(95)
    for i, (p, net) in enumerate({"1": "+VDC", "2": "GND", "3": "-VDC"}.items(), 1):
        px, py = jp[p]; ax, ay = G(jx + px), G(jy - py)
        nodes.append(pwrflag(net, G(ax - fpx), G(ay + fpy), root, "#FLG%d" % i))
    # The module supply pins (CR-200/CR-210 +Vs/-Vs) are power_in and sit on the *filtered*
    # rail nodes (post-4.7R), which ERC can't see being driven through a passive R. Flag each
    # filtered supply node so ERC sees a power source. (Electrically: PWR_FLAG = "this net is
    # a power source"; the 4.7R/10uF/0.1uF still form the real RC filter on the board.)
    filt_nets = ["SHVP", "SHVN"] + (["BLVP", "BLVN"] if MS == "M2" else [])
    fy = G(110); fxs = G(60)
    for i, net in enumerate(filt_nets):
        ax, ay = G(fxs + i * 12), fy
        nodes.append(label(net, ax, ay, "shaper"))
        nodes.append(pwrflag(net, G(ax - fpx), G(ay + fpy), root, "#FLGF%d" % i))
    si = '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)'
    out = ('(kicad_sch\n\t(version %s)\n\t(generator "gen_sch.py")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "A4")\n'
           '\t(title_block\n\t\t(title "CR-200 shaper eval board (%s)")\n'
           '\t\t(company "Yale / Brunner Neutrino Lab")\n\t)\n%s\n%s\n%s\n\t(embedded_fonts no)\n)\n' % (
        VERSION, root, MS, lib_symbols_block(), "\n".join(nodes), si))
    with open(os.path.join(HERE, "shaper.kicad_sch"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote shaper.kicad_sch (%s): %d symbols" % (MS, len(spec)))

if __name__ == "__main__":
    build()
