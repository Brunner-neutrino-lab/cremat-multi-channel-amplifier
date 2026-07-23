#!/usr/bin/env python3
"""Generate the single-channel board schematic (Phase B, track B1 chan-design).

Merges the two PROVEN Phase-A sub-components AS-IS and appends the output buffer:

  BIAS_IN/SIPM -> [csp-cr112 front-end + CR-112] --CSP_OUT--> [CR-200 + CR-210 shaper]
      --SHAPER_OUT--> [THS3491 CFA buffer, Av=+2] --49.9R--> OUT_50 (MCX, 50ohm back-term)

REVIEW LAYOUT (2026-07): this schematic is drawn for HUMAN REVIEW. Every part is placed
on a left->right signal spine with generous spacing (no overlaps), the signal path is
WIRED pin-to-pin, per-rail decoupling lives in a top (+rail) / bottom (-rail) band, and
power is distributed with power symbols + net labels the way an engineer would draw it.

DESIGN NOTES (2026-07, requested changes on top of the redraw):
  * Test input is a coax-terminated charge injector: J_TEST -> TEST_IN, R_test = shunt
    termination to GND, C_test couples TEST_IN straight into CSP_IN (R_test is NOT in series).
  * The output buffer is a POPULATE-OR-BYPASS block: JP_BUF (0R, SHAPER_OUT->BUF_OUT) XOR the
    THS3491 buffer. Default build = buffer DNP + JP_BUF fitted (shaper drives the 49.9 back-term
    directly). Populate the buffer (U_BUF/R_FB/R_GAIN + BVP/BVN decoupling) and remove JP_BUF for
    the +2 gain stage. R_BSER (49.9), J_OUT50 and JP_BUF stay fitted in both variants.
  * Rail protection = REVERSE-POLARITY block + fault interrupt (per rail): screw terminal ->
    resettable PTC (F_P/F_N, 100 mA hold) -> series Schottky (D_RP/D_RN, SS14, 40 V/1 A) -> board
    rail. The Schottky blocks a reversed supply (cathode-to-rail on +12, anode-to-rail on -12);
    the PTC interrupts a sustained fault. NO shunt over-voltage clamp: the Cremat modules'
    +/-13 V supply abs-max vs the +/-12 V nominal rail leaves no window for a passive clamp that
    both stays off at 12 V and holds below 13 V (verified vs CR-112/CR-200/CR-210 + THS3491
    datasheets), so over-voltage is an operational limit, not a clamp. New internal nets
    +VDC_F / -VDC_F sit between each PTC and its Schottky.

Method: place each symbol at a chosen (x, y, rotation); compute transformed pin
coordinates with a validated CCW transform (schematic Y-down); draw orthogonal wires
between pins; drop net labels on signal wires, power symbols on rails, no-connects on
NC pins. Deterministic uuid5 UUIDs so re-runs reproduce the file.

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_sch.py
Validate: kicad-cli sch erc channel.kicad_sch ; kicad-cli sch export netlist ...
"""
import os, re, uuid, math

HERE = os.path.dirname(os.path.abspath(__file__))
CREMAT_SYM = os.path.join(HERE, "lib", "cremat.kicad_sym")
STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/symbols"
PROJ = "channel"
NS = uuid.UUID("b1c2d3e4-0000-4000-8000-000000000000")   # B1-namespaced (distinct from A1/A4)
VERSION = "20250610"      # real KiCad-10 schematic format (the fictitious "20260306" made KiCad's GUI
                          # treat the file as newer-than-itself and load it degraded -> phantom parity fails)

def uid(*p): return str(uuid.uuid5(NS, ":".join(str(x) for x in p)))
def G(v): return round(round(float(v) / 1.27) * 1.27, 4)  # snap to 1.27mm connection grid

# ---------- minimal S-expression symbol-library reader (same as Phase-A scripts) ----------
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
    "cremat:CR-11X": (CREMAT_SYM, "CR-11X"),
    "cremat:CR-200": (CREMAT_SYM, "CR-200"),
    "cremat:CR-210": (CREMAT_SYM, "CR-210"),
    "cremat:THS3491xDDA": (CREMAT_SYM, "THS3491xDDA"),   # TI HV CFA output buffer (SOIC-8 PowerPAD)
    "Device:R": (f"{STOCK}/Device.kicad_sym", "R"),
    "Device:C": (f"{STOCK}/Device.kicad_sym", "C"),
    "Device:C_Polarized": (f"{STOCK}/Device.kicad_sym", "C_Polarized"),
    "Device:R_Potentiometer_Trim_US": (f"{STOCK}/Device.kicad_sym", "R_Potentiometer_Trim_US"),
    "Device:D_Schottky": (f"{STOCK}/Device.kicad_sym", "D_Schottky"),
    "Device:Polyfuse_Small": (f"{STOCK}/Device.kicad_sym", "Polyfuse_Small"),
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

def indent(s, n):
    pad = "\t" * n
    return "\n".join(pad + ln if ln else ln for ln in s.splitlines())

def lib_symbols_block():
    parts = []
    for lib_id, (f, nm) in SYMSRC.items():
        raw = extract_symbol(lib_text(f), nm)
        raw = raw.replace('(symbol "%s"' % nm, '(symbol "%s"' % lib_id, 1)
        parts.append(raw)
    body = "\n".join(indent(p, 2) for p in parts)
    return "\t(lib_symbols\n%s\n\t)" % body

# ---------- footprints ----------
FP_R     = "Resistor_SMD:R_0805_2012Metric"
FP_C     = "Capacitor_SMD:C_0805_2012Metric"
FP_CPELEC= "Capacitor_SMD:CP_Elec_6.3x7.7"
FP_SIP   = "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical"  # SIP-8 socket strip: solder the
                                                                         # socket, plug the Cremat module in
                                                                         # (pads+courtyard identical to the
                                                                         # PinHeader_1x08 it replaces)
FP_TRIM  = "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical"
FP_MCX   = "cremat:MCX_CONMCX013-T"   # Linx CONMCX013-T edge-mount jack (user-downloaded footprint)
FP_SCREW = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal"
FP_SOIC8EP = "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm"
FP_SCH     = "Diode_SMD:D_SMA"                  # SS14 40V 1A Schottky reverse-block (DO-214AC / SMA)
FP_PTC     = "Fuse:Fuse_1206_3216Metric"        # Littelfuse 1206L010/60WR resettable PTC (100mA hold, 60V)

# ---------- real-part metadata (from the two COMPLETE Phase-A INTERFACEs; buffer = THS3491) ----------
# (Value, MPN, Manufacturer, DigiKey_PN). Value strings aligned to the B3 single-channel BOM.
PARTS = {
    "Cf":     ("100nF 100V X7R",      "CL21B104KCFNNNE",   "Samsung Electro-Mechanics", "1276-6840-1-ND"),
    "Cc":     ("0.22uF 100V X7R",     "C0805C224K1RACTU",  "KEMET",                     "399-C0805C224K1RACTUCT-ND"),  # was Murata GRM21AR72A224KAC5K (DK 0-stock 2026-07); equal-spec 100V X7R
    "C_test": ("1pF 50V C0G",         "CC0805CRNPO9BN1R0", "Yageo",                     "311-1089-1-ND"),
    "Rf1":    ("10k",                 "RC0805FR-0710KL",   "Yageo",                     "311-10.0KCRCT-ND"),
    "Rf2":    ("10k",                 "RC0805FR-0710KL",   "Yageo",                     "311-10.0KCRCT-ND"),
    "JP_Rf1": ("0R",                  "RC0805JR-070RL",    "Yageo",                     "311-0.0ARCT-ND"),
    "JP_Rf2": ("0R",                  "RC0805JR-070RL",    "Yageo",                     "311-0.0ARCT-ND"),
    "R_test": ("47",                  "RC0805JR-0747RL",   "Yageo",                     "311-47ARCT-ND"),
    "R_dvp":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_dvn":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "Cp1":    ("10uF 25V X5R",        "C0805C106K3PACTU",  "KEMET",                     "399-11939-1-ND"),
    "Cn1":    ("10uF 25V X5R",        "C0805C106K3PACTU",  "KEMET",                     "399-11939-1-ND"),
    "U_CSP":  ("CR-112",              "CR-112-R2.1",       "Cremat Inc",                "N/A (Cremat-direct)"),
    "U_SH":   ("CR-200-1us",          "CR-200-1us-R2.1",   "Cremat Inc",                "N/A (Cremat-direct)"),
    "U_BLR":  ("CR-210",              "CR-210-R0",         "Cremat Inc",                "N/A (Cremat-direct)"),
    "RV_PZ":  ("200k",                "3296W-1-204LF",     "Bourns",                    "3296W-204LF-ND"),
    "R_SHP":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_SHN":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_BLP":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_BLN":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "JP_BLR": ("0R",                  "RC0805JR-070RL",    "Yageo",                     "311-0.0ARCT-ND"),
    "C_SHPb": ("10uF 25V X5R",        "C0805C106K3PACTU",  "KEMET",                     "399-11939-1-ND"),
    "C_SHNb": ("10uF 25V X5R",        "C0805C106K3PACTU",  "KEMET",                     "399-11939-1-ND"),
    "C_BLPb": ("10uF 25V X5R",        "C0805C106K3PACTU",  "KEMET",                     "399-11939-1-ND"),
    "C_BLNb": ("10uF 25V X5R",        "C0805C106K3PACTU",  "KEMET",                     "399-11939-1-ND"),
    "C_BULKP":("100uF 35V",           "UWT1V101MCL1GS",    "Nichicon",                  "493-2203-1-ND"),
    "C_BULKN":("100uF 35V",           "UWT1V101MCL1GS",    "Nichicon",                  "493-2203-1-ND"),
    "U_BUF":  ("THS3491",             "THS3491IDDAT",      "Texas Instruments",         "296-49085-1-ND"),  # -1 = cut tape; -2 is a 250-pc reel
    "R_FB":   ("976",                 "RC0805FR-07976RL",  "Yageo",                     "311-976CRCT-ND"),
    "R_GAIN": ("976",                 "RC0805FR-07976RL",  "Yageo",                     "311-976CRCT-ND"),
    "R_BSER": ("49.9",                "RC0805FR-0749R9L",  "Yageo",                     "311-49.9CRCT-ND"),
    "JP_BUF": ("0R",                  "RC0805JR-070RL",    "Yageo",                     "311-0.0ARCT-ND"),
    # rail reverse-polarity protection + fault interrupt (per rail): PTC fuse + series Schottky
    "F_P":   ("PTC 0.1A",             "1206L010/60WR",     "Littelfuse",                "F8130CT-ND"),
    "D_RP":  ("SS14",                 "SS14",              "onsemi",                    "SS14CT-ND"),
    "F_N":   ("PTC 0.1A",             "1206L010/60WR",     "Littelfuse",                "F8130CT-ND"),
    "D_RN":  ("SS14",                 "SS14",              "onsemi",                    "SS14CT-ND"),
    "R_BVP":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_BVN":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "C_BVPb": ("10uF 25V X5R",        "C0805C106K3PACTU",  "KEMET",                     "399-11939-1-ND"),
    "C_BVNb": ("10uF 25V X5R",        "C0805C106K3PACTU",  "KEMET",                     "399-11939-1-ND"),
    "J_BIAS": ("MCX edge jack 50R",   "CONMCX013",         "TE Connectivity / Linx",    "343-CONMCX013-ND"),
    "J_SIPM": ("MCX edge jack 50R",   "CONMCX013",         "TE Connectivity / Linx",    "343-CONMCX013-ND"),
    "J_TEST": ("MCX edge jack 50R",   "CONMCX013",         "TE Connectivity / Linx",    "343-CONMCX013-ND"),
    "J_OUT50":("MCX edge jack 50R",   "CONMCX013",         "TE Connectivity / Linx",    "343-CONMCX013-ND"),
    "J_PWR":  ("Screw terminal 3-pos 5.08mm", "1715734",   "Phoenix Contact",           "277-1264-ND"),
}
def _val(role): return PARTS[role][0] if role in PARTS else role

# =====================================================================================
#  Component spec:  role -> (lib_id, footprint, dnp, {pin#: net}, (x, y, rotation))
#  ROLES (below) fixes the reference-designator order (per-prefix counters) so refs are
#  unchanged from the committed netlist.  Net names match the baseline oracle exactly.
# =====================================================================================
SPEC = {
    # ---- bias front-end + inputs (left) ------------------------------------------------
    "J_BIAS": ("Connector:Conn_Coaxial", FP_MCX, False, {"1":"BIAS_IN","2":"GND"},   (46.99,115.57,180)),
    "Rf1":    ("Device:R",               FP_R,   False, {"1":"BIAS_IN","2":"N_filt"},(60.96,115.57, 90)),
    "JP_Rf1": ("Device:R",               FP_R,   True,  {"1":"BIAS_IN","2":"N_filt"},(60.96,101.60, 90)),
    "Cf":     ("Device:C",               FP_C,   False, {"1":"N_filt","2":"GND"},    (69.85,119.38,  0)),
    "Rf2":    ("Device:R",               FP_R,   False, {"1":"N_filt","2":"FE"},     (78.74,115.57, 90)),
    "JP_Rf2": ("Device:R",               FP_R,   True,  {"1":"N_filt","2":"FE"},     (78.74,101.60, 90)),
    "J_SIPM": ("Connector:Conn_Coaxial", FP_MCX, False, {"1":"FE","2":"GND"},        (86.36,104.14, 90)),
    "Cc":     ("Device:C",               FP_C,   False, {"1":"FE","2":"CSP_IN"},     (93.98,115.57, 90)),
    "J_TEST": ("Connector:Conn_Coaxial", FP_MCX, False, {"1":"TEST_IN","2":"GND"},   (58.42,140.97,180)),
    "R_test": ("Device:R",               FP_R,   False, {"1":"TEST_IN","2":"GND"},   (76.20,144.78,  0)),
    "C_test": ("Device:C",               FP_C,   False, {"1":"TEST_IN","2":"CSP_IN"},(93.98,140.97, 90)),
    # ---- CR-112 CSP --------------------------------------------------------------------
    "U_CSP":  ("cremat:CR-11X", FP_SIP, False,
               {"1":"CSP_IN","2":"GND","3":"NC","4":"GND","5":"-VS_F","6":"+VS_F","7":"GND","8":"CSP_OUT"},
               (120.65,120.65,0)),
    "R_dvp":  ("Device:R", FP_R, False, {"1":"+VDC","2":"+VS_F"}, (120.65, 59.69,0)),
    "Cp1":    ("Device:C", FP_C, False, {"1":"+VS_F","2":"GND"},  (128.27, 67.31,0)),
    "R_dvn":  ("Device:R", FP_R, False, {"1":"-VDC","2":"-VS_F"}, (120.65,173.99,0)),
    "Cn1":    ("Device:C", FP_C, False, {"1":"-VS_F","2":"GND"},  (128.27,181.61,0)),
    # ---- CR-200 shaper -----------------------------------------------------------------
    "U_SH":   ("cremat:CR-200", FP_SIP, False,
               {"1":"CSP_OUT","2":"PZ","3":"GND","4":"SHVN","5":"SHVP","6":"GND","7":"GND","8":"SH_OUT"},
               (185.42,120.65,0)),
    "RV_PZ":  ("Device:R_Potentiometer_Trim_US", FP_TRIM, False,
               {"1":"CSP_OUT","2":"PZ","3":"PZ"}, (168.91,138.43,0)),
    "R_SHP":  ("Device:R", FP_R, False, {"1":"+VDC","2":"SHVP"}, (185.42, 59.69,0)),
    "C_SHPb": ("Device:C", FP_C, False, {"1":"SHVP","2":"GND"},  (193.04, 67.31,0)),
    "R_SHN":  ("Device:R", FP_R, False, {"1":"-VDC","2":"SHVN"}, (185.42,173.99,0)),
    "C_SHNb": ("Device:C", FP_C, False, {"1":"SHVN","2":"GND"},  (193.04,181.61,0)),
    # ---- CR-210 baseline restorer ------------------------------------------------------
    "U_BLR":  ("cremat:CR-210", FP_SIP, False,
               {"1":"SH_OUT","2":"GND","3":"GND","4":"BLVN","5":"BLVP","6":"GND","7":"GND","8":"SHAPER_OUT"},
               (250.19,120.65,0)),
    "R_BLP":  ("Device:R", FP_R, False, {"1":"+VDC","2":"BLVP"}, (250.19, 59.69,0)),
    "C_BLPb": ("Device:C", FP_C, False, {"1":"BLVP","2":"GND"},  (257.81, 67.31,0)),
    "R_BLN":  ("Device:R", FP_R, False, {"1":"-VDC","2":"BLVN"}, (250.19,173.99,0)),
    "C_BLNb": ("Device:C", FP_C, False, {"1":"BLVN","2":"GND"},  (257.81,181.61,0)),
    "JP_BLR": ("Device:R", FP_R, True,  {"1":"SH_OUT","2":"SHAPER_OUT"}, (250.19,140.97,90)),
    # ---- board bulk electrolytics (power entry) ----------------------------------------
    "C_BULKP":("Device:C_Polarized", FP_CPELEC, False, {"1":"+VDC","2":"GND"},  (111.76,199.39,  0)),
    "C_BULKN":("Device:C_Polarized", FP_CPELEC, False, {"1":"GND","2":"-VDC"},  (111.76,223.52,180)),
    # ---- THS3491 output buffer ---------------------------------------------------------
    "U_BUF":  ("cremat:THS3491xDDA", FP_SOIC8EP, True,
               {"1":"GND","2":"BUF_FB","3":"SHAPER_OUT","4":"BVN","5":"NC","6":"BUF_OUT","7":"BVP","8":"BVP","9":"BVN"},
               (317.5,115.57,0)),
    "R_FB":   ("Device:R", FP_R, True, {"1":"BUF_OUT","2":"BUF_FB"}, (314.96,100.33,270)),
    "R_GAIN": ("Device:R", FP_R, True, {"1":"BUF_FB","2":"GND"},     (299.72,121.92,  0)),
    "R_BSER": ("Device:R", FP_R, False, {"1":"BUF_OUT","2":"OUT_50"}, (337.82,115.57, 90)),
    "J_OUT50":("Connector:Conn_Coaxial", FP_MCX, False, {"1":"OUT_50","2":"GND"}, (355.60,115.57,0)),
    # buffer-bypass 0R: populate to skip the (DNP-by-default) buffer, feeding SHAPER_OUT straight
    # to the 49.9 back-term. XOR with the buffer block (exactly one path populated).
    "JP_BUF": ("Device:R", FP_R, False, {"1":"SHAPER_OUT","2":"BUF_OUT"}, (311.15,135.89,90)),
    "R_BVP":  ("Device:R", FP_R, True, {"1":"+VDC","2":"BVP"}, (312.42, 59.69,0)),
    "C_BVPb": ("Device:C", FP_C, True, {"1":"BVP","2":"GND"},  (320.04, 67.31,0)),
    "R_BVN":  ("Device:R", FP_R, True, {"1":"-VDC","2":"BVN"}, (312.42,173.99,0)),
    "C_BVNb": ("Device:C", FP_C, True, {"1":"BVN","2":"GND"},  (320.04,181.61,0)),
    # ---- rail protection: connector IN -> PTC fuse -> series Schottky reverse-block -> board rail ----
    "F_P":    ("Device:Polyfuse_Small", FP_PTC, False, {"1":"+VDC_IN","2":"+VDC_F"}, ( 66.04,195.58, 90)),
    "D_RP":   ("Device:D_Schottky",     FP_SCH, False, {"1":"+VDC","2":"+VDC_F"},    ( 88.90,195.58,180)),
    "F_N":    ("Device:Polyfuse_Small", FP_PTC, False, {"1":"-VDC_IN","2":"-VDC_F"}, ( 66.04,219.71, 90)),
    "D_RN":   ("Device:D_Schottky",     FP_SCH, False, {"1":"-VDC_F","2":"-VDC"},    ( 88.90,219.71,  0)),
    # ---- power entry -------------------------------------------------------------------
    "J_PWR":  ("Connector:Screw_Terminal_01x03", FP_SCREW, False,
               {"1":"+VDC_IN","2":"GND","3":"-VDC_IN"}, (48.26,207.01,0)),
}
# --- keep component pins OFF the rails -------------------------------------------------
# A pin sitting mid-way along a straight wire is only connected via a junction dot: KiCad
# accepts it (ERC/netlist agree) but it is ambiguous -- dragging the part does not stretch
# anything and the pin draws its own "endpoint" circle, which reads as unconnected. Shift the
# rail decoupling R's UP and their caps DOWN one grid step so each pin TERMINATES its own
# perpendicular stub and the junction lands on the rail (wire-to-wire), never on a pin.
for _r in ("R_dvp", "R_dvn", "R_SHP", "R_SHN", "R_BLP", "R_BLN", "R_BVP", "R_BVN"):
    _l, _f, _d, _n, (_x, _y, _o) = SPEC[_r]; SPEC[_r] = (_l, _f, _d, _n, (_x, _y - 2.54, _o))
for _c in ("Cp1", "Cn1", "C_SHPb", "C_SHNb", "C_BLPb", "C_BLNb", "C_BVPb", "C_BVNb", "Cf"):
    _l, _f, _d, _n, (_x, _y, _o) = SPEC[_c]; SPEC[_c] = (_l, _f, _d, _n, (_x, _y + 2.54, _o))
_l, _f, _d, _n, (_x, _y, _o) = SPEC["R_test"]                      # same for the TEST_IN shunt
SPEC["R_test"] = (_l, _f, _d, _n, (_x, _y + 2.54, _o))

# reference-designator order (fixes U1..U4, R1.., C1.., J1.., RV1 exactly as the baseline)
ROLES = ["J_BIAS","Rf1","JP_Rf1","Cf","Rf2","JP_Rf2","J_SIPM","Cc","J_TEST","R_test","C_test",
         "U_CSP","R_dvp","Cp1","R_dvn","Cn1",
         "U_SH","RV_PZ","R_SHP","C_SHPb","R_SHN","C_SHNb",
         "U_BLR","R_BLP","C_BLPb","R_BLN","C_BLNb","JP_BLR","C_BULKP","C_BULKN",
         "U_BUF","R_FB","R_GAIN","R_BSER","J_OUT50","R_BVP","C_BVPb","R_BVN","C_BVNb",
         "JP_BUF",
         "F_P","D_RP","F_N","D_RN",
         "J_PWR"]

def prefix_of(role):
    if role.startswith("JP"): return "R"
    if role.startswith("RV"): return "RV"
    if role.startswith("U_"): return "U"
    if role.startswith("J_"): return "J"
    return role[0]

# ---------- geometry: validated CCW pin transform (schematic Y-down) ------------------
def pinpt(role, num):
    lib_id, _fp, _dnp, _nm, (x, y, rot) = SPEC[role]
    px, py = pins_of(lib_id)[num]
    a = math.radians(rot)
    rx = px * math.cos(a) - py * math.sin(a)
    ry = px * math.sin(a) + py * math.cos(a)
    return (G(G(x) + rx), G(G(y) - ry))

# ---------- emitters ------------------------------------------------------------------
def prop(name, val, x, y, hide=False, rot=0, size=1.27, just=None):
    h = "\n\t\t\t(hide yes)" if hide else ""
    j = " (justify %s)" % just if just else ""
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)%s\n'
            '\t\t\t(effects (font (size %s %s))%s)\n\t\t)' % (name, val, x, y, rot, h, size, size, j))

def _flip_just_h(j):
    """Swap left<->right in a justify string (KiCad mirrors horizontal justify for a 180-rotated symbol)."""
    if not j: return j
    return j.replace("left", "\0").replace("right", "left").replace("\0", "right")

def text_pos(lib_id, x, y, rot):
    """Where to put Reference / Value text so it clears pins, GND symbols and power flags.
    Returns (ref_x, ref_y, ref_just, val_x, val_y, val_just)."""
    passive = lib_id in ("Device:R", "Device:C", "Device:C_Polarized", "Device:D_Schottky", "Device:Polyfuse_Small")
    # D_Schottky's pins are HORIZONTAL at rot 0 (R/C/fuse are vertical); its text orientation is
    # therefore rotated 90 deg from the others, so classify "pins vertical?" accordingly.
    horiz0 = lib_id == "Device:D_Schottky"
    vertical_pins = ((rot + (90 if horiz0 else 0)) % 180) == 0
    if passive and vertical_pins:        # vertical 2-pin: stack text to the RIGHT (pins & GND are top/bottom)
        return (x + 2.8, y - 1.4, "left", x + 2.8, y + 1.4, "left")
    if passive:                          # horizontal 2-pin: ref above, value below (centered)
        return (x, y - 3.4, None, x, y + 3.4, None)
    if lib_id == "cremat:THS3491xDDA":   # op-amp: stack above-right, off the triangle body
        return (x + 2.0, y - 6.6, "left", x + 2.0, y - 9.1, "left")
    return (x + 2.0, y - 5.5, None, x + 2.0, y + 5.5, None)   # modules / connectors / trimpot

def sym_instance(lib_id, ref, value, fp, dnp, x, y, rot, root, iu, extra=None, hide_val=False):
    tang = (180 - (rot % 180)) % 180          # keep Reference/Value text horizontal & upright at any symbol rotation
    rx, ry, rj, vx, vy, vj = text_pos(lib_id, x, y, rot)
    if rot % 360 == 180:                       # KiCad flips L<->R justify for a 180-rotated symbol; pre-flip so
        rj, vj = _flip_just_h(rj), _flip_just_h(vj)   # left-stacked text still lands to the RIGHT (clear of the body)
    extralines = ""
    if extra:
        extralines = "\n" + "\n".join(prop(n, v, x, y, hide=True) for n, v in extra)
    return ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s %d)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp %s)\n\t\t(uuid "%s")\n%s\n%s\n%s%s\n'
            '\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "/%s" (reference "%s") (unit 1))\n\t\t\t)\n\t\t)\n\t)' % (
        lib_id, x, y, rot, "yes" if dnp else "no", iu,
        prop("Reference", ref, rx, ry, size=1.1, rot=tang, just=rj),
        prop("Value", value, vx, vy, hide=hide_val, size=1.0, rot=tang, just=vj),
        prop("Footprint", fp, x, y, hide=True),
        extralines, PROJ, root, ref))

def label(net, x, y, rot=0, j="left bottom"):
    return ('\t(label "%s"\n\t\t(at %s %s %d)\n\t\t(effects (font (size 1 1)) (justify %s))\n'
            '\t\t(uuid "%s")\n\t)' % (net, x, y, rot, j, uid("label", net, x, y)))

def power_sym(net, x, y, key, rot=0):
    iu = uid(key, "pwr", net, x, y)
    tang = (180 - (rot % 180)) % 180          # keep the "GND"/"+VDC" value text horizontal & upright when rotated
    return ('\t(symbol\n\t\t(lib_id "power:%s")\n\t\t(at %s %s %d)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp no)\n\t\t(uuid "%s")\n'
            '\t\t(property "Reference" "#PWR" (at %s %s %d) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "%s" (at %s %s %d) (effects (font (size 1.27 1.27))))\n'
            '\t\t(pin "1" (uuid "%s"))\n'
            '\t\t(instances (project "%s" (path "/%s" (reference "#PWR?") (unit 1))))\n\t)' % (
        net, x, y, rot, iu, x, y - 3, tang, net, x, y + 3, tang, uid(iu, "pin"), PROJ, ROOT))

def pwrflag(net, x, y, ref, rot=0):
    iu = uid(ROOT, "flag", net, ref)
    return ('\t(symbol\n\t\t(lib_id "power:PWR_FLAG")\n\t\t(at %s %s %d)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp no)\n\t\t(uuid "%s")\n'
            '\t\t(property "Reference" "%s" (at %s %s 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "PWR_FLAG" (at %s %s 0) (hide yes) (effects (font (size 1 1))))\n'
            '\t\t(pin "1" (uuid "%s"))\n'
            '\t\t(instances (project "%s" (path "/%s" (reference "%s") (unit 1))))\n\t)' % (
        x, y, rot, iu, ref, x, y - 3, x, y + 3, uid(iu, "pin"), PROJ, ROOT, ref))

# ---------- drawing state -------------------------------------------------------------
ROOT = uid("channel-root")
NODES = []          # emitted s-expr strings
SEGS = []           # list of (p1, p2) grid points, for auto-junctions
COVER = set()       # coordinates that carry a net (wire ends, labels, power, nc)
FLAGN = [0]

def _pt(p): return (G(p[0]), G(p[1]))

def W(*pts):
    """Draw an orthogonal polyline through pts (each connection point covered)."""
    pts = [_pt(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        if a == b: continue
        assert a[0] == b[0] or a[1] == b[1], "non-orthogonal wire %s->%s" % (a, b)
        NODES.append('\t(wire (pts (xy %s %s) (xy %s %s))\n\t\t(stroke (width 0) (type default))\n'
                     '\t\t(uuid "%s"))' % (a[0], a[1], b[0], b[1], uid("w", a, b)))
        SEGS.append((a, b))
    for p in pts: COVER.add(p)

def lbl(net, p, rot=0, j="left bottom"):
    p = _pt(p); NODES.append(label(net, p[0], p[1], rot, j)); COVER.add(p)

def pwr(net, p, rot=0):
    p = _pt(p); NODES.append(power_sym(net, p[0], p[1], "n", rot)); COVER.add(p)

def flag(net, p, rot=0):
    p = _pt(p); FLAGN[0] += 1
    NODES.append(pwrflag(net, p[0], p[1], "#FLG%d" % FLAGN[0], rot)); COVER.add(p)

def nc(p):
    p = _pt(p); NODES.append('\t(no_connect (at %s %s) (uuid "%s"))' % (p[0], p[1], uid("nc", p)))
    COVER.add(p)

def place(role, ref, extra):
    lib_id, fp, dnp, _nm, (x, y, rot) = SPEC[role]
    hide_val = role.startswith("J_")          # connectors: hide verbose value string (ref + net label say it all)
    NODES.append(sym_instance(lib_id, ref, _val(role), fp, dnp, G(x), G(y), rot, ROOT,
                              uid("sym", role), extra, hide_val=hide_val))

def P(role, num): return pinpt(role, num)

def gnd_bus(role, gpins, bus_y, sym_x=None):
    """Stub each GND pin down/up to a horizontal bus and drop ONE GND symbol.
    (auto_junctions() pre-splits the bus at every stub so all taps are end-to-end.)"""
    xs = sorted(P(role, p)[0] for p in gpins)
    for p in gpins:
        px, py = P(role, p); W((px, py), (px, bus_y))
    W((xs[0], bus_y), (xs[-1], bus_y))
    pwr("GND", (sym_x if sym_x is not None else xs[0], bus_y))

def power_terminal(role):
    """3-pin screw terminal on the RAW rails (pin1=+VDC_IN top, pin2=GND mid, pin3=-VDC_IN bottom).
    Pins exit left; the two rail labels spread above/below their stubs, and GND runs out to its own
    clear stub past the label column and points DOWN -- so nothing overlaps the -VDC_IN label."""
    p1 = P(role, "1"); p2 = P(role, "2"); p3 = P(role, "3")
    W(p1, (p1[0] - 6.35, p1[1])); lbl("+VDC_IN", (p1[0] - 6.35, p1[1]), j="right bottom")   # text above
    W(p3, (p3[0] - 6.35, p3[1])); lbl("-VDC_IN", (p3[0] - 6.35, p3[1]), j="right top")       # text below
    gx = p2[0] - 16.51                          # GND runs out past the -VDC_IN label column
    W(p2, (p2[0] - 6.35, p2[1]), (gx, p2[1])); pwr("GND", (gx, p2[1]))                       # GND points down

def coax_gnd(role, dx, dy, rot):
    """Coax shield (pin 2) -> GND on a short stub pointing AWAY from the jack body, so the ground
    symbol + text sit clear of the connector instead of overlapping it (legibility)."""
    p = P(role, "2"); q = (p[0] + dx, p[1] + dy)
    W(p, q); pwr("GND", q, rot=rot)

def rail_labels(role, npin, nnet, ppin, pnet):
    """Stub the -Vs and +Vs supply pins down below the pin-number row and spread their
    labels in opposite directions so the bipolar bias nets never merge/overlap the pins."""
    for pin, net, j in [(npin, nnet, "right bottom"), (ppin, pnet, "left bottom")]:
        px, py = P(role, pin)
        W((px, py), (px, py + 5.08))
        lbl(net, (px, py + 5.08), j=j)     # anchor ON the stub end; justify spreads the text L/R

def deco(rrole, cb, rail, vdc, top=True):
    """+/- rail decoupling: VDC -> R -> rail node -> one bulk cap to GND, + label + flag."""
    rp = P(rrole, "2"); cp = P(cb, "1")
    bus = rp[1] + 2.54                     # rail runs BETWEEN the R pin and the cap pin, through neither
    x0 = rp[0] - 6.35; x1 = cp[0] + 5.08
    pwr(vdc, P(rrole, "1"))
    # The rail is SPLIT at each tap so every T is wire-END-to-wire-END. A stub that merely ends
    # part-way along a longer wire does NOT connect in KiCad's GUI (its netlister is lenient and
    # will claim it does -- that discrepancy is what hid this for so long).
    W((x0, bus), (rp[0], bus), (cp[0], bus), (x1, bus))
    W(rp, (rp[0], bus))                    # R lower pin -> its own stub down -> T into the rail
    W(cp, (cp[0], bus))                    # cap upper pin -> its own stub up  -> T into the rail
    flag(rail, (x0, bus))
    lbl(rail, (x1, bus))                   # label sits ON the bus end so it names the rail
    pwr("GND", P(cb, "2"))

# ---------- the layout ----------------------------------------------------------------
def layout_channel():
    # ===== bias front-end + inputs =====
    # BIAS_IN: J_BIAS -> Rf1 ; JP_Rf1 bypass tap up
    W(P("J_BIAS", "1"), P("Rf1", "1")); W(P("Rf1", "1"), P("JP_Rf1", "1"))
    lbl("BIAS_IN", P("Rf1", "1"), j="right bottom")
    # N_filt: Rf1 -> Rf2, Cf tap down, JP_Rf1/JP_Rf2 bypass taps up
    _fx, _fy = P("Cf", "1")[0], P("Rf1", "2")[1]       # N_filt run, SPLIT at the Cf tap
    W(P("Rf1", "2"), (_fx, _fy), P("Rf2", "1"))
    W(P("Cf", "1"), (_fx, _fy))                        # Cf top pin -> stub up -> T into N_filt
    W(P("Rf1", "2"), P("JP_Rf1", "2")); W(P("Rf2", "1"), P("JP_Rf2", "1"))
    pwr("GND", P("Cf", "2"))
    lbl("N_filt", P("Cf", "1"))
    # FE: Rf2 -> Cc, J_SIPM tap down, JP_Rf2 bypass tap up
    W(P("Rf2", "2"), P("Cc", "1")); W(P("Rf2", "2"), P("JP_Rf2", "2"))
    W((P("J_SIPM", "1")[0], P("Cc", "1")[1]), P("J_SIPM", "1"))
    lbl("FE", P("Rf2", "2"))
    # CSP_IN: Cc -> U_CSP.1 ; C_test tap up
    W(P("Cc", "2"), P("U_CSP", "1")); W(P("Cc", "2"), (P("C_test", "2")[0], P("Cc", "2")[1]), P("C_test", "2"))
    lbl("CSP_IN", (P("Cc", "2")[0] + 1.27, P("Cc", "2")[1]))
    # test-injection branch: coax -> TEST_IN node (R5 = shunt termination to GND) -> C3 couples in
    _tx, _ty = P("R_test", "1")[0], P("J_TEST", "1")[1]        # TEST_IN rail, SPLIT at the R5 tap
    W(P("J_TEST", "1"), (_tx, _ty), P("C_test", "1"))
    W(P("R_test", "1"), (_tx, _ty))                            # R5 top pin -> stub up -> T into rail
    lbl("TEST_IN", (69.85, 140.97))
    pwr("GND", P("R_test", "2"))                               # R5 lower leg to ground
    coax_gnd("J_BIAS", 0.0, -3.81, 180)      # shield above the body -> GND points up/away
    coax_gnd("J_TEST", 0.0, -3.81, 180)
    coax_gnd("J_SIPM", 3.81, 0.0, 90)         # shield right of the body -> GND points right/away

    # ===== CR-112 CSP =====
    gnd_bus("U_CSP", ["2", "4", "7"], 128.27, sym_x=P("U_CSP", "7")[0])
    nc(P("U_CSP", "3"))
    rail_labels("U_CSP", "5", "-VS_F", "6", "+VS_F")
    deco("R_dvp", "Cp1", "+VS_F", "+VDC", top=True)
    deco("R_dvn", "Cn1", "-VS_F", "-VDC", top=False)

    # CSP_OUT: U_CSP.8 -> U_SH.1 ; trimpot.1 tap down
    W(P("U_CSP", "8"), P("U_SH", "1"))
    W((P("RV_PZ", "1")[0], P("U_SH", "1")[1]), P("RV_PZ", "1"))
    lbl("CSP_OUT", (P("U_CSP", "8")[0] + 3.81, P("U_CSP", "8")[1]))

    # ===== CR-200 shaper =====
    gnd_bus("U_SH", ["3", "6", "7"], 128.27, sym_x=P("U_SH", "7")[0])
    rail_labels("U_SH", "4", "SHVN", "5", "SHVP")
    deco("R_SHP", "C_SHPb", "SHVP", "+VDC", top=True)
    deco("R_SHN", "C_SHNb", "SHVN", "-VDC", top=False)
    # P/Z: U_SH.2 down to wiper, wiper<->bottom tied
    pz2 = P("RV_PZ", "2"); pz3 = P("RV_PZ", "3")
    W(P("U_SH", "2"), (P("U_SH", "2")[0], pz2[1]), pz2)
    W(pz2, (pz2[0], pz3[1]), pz3)
    lbl("PZ", (P("U_SH", "2")[0], P("U_SH", "2")[1] + 6.35))

    # SH_OUT: U_SH.8 -> U_BLR.1 ; JP_BLR.1 tap
    W(P("U_SH", "8"), P("U_BLR", "1"))
    W(P("U_BLR", "1"), (P("U_BLR", "1")[0], P("JP_BLR", "1")[1]), P("JP_BLR", "1"))
    lbl("SH_OUT", (P("U_SH", "8")[0] + 3.81, P("U_SH", "8")[1]))

    # ===== CR-210 BLR =====
    gnd_bus("U_BLR", ["2", "3", "6", "7"], 128.27, sym_x=P("U_BLR", "7")[0])
    rail_labels("U_BLR", "4", "BLVN", "5", "BLVP")
    deco("R_BLP", "C_BLPb", "BLVP", "+VDC", top=True)
    deco("R_BLN", "C_BLNb", "BLVN", "-VDC", top=False)

    # SHAPER_OUT: U_BLR.8 -> buffer +IN ; JP_BLR.2 tap down
    bp = P("U_BUF", "3")
    W(P("U_BLR", "8"), (P("U_BLR", "8")[0], P("JP_BLR", "2")[1]), P("JP_BLR", "2"))  # to bypass
    W(P("U_BLR", "8"), (bp[0] - 7.62, P("U_BLR", "8")[1]), (bp[0] - 7.62, bp[1]), bp)
    lbl("SHAPER_OUT", (P("U_BLR", "8")[0] + 3.81, P("U_BLR", "8")[1]))

    # ===== THS3491 buffer (non-inverting CFA, Av = 1 + R_FB/R_GAIN = +2) =====
    fb = P("U_BUF", "2"); o = P("U_BUF", "6")
    # BUF_FB node: R_GAIN.1 -- -IN -- up to R_FB left leg
    W(P("R_GAIN", "1"), fb)
    W(fb, (P("R_FB", "2")[0], fb[1]), P("R_FB", "2"))
    lbl("BUF_FB", (303.0, fb[1]))
    # BUF_OUT node: OUT -- R_BSER.1 ; OUT up to R_FB right leg
    W(o, P("R_BSER", "1"))
    W(o, (o[0], P("R_FB", "1")[1]), P("R_FB", "1"))
    lbl("BUF_OUT", (328.0, o[1]))
    # OUT_50 -> jack (49.9 series back-termination)
    W(P("R_BSER", "2"), P("J_OUT50", "1")); lbl("OUT_50", (344.0, P("R_BSER", "2")[1]))
    # V+ (7) & PD (8) tied -> one BVP up-stub ; V- (4) & EP (9) -> BVN out-stubs (REF sits between)
    W(P("U_BUF", "7"), P("U_BUF", "8"))
    W(P("U_BUF", "8"), (P("U_BUF", "8")[0], 105.73)); lbl("BVP", (P("U_BUF", "8")[0], 105.73))
    W(P("U_BUF", "4"), (P("U_BUF", "4")[0], 127.0), (P("U_BUF", "4")[0] - 3.81, 127.0))
    lbl("BVN", (P("U_BUF", "4")[0] - 3.81, 127.0), j="right bottom")
    W(P("U_BUF", "9"), (P("U_BUF", "9")[0], 127.0), (P("U_BUF", "9")[0] + 2.54, 127.0))
    lbl("BVN", (P("U_BUF", "9")[0] + 2.54, 127.0))
    # REF (1) -> GND ; gain leg -> GND ; NC ; output-jack shield
    W(P("U_BUF", "1"), (P("U_BUF", "1")[0], P("U_BUF", "1")[1] + 3.81))
    pwr("GND", (P("U_BUF", "1")[0], P("U_BUF", "1")[1] + 3.81))
    pwr("GND", P("R_GAIN", "2"))
    nc(P("U_BUF", "5"))
    coax_gnd("J_OUT50", 0.0, 3.81, 0)         # shield below the body -> GND points down/away
    deco("R_BVP", "C_BVPb", "BVP", "+VDC", top=True)
    deco("R_BVN", "C_BVNb", "BVN", "-VDC", top=False)
    # buffer-bypass 0R jumper (populate when the buffer block is DNP): SHAPER_OUT -> BUF_OUT
    W((295.91, 115.57), (295.91, 135.89), P("JP_BUF", "1"))    # tap SHAPER_OUT down to the jumper
    W(P("JP_BUF", "2"), (325.12, 135.89), (325.12, 115.57))    # jumper up to the BUF_OUT node

def layout_power():
    # ===== power entry: screw terminal -> PTC fuse -> series Schottky reverse-block -> board rail =====
    # Two clean HORIZONTAL rails: +VDC on top, -VDC below, fed BY NAME from the input terminal.
    # Left = node labels; ref/value sit centred under each part (text_pos); the rail power-symbols and
    # PWR_FLAGs live on their own short stubs pointing away from the parts; one isolated GND+flag pair
    # (in clear space) drives the ERC "power-input driven" check for GND.
    IN = 6.35                                          # input-label stub length

    # ---- input terminal J_PWR (pins exit left) -> +VDC_IN / GND / -VDC_IN
    power_terminal("J_PWR")

    # ---- +VDC rail:  +VDC_IN --[F_P PTC]--> +VDC_F --[D_RP anode->cathode]--> +VDC (rail) --> C_BULKP -> GND
    f1 = P("F_P", "1")
    W(f1, (f1[0] - IN, f1[1])); lbl("+VDC_IN", (f1[0] - IN, f1[1]), j="right bottom")
    W(P("F_P", "2"), P("D_RP", "2"))                                       # +VDC_F run: PTC out -> Schottky anode
    lbl("+VDC_F", ((P("F_P", "2")[0] + P("D_RP", "2")[0]) / 2, P("F_P", "2")[1]), j="left bottom")
    kx, ky = P("D_RP", "1")                                                # +VDC rail node = Schottky cathode
    W((kx, ky), P("C_BULKP", "1"))                                         # rail across to the bulk cap top pin
    W((kx + 7.62, ky), (kx + 7.62, ky - 3.81)); pwr("+VDC", (kx + 7.62, ky - 3.81))    # +VDC symbol up-stub
    W((kx + 12.70, ky), (kx + 12.70, ky - 3.81)); flag("+VDC", (kx + 12.70, ky - 3.81))
    pwr("GND", P("C_BULKP", "2"))                                          # bulk cap lower leg -> GND (points down)

    # ---- -VDC rail (mirror below):
    n1 = P("F_N", "1")
    W(n1, (n1[0] - IN, n1[1])); lbl("-VDC_IN", (n1[0] - IN, n1[1]), j="right bottom")
    W(P("F_N", "2"), P("D_RN", "1"))                                       # -VDC_F run: PTC out -> Schottky cathode
    lbl("-VDC_F", ((P("F_N", "2")[0] + P("D_RN", "1")[0]) / 2, P("F_N", "2")[1]), j="left bottom")
    ax, ay = P("D_RN", "2")                                                # -VDC rail node = Schottky anode
    W((ax, ay), P("C_BULKN", "2"))
    W((ax + 7.62, ay), (ax + 7.62, ay - 3.81)); pwr("-VDC", (ax + 7.62, ay - 3.81))    # up-stub, clear of the cap
    W((ax + 12.70, ay), (ax + 12.70, ay - 3.81)); flag("-VDC", (ax + 12.70, ay - 3.81))
    pwr("GND", P("C_BULKN", "1"))

    # ---- one isolated GND symbol + PWR_FLAG pair in clear space (right of the caps) for ERC
    gx = kx + 35.56; gy = ky + 7.62
    W((gx, gy - 3.81), (gx, gy)); flag("GND", (gx, gy - 3.81)); pwr("GND", (gx, gy))

def layout():
    layout_channel()
    layout_power()

def split_wires_at_taps():
    """KiCad connects wires END-to-END. A wire that merely ENDS part-way along another wire is NOT
    connected in the GUI -- even with a junction dot on top of it. (kicad-cli's netlister *is*
    lenient and reports such a tap as connected, which is exactly why this hid for so long.)
    So: split every segment at any other wire's endpoint lying on it, making all T-taps end-to-end."""
    pts = {p for seg in SEGS for p in seg}
    def on(p, a, b):
        if p == a or p == b: return False
        if a[1] == b[1] == p[1]: return min(a[0], b[0]) < p[0] < max(a[0], b[0])
        if a[0] == b[0] == p[0]: return min(a[1], b[1]) < p[1] < max(a[1], b[1])
        return False
    new = []
    for a, b in SEGS:
        cut = sorted((p for p in pts if on(p, a, b)),
                     key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
        chain = [a] + cut + [b]
        new += list(zip(chain, chain[1:]))
    NODES[:] = [n for n in NODES if not n.lstrip().startswith("(wire")]
    SEGS[:] = []
    for a, b in new:
        NODES.append('\t(wire (pts (xy %s %s) (xy %s %s))\n\t\t(stroke (width 0) (type default))\n'
                     '\t\t(uuid "%s"))' % (a[0], a[1], b[0], b[1], uid("w", a, b)))
        SEGS.append((a, b))

def auto_junctions():
    split_wires_at_taps()          # make every T end-to-end BEFORE deciding where dots go
    from collections import Counter
    cnt = Counter()
    for a, b in SEGS: cnt[a] += 1; cnt[b] += 1
    pin_pts = Counter()                       # component pin coordinates (a pin tapping a wire needs a dot)
    for role in ROLES:
        for num in SPEC[role][3]:
            pin_pts[P(role, num)] += 1
    def interior(p, seg):
        (x1, y1), (x2, y2) = seg
        if p == (x1, y1) or p == (x2, y2): return False
        if y1 == y2 and abs(p[1] - y1) < 1e-6: return min(x1, x2) < p[0] < max(x1, x2)
        if x1 == x2 and abs(p[0] - x1) < 1e-6: return min(y1, y2) < p[1] < max(y1, y2)
        return False
    junc = set()
    for p in set(cnt) | set(pin_pts):
        # conductors at p: wire-ends (1 each) + wires passing through interior (2 each) + pins (1 each)
        degree = cnt.get(p, 0) + 2 * sum(1 for s in SEGS if interior(p, s)) + pin_pts.get(p, 0)
        if degree >= 3: junc.add(p)
    for p in sorted(junc):
        # diameter 0 = "use the theme default" -- what KiCad itself writes. An explicit diameter is
        # legal but non-canonical, and is the only thing odd about how we emit junctions.
        NODES.append('\t(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))'
                     % (p[0], p[1], uid("j", p)))

def build():
    # assign references in ROLES order (per-prefix counters) -> identical to baseline
    cnt = {}; refmap = {}
    for role in ROLES:
        pfx = prefix_of(role); cnt[pfx] = cnt.get(pfx, 0) + 1
        refmap[role] = "%s%d" % (pfx, cnt[pfx])
    for role in ROLES:
        extra = None
        if role in PARTS:
            _v, mpn, mfr, dkpn = PARTS[role]
            extra = [("MPN", mpn), ("Manufacturer", mfr), ("Distributor PN", dkpn)]
        place(role, refmap[role], extra)
    layout()
    auto_junctions()
    # coverage self-check: every declared pin must carry a net
    missing = []
    for role in ROLES:
        for num in SPEC[role][3]:
            if P(role, num) not in COVER:
                missing.append("%s.%s @ %s" % (refmap[role], num, P(role, num)))
    if missing:
        print("WARNING: %d uncovered pins:\n  %s" % (len(missing), "\n  ".join(missing)))
    si = '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)'
    out = ('(kicad_sch\n\t(version %s)\n\t(generator "gen_sch.py")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "A3")\n'
           '\t(title_block\n\t\t(title "Single-channel SiPM CSP+shaper+buffer (channel)")\n'
           '\t\t(company "Yale / Brunner Neutrino Lab")\n\t)\n%s\n%s\n%s\n\t(embedded_fonts no)\n)\n' % (
        VERSION, ROOT, lib_symbols_block(), "\n".join(NODES), si))
    with open(os.path.join(HERE, "channel.kicad_sch"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote channel.kicad_sch: %d symbols, %d wire segments%s" % (
        len(ROLES), len(SEGS), "" if not missing else "  (SEE WARNING)"))

if __name__ == "__main__":
    build()
