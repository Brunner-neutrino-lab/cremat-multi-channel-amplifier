#!/usr/bin/env python3
"""Generate the multi-channel Cremat amplifier schematic from a netlist spec.

Method (see docs/KICAD_WITH_CLAUDE_CODE.md): place every symbol at rotation 0 and
connect pins by dropping a net label (signal) or a power symbol (power rail) at the
*exact* pin coordinate -- no routed wires. Connectivity is by net name + coincident
pins; ERC (pin_not_connected / label_dangling as errors) proves it. UUIDs are
deterministic (uuid5) so re-runs reproduce the file.

Outputs:
  hardware/channel.kicad_sch                       one channel (standalone, self-driven)
  hardware/multi-channel-cremat-amplifier.kicad_sch root, 12x channel + power

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/gen_sch.py   (or system python)
Validate: kicad-cli sch erc / sch export netlist
"""
import os, re, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
CREMAT_SYM = os.path.join(HERE, "lib", "cremat.kicad_sym")
STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/symbols"
PROJ = "multi-channel-cremat-amplifier"
NS = uuid.UUID("a1b2c3d4-0000-4000-8000-000000000000")
VERSION = "20260306"

def uid(*p): return str(uuid.uuid5(NS, ":".join(str(x) for x in p)))

def G(v): return round(round(float(v) / 1.27) * 1.27, 4)  # snap to 1.27mm connection grid

# ---------- minimal S-expression symbol-library reader ----------
def _match(text, start):
    """Return end index just past the ')' matching the '(' at `start`."""
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
    """Raw '(symbol "name" ...)' block, with top name kept (caller renames)."""
    m = re.search(r'\(symbol\s+"%s"' % re.escape(name), libtext)
    if not m: raise KeyError(name)
    return libtext[m.start():_match(libtext, m.start())]

def pin_coords(block):
    """{pin_number: (x, y)} connection points, lib coords (Y-up), rotation 0."""
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

# symbol source: lib_id -> (file, name_in_file)
SYMSRC = {
    "cremat:CR-11X": (CREMAT_SYM, "CR-11X"),
    "cremat:CR-200": (CREMAT_SYM, "CR-200"),
    "cremat:CR-210": (CREMAT_SYM, "CR-210"),
    "cremat:EL5167": (CREMAT_SYM, "EL5167"),
    "Device:R": (f"{STOCK}/Device.kicad_sym", "R"),
    "Device:C": (f"{STOCK}/Device.kicad_sym", "C"),
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

# ---------- channel netlist spec ----------
# role: (lib_id, value, footprint, dnp, (x,y), {pin#: net})
# net "+VDC"/"-VDC"/"GND" -> power symbol; anything else -> local label.
FP_R = "Resistor_SMD:R_0805_2012Metric"
FP_C = "Capacitor_SMD:C_0805_2012Metric"
FP_SIP = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
FP_OP = "Package_TO_SOT_SMD:SOT-23-5"
FP_TRIM = "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical"
FP_MCX = "cremat:MCX_CONMCX013_EdgeMount"

CH = [
    # role        lib_id                  value         fp      dnp    pos       pins
    ("J_BIAS","Connector:Conn_Coaxial","MCX CONMCX013",FP_MCX,False,(30,40), {"1":"BIAS_IN","2":"GND"}),
    ("Rf1",  "Device:R",               "10k",          FP_R, False,(50,30), {"1":"BIAS_IN","2":"N_filt"}),
    ("JP_Rf1","Device:R",              "0R",           FP_R, True, (50,50), {"1":"BIAS_IN","2":"N_filt"}),
    ("Cf",   "Device:C",               "100nF/100V",   FP_C, False,(65,40), {"1":"N_filt","2":"GND"}),
    ("Rf2",  "Device:R",               "10k",          FP_R, False,(80,30), {"1":"N_filt","2":"FE"}),
    ("JP_Rf2","Device:R",              "0R",           FP_R, True, (80,50), {"1":"N_filt","2":"FE"}),
    ("J_SIPM","Connector:Conn_Coaxial","MCX CONMCX013",FP_MCX,False,(95,55),{"1":"FE","2":"GND"}),
    ("Cc",   "Device:C",               "0.22uF/100V",  FP_C, False,(100,30),{"1":"FE","2":"CSP_IN"}),
    ("U_CSP","cremat:CR-11X",          "CR-112",       FP_SIP,False,(120,35),
        {"1":"CSP_IN","2":"GND","3":"NC","4":"GND","5":"-VDC","6":"+VDC","7":"GND","8":"CSP_OUT"}),
    ("U_SHAPER","cremat:CR-200",       "CR-200-1us",   FP_SIP,False,(150,35),
        {"1":"CSP_OUT","2":"PZ","3":"GND","4":"-VDC","5":"+VDC","6":"GND","7":"GND","8":"SH_OUT"}),
    ("RV_PZ","Device:R_Potentiometer_Trim_US","100k",  FP_TRIM,False,(150,70),
        {"1":"SH_OUT","2":"PZ","3":"PZ"}),
    ("U_BLR","cremat:CR-210",          "CR-210",       FP_SIP,False,(180,35),
        {"1":"SH_OUT","2":"GND","3":"GND","4":"-VDC","5":"+VDC","6":"GND","7":"GND","8":"BLR_OUT"}),
    ("JP_BLR","Device:R",              "0R",           FP_R, True, (180,75),{"1":"SH_OUT","2":"BLR_OUT"}),
    ("U_BUF","cremat:EL5167",          "EL5167",       FP_OP,False,(210,40),
        {"3":"BLR_OUT","4":"BUF_OUT","1":"BUF_OUT","5":"+VDC","2":"-VDC"}),
    ("R_OUT","Device:R",               "49.9",         FP_R, False,(230,40),{"1":"BUF_OUT","2":"OUT"}),
    ("J_OUT","Connector:Conn_Coaxial", "MCX CONMCX013",FP_MCX,False,(245,40),{"1":"OUT","2":"GND"}),
    # per-channel decoupling (representative; full set in GUI)
    ("C_dvp","Device:C",               "100nF",        FP_C, False,(125,80),{"1":"+VDC","2":"GND"}),
    ("C_dvn","Device:C",               "100nF",        FP_C, False,(140,80),{"1":"-VDC","2":"GND"}),
]
REFPREFIX = {"J":"J","R":"R","C":"C","U":"U","RV":"RV","JP":"R"}
def prefix_of(role):
    if role.startswith("JP"): return "R"
    if role.startswith("RV"): return "RV"
    return role[0]

# ---------- emitters ----------
def prop(name, val, x, y, hide=False, rot=0):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)%s\n'
            '\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)' % (name, val, x, y, rot, h))

def sym_instance(lib_id, ref, value, fp, dnp, x, y, paths, inst_uuid, hide_val=False):
    pn = pins_of(lib_id)
    pinlines = "\n".join('\t\t(pin "%s" (uuid "%s"))' % (p, uid(inst_uuid, "pin", p)) for p in pn)
    pathlines = "\n".join(
        '\t\t\t\t(path "%s" (reference "%s") (unit 1))' % (path, r) for path, r in paths)
    return ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp %s)\n\t\t(uuid "%s")\n%s\n%s\n%s\n'
            '\t\t(instances\n\t\t\t(project "%s"\n%s\n\t\t\t)\n\t\t)\n\t)' % (
        lib_id, x, y, "yes" if dnp else "no", inst_uuid,
        prop("Reference", ref, x + 2, y - 2),
        prop("Value", value, x + 2, y + 2, hide=hide_val),
        prop("Footprint", fp, x, y, hide=True),
        PROJ, pathlines))

def label(net, x, y, key):
    return ('\t(label "%s"\n\t\t(at %s %s 0)\n\t\t(effects (font (size 1.27 1.27)) (justify left bottom))\n'
            '\t\t(uuid "%s")\n\t)' % (net, x, y, uid(key, "label", net, x, y)))

def global_label(net, x, y, key):
    return ('\t(global_label "%s"\n\t\t(shape input)\n\t\t(at %s %s 0)\n'
            '\t\t(effects (font (size 1.27 1.27)) (justify left))\n\t\t(uuid "%s")\n\t)' % (
        net, x, y, uid(key, "glabel", net, x, y)))

def power_sym(net, x, y, key):
    iu = uid(key, "pwr", net, x, y)
    paths = [("/" + key, "#PWR?")]
    # power symbols: single pin, ref #PWR, value = net name
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

def emit_channel_nodes(refmap, paths_for, key):
    """Emit all component instances + labels/power symbols for one channel layout.
    refmap: role -> reference (for single-instance) ; paths_for(role) -> [(path,ref)..]
    """
    nodes = []
    powerpts = {"+VDC": [], "-VDC": [], "GND": []}
    for role, lib_id, value, fp, dnp, (x, y), netmap in CH:
        x, y = G(x), G(y)
        iu = uid(key, "sym", role)
        nodes.append(sym_instance(lib_id, refmap[role], value, fp, dnp, x, y,
                                  paths_for(role), iu))
        pn = pins_of(lib_id)
        for p, net in netmap.items():
            if net == "NC":
                px, py = pn[p]; ax, ay = G(x + px), G(y - py)
                nodes.append('\t(no_connect (at %s %s) (uuid "%s"))' % (ax, ay, uid(key, "nc", role, p)))
                continue
            px, py = pn[p]; ax, ay = G(x + px), G(y - py)
            if net in powerpts:
                nodes.append(global_label(net, ax, ay, key))   # global: connects across all 12 sheets
            else:
                nodes.append(label(net, ax, ay, key))          # local: per-channel-instance net
    return nodes

def file_wrap(uuid_root, title, body_nodes, sheet_instances):
    return ('(kicad_sch\n\t(version %s)\n\t(generator "gen_sch.py")\n\t(generator_version "10.0")\n'
            '\t(uuid "%s")\n\t(paper "A3")\n'
            '\t(title_block\n\t\t(title "%s")\n\t\t(company "Yale / Brunner Neutrino Lab")\n\t)\n'
            '%s\n%s\n%s\n\t(embedded_fonts no)\n)\n' % (
        VERSION, uuid_root, title, lib_symbols_block(),
        "\n".join(body_nodes), sheet_instances))

# ---------- build standalone channel ----------
def build_channel_standalone():
    root = uid("channel-root")
    refmap = {}
    cnt = {}
    for role, *_ in CH:
        pfx = prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1
        refmap[role] = "%s%d" % (pfx, cnt[pfx])
    paths_for = lambda role: [("/" + root, refmap[role])]
    nodes = emit_channel_nodes(refmap, paths_for, "ch0")
    # add one (power sym + PWR_FLAG) per rail to self-drive ERC
    fx = 30
    for net in ("+VDC", "-VDC", "GND"):
        nodes.append(power_sym(net, G(fx), G(95), "ch0"))
        nodes.append(pwrflag(net, G(fx), G(95), "ch0"))
        fx += 15.24
    si = '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)'
    out = file_wrap(root, "Cremat amplifier channel (1 of 12)", nodes, si)
    with open(os.path.join(HERE, "channel.kicad_sch"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote channel.kicad_sch")

def emit_sheet(n, x, y, suid, root_uuid):
    x, y = G(x), G(y)
    return ('\t(sheet\n\t\t(at %s %s)\n\t\t(size 40 24)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n'
            '\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n'
            '\t\t(stroke (width 0.1524) (type solid))\n\t\t(fill (color 0 0 0 0.0000))\n\t\t(uuid "%s")\n'
            '\t\t(property "Sheetname" "ch%d" (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left bottom)))\n'
            '\t\t(property "Sheetfile" "channel.kicad_sch" (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left top)))\n'
            '\t\t(instances (project "%s" (path "/%s" (page "%d"))))\n\t)' % (
        x, y, suid, n, x, y - 1, x, y + 25, PROJ, root_uuid, n + 1))

def build_all():
    """Generate channel.kicad_sch (sub-sheet, 12 instances) + the 12-channel root."""
    ROOT = uid("root"); CHFILE = uid("channelfile")
    sheets = [uid("sheetinst", n) for n in range(1, 13)]
    # per-channel reference maps (globally-unique refs)
    cnt = {}; refmaps = []
    for n in range(12):
        rm = {}
        for role, *_ in CH:
            pfx = prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1; rm[role] = "%s%d" % (pfx, cnt[pfx])
        refmaps.append(rm)
    paths_for = lambda role: [("/%s/%s" % (ROOT, sheets[n]), refmaps[n][role]) for n in range(12)]
    # --- channel sub-sheet (12-path instances, global labels for rails) ---
    nodes = emit_channel_nodes(refmaps[0], paths_for, "ch")
    with open(os.path.join(HERE, "channel.kicad_sch"), "w", encoding="utf-8") as f:
        f.write(file_wrap(CHFILE, "Cremat amplifier channel (x12)", nodes, ""))
    # --- root ---
    rnodes = []
    for n in range(12):
        rnodes.append(emit_sheet(n + 1, 30 + (n % 4) * 55, 30 + (n // 4) * 45, sheets[n], ROOT))
    # power entry: J_PWR screw terminal + global labels + PWR_FLAG driving each rail
    jx, jy = G(40), G(180)
    jiu = uid("root", "jpwr")
    rnodes.append(sym_instance("Connector:Screw_Terminal_01x03", "J_PWR", "+Vs/-Vs/GND",
                  "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm",
                  False, jx, jy, [("/" + ROOT, "J_PWR")], jiu))
    jp = pins_of("Connector:Screw_Terminal_01x03")
    fpx, fpy = pins_of("power:PWR_FLAG")["1"]          # flag pin offset (lib coords)
    rails = {"1": "+VDC", "2": "GND", "3": "-VDC"}
    for i, (p, net) in enumerate(rails.items(), 1):
        px, py = jp[p]; ax, ay = G(jx + px), G(jy - py)   # J_PWR pin coordinate
        rnodes.append(global_label(net, ax, ay, "root"))
        # place PWR_FLAG so its pin lands exactly on (ax, ay) -> drives the rail
        rnodes.append(pwrflag(net, G(ax - fpx), G(ay + fpy), ROOT, "#FLG%d" % i))
    si = '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)'
    with open(os.path.join(HERE, PROJ + ".kicad_sch"), "w", encoding="utf-8") as f:
        f.write(file_wrap(ROOT, "Multi-channel Cremat amplifier (12 channel)", rnodes, si))
    print("wrote channel.kicad_sch + %s.kicad_sch (12x)" % PROJ)

if __name__ == "__main__":
    build_all()
