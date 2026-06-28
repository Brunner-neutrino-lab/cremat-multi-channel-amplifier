#!/usr/bin/env python3
"""Generate the single-channel board schematic (Phase B, track B1 chan-design).

Merges the two PROVEN Phase-A sub-components AS-IS and appends the output buffer:

  BIAS_IN/SIPM -> [csp-cr112 front-end + CR-112] --CSP_OUT--> [CR-200 + CR-210 shaper]
      --SHAPER_OUT--> [EL5167-class CFA buffer, Av=+2] --49.9R--> OUT_50 (MCX, 50ohm back-term)

The CSP and shaper blocks are reproduced with the same nets / values / footprints / DNP as
their COMPLETE INTERFACE.md contracts (real parts). The ONLY structural joins are:
  * the shaper input == CSP output  (net `CSP_OUT`, was the shaper's `SH_IN`/`IN`)
  * the shaper output -> buffer +IN  (net `SHAPER_OUT`, was the shaper's `OUT`)
The standalone-board-only jacks (CSP J_OUT, shaper J_IN) and one screw terminal are dropped
in the merge; new boundary MCX jacks are BIAS_IN, SIPM, TEST_IN, OUT_50; one screw terminal.

This flat sheet is the reusable `channel` cell. Phase C multiplies the per-channel block 12x
(the same way hardware/gen_sch.py replicates a per-channel block with net labels), so every
net that must stay per-channel is a plain local label (suffix-able), while shared rails are
power symbols.

Method (docs/KICAD_WITH_CLAUDE_CODE.md): place every symbol at rotation 0 and connect pins
by dropping a net label (signal) or power symbol (rail) at the *exact* pin coordinate -- no
routed wires. Connectivity is by net name + coincident pins; ERC proves it. UUIDs are
deterministic (uuid5) so re-runs reproduce the file.

Run:  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_sch.py
Validate: kicad-cli sch erc channel.kicad_sch
"""
import os, re, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
CREMAT_SYM = os.path.join(HERE, "lib", "cremat.kicad_sym")
STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/symbols"
PROJ = "channel"
NS = uuid.UUID("b1c2d3e4-0000-4000-8000-000000000000")   # B1-namespaced (distinct from A1/A4)
VERSION = "20260306"

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
FP_C     = "Capacitor_SMD:C_0805_2012Metric"           # 0.1uF HF + 10uF local bulk (0805)
FP_CPELEC= "Capacitor_SMD:CP_Elec_6.3x7.7"             # 100uF SMD can rail bulk (B3-reconciled, both rails)
FP_SIP   = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"   # CR-module SIP-8, 2.54mm
FP_TRIM  = "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical"
FP_MCX   = "cremat:MCX_CONMCX013_EdgeMount"
FP_SCREW = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal"
FP_SOIC8EP = "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm"   # TI THS3491 DDA PowerPAD (EP=pad9)

# ---------- real-part metadata (from the two COMPLETE Phase-A INTERFACEs; buffer = generic) ----------
# (Value, MPN, Manufacturer, DigiKey_PN). BUFFER rows are GENERIC pending B3 (real-parts gate).
# Value strings ALIGNED to B3 single-channel-bom.csv so the design BOM matches line-for-line.
PARTS = {
    # --- CSP block (csp-cr112) ---
    "Cf":     ("100nF 100V X7R",      "CL21B104KCC5PNC",   "Samsung Electro-Mechanics", "1276-2447-1-ND"),
    "Cc":     ("0.22uF 100V X7R",     "GRM21AR72A224KAC5K","Murata Electronics",        "490-GRM21AR72A224KAC5K"),
    "C_test": ("1pF 50V C0G",         "CC0805CRNPO9BN1R0", "Yageo",                     "311-CC0805CRNPO9BN1R0CT-ND"),
    "Rf1":    ("10k",                 "RC0805FR-0710KL",   "Yageo",                     "311-10.0KCRCT-ND"),
    "Rf2":    ("10k",                 "RC0805FR-0710KL",   "Yageo",                     "311-10.0KCRCT-ND"),
    "JP_Rf1": ("0R",                  "RC0805JR-070RL",    "Yageo",                     "311-0.0ARCT-ND"),
    "JP_Rf2": ("0R",                  "RC0805JR-070RL",    "Yageo",                     "311-0.0ARCT-ND"),
    "R_test": ("47",                  "RC0805JR-0747RL",   "Yageo",                     "311-47ARCT-ND"),
    "R_dvp":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_dvn":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "Cp1":    ("10uF 25V X5R",        "CL21A106KAYNNNE",   "Samsung Electro-Mechanics", "1276-1037-1-ND"),
    "Cp2":    ("0.1uF 50V X7R",       "CL21B104KBCNNNC",   "Samsung Electro-Mechanics", "1276-1000-1-ND"),
    "Cn1":    ("10uF 25V X5R",        "CL21A106KAYNNNE",   "Samsung Electro-Mechanics", "1276-1037-1-ND"),
    "Cn2":    ("0.1uF 50V X7R",       "CL21B104KBCNNNC",   "Samsung Electro-Mechanics", "1276-1000-1-ND"),
    "U_CSP":  ("CR-112",              "CR-112-R2.1",       "Cremat Inc",                "N/A (Cremat-direct)"),
    # --- shaper block (shaper-cr200-cr210). NOTE: the shaper's board-edge 49.9 R_OUT is
    #     DROPPED in the merge (B3 dedupe): CR-210 out feeds the buffer +IN directly (high-Z),
    #     and the single channel 49.9 back-term lives at OUT_50 after the buffer. ---
    "U_SH":   ("CR-200-1us",          "CR-200-1us-R2.1",   "Cremat Inc",                "N/A (Cremat-direct)"),
    "U_BLR":  ("CR-210",              "CR-210-R0",         "Cremat Inc",                "N/A (Cremat-direct)"),
    "RV_PZ":  ("200k",                "3296W-1-204LF",     "Bourns",                    "3296W-204LF-ND"),
    "R_SHP":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_SHN":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_BLP":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_BLN":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "JP_BLR": ("0R",                  "RC0805JR-070RL",    "Yageo",                     "311-0.0ARCT-ND"),
    "C_SHPb": ("10uF 25V X5R",        "CL21A106KAYNNNE",   "Samsung Electro-Mechanics", "1276-1037-1-ND"),
    "C_SHPh": ("0.1uF 50V X7R",       "CL21B104KBCNNNC",   "Samsung Electro-Mechanics", "1276-1000-1-ND"),
    "C_SHNb": ("10uF 25V X5R",        "CL21A106KAYNNNE",   "Samsung Electro-Mechanics", "1276-1037-1-ND"),
    "C_SHNh": ("0.1uF 50V X7R",       "CL21B104KBCNNNC",   "Samsung Electro-Mechanics", "1276-1000-1-ND"),
    "C_BLPb": ("10uF 25V X5R",        "CL21A106KAYNNNE",   "Samsung Electro-Mechanics", "1276-1037-1-ND"),
    "C_BLPh": ("0.1uF 50V X7R",       "CL21B104KBCNNNC",   "Samsung Electro-Mechanics", "1276-1000-1-ND"),
    "C_BLNb": ("10uF 25V X5R",        "CL21A106KAYNNNE",   "Samsung Electro-Mechanics", "1276-1037-1-ND"),
    "C_BLNh": ("0.1uF 50V X7R",       "CL21B104KBCNNNC",   "Samsung Electro-Mechanics", "1276-1000-1-ND"),
    # --- board bulk electrolytics (B3-reconciled: ONE pair, Nichicon UWT SMD, both rails) ---
    "C_BULKP":("100uF 35V",           "UWT1V101MCL1GS",    "Nichicon",                  "493-2203-1-ND"),
    "C_BULKN":("100uF 35V",           "UWT1V101MCL1GS",    "Nichicon",                  "493-2203-1-ND"),
    # --- output buffer (REAL, B3 gate resolved: coordinator picked THS3491) ---
    "U_BUF":  ("THS3491",             "THS3491IDDAT",      "Texas Instruments",         "296-49085-2-ND"),
    # Rf=Rg=976R: TI THS3491 datasheet G=+2 recommended feedback resistor (CFA Rf sets loop
    # stability) -- B2 validated this value against TI's official SPICE model. Value-only swap
    # from 1.21k (same RC0805 footprint). Av = 1 + 976/976 = +2 (unchanged).
    "R_FB":   ("976",                 "RC0805FR-07976RL",  "Yageo",                     "311-976CRCT-ND"),
    "R_GAIN": ("976",                 "RC0805FR-07976RL",  "Yageo",                     "311-976CRCT-ND"),
    "R_BSER": ("49.9",                "RC0805FR-0749R9L",  "Yageo",                     "311-49.9CRCT-ND"),
    "R_BVP":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "R_BVN":  ("4.7",                 "RC0805JR-074R7L",   "Yageo",                     "311-4.7ARCT-ND"),
    "C_BVPb": ("10uF 25V X5R",        "CL21A106KAYNNNE",   "Samsung Electro-Mechanics", "1276-1037-1-ND"),
    "C_BVPh": ("0.1uF 50V X7R",       "CL21B104KBCNNNC",   "Samsung Electro-Mechanics", "1276-1000-1-ND"),
    "C_BVNb": ("10uF 25V X5R",        "CL21A106KAYNNNE",   "Samsung Electro-Mechanics", "1276-1037-1-ND"),
    "C_BVNh": ("0.1uF 50V X7R",       "CL21B104KBCNNNC",   "Samsung Electro-Mechanics", "1276-1000-1-ND"),
    # --- shared boundary parts ---
    "J_BIAS": ("MCX edge jack 50R",   "CONMCX013",         "TE Connectivity / Linx",    "343-CONMCX013-ND"),
    "J_SIPM": ("MCX edge jack 50R",   "CONMCX013",         "TE Connectivity / Linx",    "343-CONMCX013-ND"),
    "J_TEST": ("MCX edge jack 50R",   "CONMCX013",         "TE Connectivity / Linx",    "343-CONMCX013-ND"),
    "J_OUT50":("MCX edge jack 50R",   "CONMCX013",         "TE Connectivity / Linx",    "343-CONMCX013-ND"),
    "J_PWR":  ("Screw terminal 3-pos 5.08mm", "1715734",   "Phoenix Contact",           "277-1264-ND"),
}

def _val(role):
    return PARTS[role][0] if role in PARTS else role

# ---------- channel netlist spec ----------
# role : (lib_id, value, footprint, dnp, (x,y), {pin#: net})
# nets +VDC/-VDC/GND -> power symbol; "NC" -> no-connect; anything else -> local label.
# Coordinates are schematic-readability only (PCB placement is independent in gen_pcb.py);
# left->right by signal flow, generous spacing so labels don't collide.
def build_spec():
    spec = []
    # =========================== CSP BLOCK (csp-cr112, reused as-is) ===========================
    # SiPM bias front-end (HV): BIAS_IN -> Rf1/JP_Rf1 -> N_filt(-Cf->GND) -> Rf2/JP_Rf2 -> FE
    spec += [
        ("J_BIAS","Connector:Conn_Coaxial", _val("J_BIAS"), FP_MCX, False, (25, 55), {"1":"BIAS_IN","2":"GND"}),
        ("Rf1",   "Device:R",               _val("Rf1"),    FP_R,   False, (45, 40), {"1":"BIAS_IN","2":"N_filt"}),
        ("JP_Rf1","Device:R",               _val("JP_Rf1"), FP_R,   True,  (45, 65), {"1":"BIAS_IN","2":"N_filt"}),
        ("Cf",    "Device:C",               _val("Cf"),     FP_C,   False, (60, 50), {"1":"N_filt","2":"GND"}),
        ("Rf2",   "Device:R",               _val("Rf2"),    FP_R,   False, (75, 40), {"1":"N_filt","2":"FE"}),
        ("JP_Rf2","Device:R",               _val("JP_Rf2"), FP_R,   True,  (75, 65), {"1":"N_filt","2":"FE"}),
        ("J_SIPM","Connector:Conn_Coaxial", _val("J_SIPM"), FP_MCX, False, (90, 70), {"1":"FE","2":"GND"}),
        ("Cc",    "Device:C",               _val("Cc"),     FP_C,   False, (100,40), {"1":"FE","2":"CSP_IN"}),
        # charge-injection test input (per CR-150-R5: 47R + 1pF)
        ("J_TEST","Connector:Conn_Coaxial", _val("J_TEST"), FP_MCX, False, (100,90), {"1":"TEST_IN","2":"GND"}),
        ("R_test","Device:R",               _val("R_test"), FP_R,   False, (115,85), {"1":"TEST_IN","2":"TEST_N"}),
        ("C_test","Device:C",               _val("C_test"), FP_C,   False, (115,65), {"1":"TEST_N","2":"CSP_IN"}),
        # CR-112 CSP module: pin8 out -> CSP_OUT (this net == shaper input, the merge join)
        ("U_CSP", "cremat:CR-11X",          _val("U_CSP"),  FP_SIP, False, (135,40),
            {"1":"CSP_IN","2":"GND","3":"NC","4":"GND","5":"-VS_F","6":"+VS_F","7":"GND","8":"CSP_OUT"}),
        # CR-112 per-rail decoupling (CR-150-R5: 4.7R series + 10uF + 0.1uF)
        ("R_dvp", "Device:R",               _val("R_dvp"),  FP_R,   False, (125,105),{"1":"+VDC","2":"+VS_F"}),
        ("Cp1",   "Device:C",               _val("Cp1"),    FP_C,   False, (135,115),{"1":"+VS_F","2":"GND"}),
        ("Cp2",   "Device:C",               _val("Cp2"),    FP_C,   False, (145,115),{"1":"+VS_F","2":"GND"}),
        ("R_dvn", "Device:R",               _val("R_dvn"),  FP_R,   False, (125,130),{"1":"-VDC","2":"-VS_F"}),
        ("Cn1",   "Device:C",               _val("Cn1"),    FP_C,   False, (135,140),{"1":"-VS_F","2":"GND"}),
        ("Cn2",   "Device:C",               _val("Cn2"),    FP_C,   False, (145,140),{"1":"-VS_F","2":"GND"}),
        # (CSP standalone radial entry-bulk Cb_p/Cb_n REMOVED in the merge -- B3 dedupe:
        #  the channel keeps ONE pair of 100uF rail bulk = the shaper SMD electrolytics below.)
    ]
    # =========================== SHAPER BLOCK (shaper-cr200-cr210, reused as-is) ===============
    # CR-200 input == CSP_OUT (merge join). P/Z trim = 200k trimpot alone.
    spec += [
        ("U_SH",  "cremat:CR-200", _val("U_SH"), FP_SIP, False, (180,40),
            {"1":"CSP_OUT", "2":"PZ", "3":"GND", "4":"SHVN", "5":"SHVP",
             "6":"GND", "7":"GND", "8":"SH_OUT"}),
        ("RV_PZ", "Device:R_Potentiometer_Trim_US", _val("RV_PZ"), FP_TRIM, False, (180,75),
            {"1":"CSP_OUT", "2":"PZ", "3":"PZ"}),
        # CR-200 per-rail decoupling
        ("R_SHP", "Device:R", _val("R_SHP"), FP_R, False, (162,18), {"1":"+VDC","2":"SHVP"}),
        ("C_SHPb","Device:C", _val("C_SHPb"),FP_C, False, (170,18), {"1":"SHVP","2":"GND"}),
        ("C_SHPh","Device:C", _val("C_SHPh"),FP_C, False, (176,18), {"1":"SHVP","2":"GND"}),
        ("R_SHN", "Device:R", _val("R_SHN"), FP_R, False, (162,58), {"1":"-VDC","2":"SHVN"}),
        ("C_SHNb","Device:C", _val("C_SHNb"),FP_C, False, (170,58), {"1":"SHVN","2":"GND"}),
        ("C_SHNh","Device:C", _val("C_SHNh"),FP_C, False, (176,58), {"1":"SHVN","2":"GND"}),
        # CR-210 BLR between SH_OUT and the shaper-output node, with JP_BLR 0R populate-XOR bypass.
        # In the merged channel the CR-210 output IS the shaper output node `SHAPER_OUT` (the
        # shaper's standalone board-edge 49.9 R_OUT is dropped -- B3 dedupe -- since SHAPER_OUT
        # now feeds the buffer's high-Z +IN directly; the single 49.9 back-term is at OUT_50).
        ("U_BLR", "cremat:CR-210", _val("U_BLR"), FP_SIP, False, (220,40),
            {"1":"SH_OUT", "2":"GND", "3":"GND", "4":"BLVN", "5":"BLVP",
             "6":"GND", "7":"GND", "8":"SHAPER_OUT"}),
        ("R_BLP", "Device:R", _val("R_BLP"), FP_R, False, (202,18), {"1":"+VDC","2":"BLVP"}),
        ("C_BLPb","Device:C", _val("C_BLPb"),FP_C, False, (210,18), {"1":"BLVP","2":"GND"}),
        ("C_BLPh","Device:C", _val("C_BLPh"),FP_C, False, (216,18), {"1":"BLVP","2":"GND"}),
        ("R_BLN", "Device:R", _val("R_BLN"), FP_R, False, (202,58), {"1":"-VDC","2":"BLVN"}),
        ("C_BLNb","Device:C", _val("C_BLNb"),FP_C, False, (210,58), {"1":"BLVN","2":"GND"}),
        ("C_BLNh","Device:C", _val("C_BLNh"),FP_C, False, (216,58), {"1":"BLVN","2":"GND"}),
        # JP_BLR bypass bridges CR-200 out (SH_OUT) <-> shaper-output node (SHAPER_OUT)
        ("JP_BLR","Device:R", _val("JP_BLR"),FP_R, True,  (220,80), {"1":"SH_OUT","2":"SHAPER_OUT"}),
        # board bulk electrolytics (100uF SMD, B3-reconciled): the channel's ONE rail-bulk pair
        ("C_BULKP","Device:C_Polarized", _val("C_BULKP"), FP_CPELEC, False, (60,135), {"1":"+VDC","2":"GND"}),
        ("C_BULKN","Device:C_Polarized", _val("C_BULKN"), FP_CPELEC, False, (75,135), {"1":"GND","2":"-VDC"}),
    ]
    # =========================== OUTPUT BUFFER (TI THS3491, HV CFA) ============================
    # Non-inverting CFA, Av = 1 + R_FB/R_GAIN = +2 (Rf=Rg=976R). Output -> 49.9R -> OUT_50
    # (50 ohm back-term). THS3491 DDA (SOIC-8 PowerPAD) pin map (KiCad THS3491xDDA symbol /
    # datasheet): 1=REF 2=-IN 3=+IN 4=V- 5=NC 6=OUT 7=V+ 8=PD 9=EP(thermal pad).
    #   REF(1) -> GND (split-supply mode; enable/disable thresholds set vs GND);
    #   PD(8)  -> V+ (tie high = enabled; TI advises not floating PD);
    #   EP(9)  -> V- (coordinator instruction; thermal pad sinks to the -VDC plane).
    # Supply via per-rail 4.7R+10uF+0.1uF (BVP/BVN), same pattern as the modules.
    spec += [
        ("U_BUF", "cremat:THS3491xDDA", _val("U_BUF"), FP_SOIC8EP, False, (290,40),
            {"1":"GND", "2":"BUF_FB", "3":"SHAPER_OUT", "4":"BVN", "5":"NC",
             "6":"BUF_OUT", "7":"BVP", "8":"BVP", "9":"BVN"}),
        ("R_FB",  "Device:R", _val("R_FB"),   FP_R, False, (290,75), {"1":"BUF_OUT","2":"BUF_FB"}),  # OUT -> -IN
        ("R_GAIN","Device:R", _val("R_GAIN"), FP_R, False, (290,95), {"1":"BUF_FB","2":"GND"}),       # -IN -> GND
        ("R_BSER","Device:R", _val("R_BSER"), FP_R, False, (315,40), {"1":"BUF_OUT","2":"OUT_50"}),   # 49.9R series
        ("J_OUT50","Connector:Conn_Coaxial", _val("J_OUT50"), FP_MCX, False, (335,45), {"1":"OUT_50","2":"GND"}),
        # buffer per-rail decoupling (4.7R + 10uF + 0.1uF)
        ("R_BVP", "Device:R", _val("R_BVP"), FP_R, False, (272,18), {"1":"+VDC","2":"BVP"}),
        ("C_BVPb","Device:C", _val("C_BVPb"),FP_C, False, (280,18), {"1":"BVP","2":"GND"}),
        ("C_BVPh","Device:C", _val("C_BVPh"),FP_C, False, (286,18), {"1":"BVP","2":"GND"}),
        ("R_BVN", "Device:R", _val("R_BVN"), FP_R, False, (272,58), {"1":"-VDC","2":"BVN"}),
        ("C_BVNb","Device:C", _val("C_BVNb"),FP_C, False, (280,58), {"1":"BVN","2":"GND"}),
        ("C_BVNh","Device:C", _val("C_BVNh"),FP_C, False, (286,58), {"1":"BVN","2":"GND"}),
    ]
    # =========================== POWER ENTRY ==================================================
    spec += [
        ("J_PWR", "Connector:Screw_Terminal_01x03", _val("J_PWR"), FP_SCREW, False, (25, 110),
            {"1":"+VDC", "2":"GND", "3":"-VDC"}),
    ]
    return spec

def prefix_of(role):
    if role.startswith("JP"): return "R"
    if role.startswith("RV"): return "RV"
    if role.startswith("U_"): return "U"
    if role.startswith("J_"): return "J"
    return role[0]

# ---------- emitters (same structure as the Phase-A gen_sch scripts) ----------
def prop(name, val, x, y, hide=False, rot=0):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)%s\n'
            '\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)' % (name, val, x, y, rot, h))

def sym_instance(lib_id, ref, value, fp, dnp, x, y, paths, inst_uuid, hide_val=False, extra=None):
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
    spec = build_spec()
    root = uid("channel-root")
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
            if net == "NC":
                nodes.append('\t(no_connect (at %s %s) (uuid "%s"))' % (ax, ay, uid("nc", role, p)))
                continue
            if net in ("+VDC", "-VDC", "GND"):
                nodes.append(power_sym(net, ax, ay, "channel:%s:%s" % (role, p)))
            else:
                nodes.append(label(net, ax, ay, "channel"))
    # drive each rail once with a PWR_FLAG at the screw terminal so ERC sees a source
    jp = pins_of("Connector:Screw_Terminal_01x03")
    fpx, fpy = pins_of("power:PWR_FLAG")["1"]
    jx, jy = G(25), G(110)
    for i, (p, net) in enumerate({"1": "+VDC", "2": "GND", "3": "-VDC"}.items(), 1):
        px, py = jp[p]; ax, ay = G(jx + px), G(jy - py)
        nodes.append(pwrflag(net, G(ax - fpx), G(ay + fpy), root, "#FLG%d" % i))
    # The module/buffer supply pins are power_in on FILTERED rail nodes (post-4.7R), which ERC
    # can't see being driven through a passive R. Flag each filtered supply node so ERC sees a
    # power source. (Electrically the 4.7R/10uF/0.1uF are still the real RC filter.)
    filt_nets = ["+VS_F", "-VS_F", "SHVP", "SHVN", "BLVP", "BLVN", "BVP", "BVN"]
    fy = G(155); fxs = G(40)
    for i, net in enumerate(filt_nets):
        ax, ay = G(fxs + i * 14), fy
        nodes.append(label(net, ax, ay, "channel"))
        nodes.append(pwrflag(net, G(ax - fpx), G(ay + fpy), root, "#FLGF%d" % i))
    si = '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)'
    out = ('(kicad_sch\n\t(version %s)\n\t(generator "gen_sch.py")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "A3")\n'
           '\t(title_block\n\t\t(title "Single-channel SiPM CSP+shaper+buffer (channel)")\n'
           '\t\t(company "Yale / Brunner Neutrino Lab")\n\t)\n%s\n%s\n%s\n\t(embedded_fonts no)\n)\n' % (
        VERSION, root, lib_symbols_block(), "\n".join(nodes), si))
    with open(os.path.join(HERE, "channel.kicad_sch"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote channel.kicad_sch: %d symbols (CSP+shaper+buffer)" % len(spec))

if __name__ == "__main__":
    build()
