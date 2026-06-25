#!/usr/bin/env python3
"""Generate the standalone CR-112 CSP eval board schematic (track A1 csp-design).

Adapted from hardware/gen_sch.py (same net-label-at-pin-coordinate method, see
docs/KICAD_WITH_CLAUDE_CODE.md). Single channel only: SiPM bias front-end ->
AC-coupling Cc -> CR-112 -> CSP_OUT, with charge-injection test input, per-rail
module decoupling per the CR-150-R5 reference (4.7R series + 10uF + 0.1uF on each
rail at the module), MCX coax I/O and a 3-pos screw terminal for +/-12V/GND.

Generic parts only (real MPNs swapped in at the A3 real-parts gate).

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_sch.py
Validate: kicad-cli sch erc csp-cr112.kicad_sch
"""
import os, re, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
CREMAT_SYM = os.path.join(HERE, "lib", "cremat.kicad_sym")
STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/symbols"
PROJ = "csp-cr112"
NS = uuid.UUID("a1b2c3d4-0001-4000-8000-000000000000")   # distinct namespace from hardware/
VERSION = "20260306"

def uid(*p): return str(uuid.uuid5(NS, ":".join(str(x) for x in p)))

def G(v): return round(round(float(v) / 1.27) * 1.27, 4)  # snap to 1.27mm connection grid

# ---------- minimal S-expression symbol-library reader ----------
def _match(text, start):
    depth, i, n = 0, start, len(text)
    in_str = False
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
    "cremat:CR-11X": (CREMAT_SYM, "CR-11X"),
    "Device:R": (f"{STOCK}/Device.kicad_sym", "R"),
    "Device:C": (f"{STOCK}/Device.kicad_sym", "C"),
    "Device:C_Polarized": (f"{STOCK}/Device.kicad_sym", "C_Polarized"),
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

# ---------- channel netlist spec ----------
# role: (lib_id, value, footprint, dnp, (x,y), {pin#: net}, mpn, mfr)
# REAL parts (A3 real-parts gate, models-bom/PARTS_REPORT.md + csp-cr112-bom.csv).
# Footprints are unchanged 0805 / SIP-8 / MCX from the generic board EXCEPT:
#   - rail bulk 10uF (Cp1/Cn1): 1206 -> 0805 (A3 0805 policy, Samsung CL21A106KAYNNNE)
#   - rail-entry bulk: was 10uF/1206 generic -> 100uF/25V radial THT (A3 Nichicon UVR1E101MED)
FP_R   = "Resistor_SMD:R_0805_2012Metric"
FP_C   = "Capacitor_SMD:C_0805_2012Metric"
FP_CPRAD = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"   # 100uF radial electrolytic rail-entry bulk
FP_SIP = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"   # CR-112 SIP-8, 2.54mm pitch (matches Cremat 8pinSIP)
FP_MCX = "cremat:MCX_CONMCX013_EdgeMount"
FP_TB  = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal"

# Layout coordinates are roughly left->right by signal flow (schematic readability only;
# PCB placement is independent). Generous spacing so labels don't collide.
CH = [
    # --- SiPM bias front-end (HV) ---
    ("J_BIAS","Connector:Conn_Coaxial","MCX CONMCX013",FP_MCX,False,(25,55), {"1":"BIAS_IN","2":"GND"}, "CONMCX013","TE/Linx"),
    ("Rf1",  "Device:R",               "10k",          FP_R, False,(45,40), {"1":"BIAS_IN","2":"N_filt"}, "RC0805FR-0710KL","Yageo"),
    ("JP_Rf1","Device:R",              "0R",           FP_R, True, (45,65), {"1":"BIAS_IN","2":"N_filt"}, "RC0805JR-070RL","Yageo"),
    ("Cf",   "Device:C",               "100nF/100V",   FP_C, False,(60,50), {"1":"N_filt","2":"GND"}, "CL21B104KCC5PNC","Samsung"),
    ("Rf2",  "Device:R",               "10k",          FP_R, False,(75,40), {"1":"N_filt","2":"FE"}, "RC0805FR-0710KL","Yageo"),
    ("JP_Rf2","Device:R",              "0R",           FP_R, True, (75,65), {"1":"N_filt","2":"FE"}, "RC0805JR-070RL","Yageo"),
    ("J_SIPM","Connector:Conn_Coaxial","MCX CONMCX013",FP_MCX,False,(90,70),{"1":"FE","2":"GND"}, "CONMCX013","TE/Linx"),
    ("Cc",   "Device:C",               "0.22uF/100V",  FP_C, False,(100,40),{"1":"FE","2":"CSP_IN"}, "GRM21AR72A224KAC5K","Murata"),
    # --- charge-injection test input (per CR-150-R5: 47R + 1pF) ---
    ("J_TEST","Connector:Conn_Coaxial","MCX CONMCX013",FP_MCX,False,(100,90),{"1":"TEST_IN","2":"GND"}, "CONMCX013","TE/Linx"),
    ("R_test","Device:R",              "47",           FP_R, False,(115,85),{"1":"TEST_IN","2":"TEST_N"}, "RC0805JR-0747RL","Yageo"),
    ("C_test","Device:C",              "1pF",          FP_C, False,(115,65),{"1":"TEST_N","2":"CSP_IN"}, "CC0805CRNPO9BN1R0","Yageo"),
    # --- CR-112 CSP module ---
    ("U_CSP","cremat:CR-11X",          "CR-112",       FP_SIP,False,(135,40),
        {"1":"CSP_IN","2":"GND","3":"NC","4":"GND","5":"-VS_F","6":"+VS_F","7":"GND","8":"CSP_OUT"}, "CR-112-R2.1","Cremat"),
    ("J_OUT","Connector:Conn_Coaxial", "MCX CONMCX013",FP_MCX,False,(165,45),{"1":"CSP_OUT","2":"GND"}, "CONMCX013","TE/Linx"),
    # --- per-rail module decoupling per CR-150-R5 (4.7R series + 10uF + 0.1uF) ---
    ("R_dvp","Device:R",               "4.7",          FP_R,   False,(125,85),{"1":"+VDC","2":"+VS_F"}, "RC0805JR-074R7L","Yageo"),
    ("Cp1",  "Device:C",               "10uF",         FP_C,   False,(135,95),{"1":"+VS_F","2":"GND"}, "CL21A106KAYNNNE","Samsung"),
    ("Cp2",  "Device:C",               "0.1uF",        FP_C,   False,(145,95),{"1":"+VS_F","2":"GND"}, "CL21B104KBCNNNC","Samsung"),
    ("R_dvn","Device:R",               "4.7",          FP_R,   False,(125,110),{"1":"-VDC","2":"-VS_F"}, "RC0805JR-074R7L","Yageo"),
    ("Cn1",  "Device:C",               "10uF",         FP_C,   False,(135,120),{"1":"-VS_F","2":"GND"}, "CL21A106KAYNNNE","Samsung"),
    ("Cn2",  "Device:C",               "0.1uF",        FP_C,   False,(145,120),{"1":"-VS_F","2":"GND"}, "CL21B104KBCNNNC","Samsung"),
    # --- board-level rail entry bulk (100uF radial electrolytic) + power entry ---
    ("Cb_p", "Device:C_Polarized",     "100uF/25V",    FP_CPRAD,False,(40,110),{"1":"+VDC","2":"GND"}, "UVR1E101MED","Nichicon"),
    ("Cb_n", "Device:C_Polarized",     "100uF/25V",    FP_CPRAD,False,(60,110),{"1":"-VDC","2":"GND"}, "UVR1E101MED","Nichicon"),
    ("J_PWR","Connector:Screw_Terminal_01x03","+Vs/GND/-Vs",FP_TB,False,(25,110),
        {"1":"+VDC","2":"GND","3":"-VDC"}, "1715035","Phoenix"),
]
def prefix_of(role):
    if role.startswith("JP"): return "R"
    if role.startswith("RV"): return "RV"
    return role[0]

# ---------- emitters ----------
def prop(name, val, x, y, hide=False, rot=0):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)%s\n'
            '\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)' % (name, val, x, y, rot, h))

def sym_instance(lib_id, ref, value, fp, dnp, x, y, paths, inst_uuid, hide_val=False, mpn="", mfr=""):
    pn = pins_of(lib_id)
    pinlines = "\n".join('\t\t(pin "%s" (uuid "%s"))' % (p, uid(inst_uuid, "pin", p)) for p in pn)
    pathlines = "\n".join(
        '\t\t\t\t(path "%s" (reference "%s") (unit 1))' % (path, r) for path, r in paths)
    extra = ""
    if mpn:
        extra += "\n" + prop("MPN", mpn, x, y, hide=True)
    if mfr:
        extra += "\n" + prop("MFN", mfr, x, y, hide=True)
    return ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp %s)\n\t\t(uuid "%s")\n%s\n%s\n%s%s\n'
            '\t\t(instances\n\t\t\t(project "%s"\n%s\n\t\t\t)\n\t\t)\n\t)' % (
        lib_id, x, y, "yes" if dnp else "no", inst_uuid,
        prop("Reference", ref, x + 2, y - 2),
        prop("Value", value, x + 2, y + 2, hide=hide_val),
        prop("Footprint", fp, x, y, hide=True), extra,
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

def emit_nodes(refmap, paths_for, key):
    nodes = []
    for role, lib_id, value, fp, dnp, (x, y), netmap, mpn, mfr in CH:
        x, y = G(x), G(y)
        iu = uid(key, "sym", role)
        nodes.append(sym_instance(lib_id, refmap[role], value, fp, dnp, x, y, paths_for(role), iu,
                                  mpn=mpn, mfr=mfr))
        pn = pins_of(lib_id)
        for p, net in netmap.items():
            px, py = pn[p]; ax, ay = G(x + px), G(y - py)
            if net == "NC":
                nodes.append('\t(no_connect (at %s %s) (uuid "%s"))' % (ax, ay, uid(key, "nc", role, p)))
                continue
            if net in ("+VDC", "-VDC", "GND"):
                nodes.append(power_sym(net, ax, ay, uid(key, role, p)))   # power symbol at pin
            else:
                nodes.append(label(net, ax, ay, key))
    return nodes

def file_wrap(uuid_root, title, body_nodes, sheet_instances):
    return ('(kicad_sch\n\t(version %s)\n\t(generator "gen_sch.py")\n\t(generator_version "10.0")\n'
            '\t(uuid "%s")\n\t(paper "A4")\n'
            '\t(title_block\n\t\t(title "%s")\n\t\t(company "Yale / Brunner Neutrino Lab")\n\t)\n'
            '%s\n%s\n%s\n\t(embedded_fonts no)\n)\n' % (
        VERSION, uuid_root, title, lib_symbols_block(),
        "\n".join(body_nodes), sheet_instances))

def build():
    root = uid("csp-root")
    refmap = {}
    cnt = {}
    for role, *_ in CH:
        pfx = prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1
        refmap[role] = "%s%d" % (pfx, cnt[pfx])
    paths_for = lambda role: [("/" + root, refmap[role])]
    nodes = emit_nodes(refmap, paths_for, "csp")
    # PWR_FLAG on each rail so ERC sees the screw-terminal-driven rails as driven.
    fx = 25
    for net in ("+VDC", "-VDC", "GND"):
        nodes.append(pwrflag(net, G(fx), G(130), root, "#FLG_%s" % net.replace("+","P").replace("-","N")))
        nodes.append(power_sym(net, G(fx), G(130), uid("flagpwr", net)))
        fx += 15.24
    # The CR-112 +Vs/-Vs power-input pins sit behind the 4.7R series decoupling resistors,
    # on the FILTERED rails +VS_F/-VS_F. ERC can't trace power-drive through a passive R, so
    # flag those nodes as driven too (a PWR_FLAG carries no net name -> attach via a local
    # label at the same coordinate, which already names the net at the cap pin).
    fy = 150
    for net in ("+VS_F", "-VS_F"):
        nx = G(160); ny = G(fy)
        nodes.append(pwrflag(net, nx, ny, root, "#FLG_%s" % net.replace("+","P").replace("-","N")))
        nodes.append(label(net, nx, ny, "csp_railflag"))
        fy += 12
    si = '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)'
    out = file_wrap(root, "CR-112 CSP eval board + SiPM bias front-end (csp-cr112)", nodes, si)
    with open(os.path.join(HERE, PROJ + ".kicad_sch"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote %s.kicad_sch (%d roles)" % (PROJ, len(CH)))

if __name__ == "__main__":
    build()
