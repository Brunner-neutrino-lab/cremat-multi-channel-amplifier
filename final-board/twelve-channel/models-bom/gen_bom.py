#!/usr/bin/env python3
"""Generate twelve-channel-bom.csv from the board's netlist + board (authoritative).

Groups the 464 placed parts by (MPN, value, DNP) into purchasing line items, rolls up quantity,
and enriches each line with metadata (Description/Block/Package/HV/Datasheet/Cost/Stock/Notes)
from the single-channel BOM by MPN. Common-power parts up-rated for 12x (new MPNs) get their
metadata from COMMON_META below (filled from the sourcing verification).

  "C:/Program Files/KiCad/10.0/bin/python.exe" gen_bom.py
"""
import os, re, csv
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.join(HERE, "..", "design")
NET = os.path.join(DESIGN, "twelve-channel.net")
PCB = os.path.join(DESIGN, "twelve-channel.kicad_pcb")
SC_BOM = os.path.abspath(os.path.join(HERE, "..", "..", "..", "integration", "single-channel", "models-bom", "single-channel-bom.csv"))
OUT = os.path.join(HERE, "twelve-channel-bom.csv")

# ---- metadata for the up-rated common-power parts (not in the single-channel BOM) ----
# filled from SOURCING-VERIFICATION; keyed by MPN.
COMMON_META = {
    "1812L110/24DR": {"Description": "Resettable PTC fuse, rail fault-interrupt (1.1A hold; up-rated for 12x)",
        "Block": "POWER", "Package": "1812", "HV_Rating": "24V",
        "Datasheet": "https://www.littelfuse.com/assetdocs/resettable-ptcs-1812l-datasheet",
        "Unit_Cost_USD": "0.78", "Stock_Qty": "~1.5k (DK, 2026-07)",
        "Notes": "Verified 2026-07-08 (provisional Bourns MF-MSMF110-2 rejected: obsolete + only 6V). Ihold 1.1A (23C) vs 0.584A worst-case (+rail, all 12 buffers) = ~1.9x margin; Itrip 1.95A, Vmax 24V. F_P=+12V, F_N=-12V. Hold derates to ~0.9A near 50C, still >>0.6A."},
    "SSA24": {"Description": "Schottky reverse-polarity block, SMA (40V/2A; up-rated for 12x)",
        "Block": "POWER", "Package": "DO-214AC (SMA)", "HV_Rating": "40V Vr",
        "Datasheet": "https://www.onsemi.com/pdf/datasheet/ssa24-d.pdf",
        "Unit_Cost_USD": "0.84", "Stock_Qty": "~16k (DK, 2026-07)",
        "Notes": "Verified 2026-07-08 (provisional SS24 rejected: SS24 is SMB/DO-214AA, wrong footprint, + obsolete). SSA prefix = SMA package. Series reverse-block: cathode->+VDC (D_RP), anode->-VDC (D_RN). Vf ~0.35-0.4V @ 0.5A; 2A >> ~0.5A per-diode."},
    "EEE-FN1V471UP": {"Description": "Board bulk electrolytic 470uF, rail reservoir (up-rated for 12x)",
        "Block": "POWER", "Package": "SMD can Ø10x10.5mm", "HV_Rating": "35V",
        "Datasheet": "https://industrial.panasonic.com/cdbs/www-data/pdf/RDE0000/RDE0000C1259.pdf",
        "Unit_Cost_USD": "1.17", "Stock_Qty": "~2.8k (DK, 2026-07)",
        "Notes": "Verified 2026-07-08 (provisional Nichicon UWT1V471MNL1GS was fictional: 35V UWT tops at 47uF). Panasonic FN-series, Ø10x10.5mm exact CP_Elec_10x10.5 fit. Up-rated from single-channel 100uF; 35V ~3x margin. Backs the 12x distributed 10uF."},
    # Cremat modules at the qty-12 tier of the 2026-01 US price list (10-99 pcs): CR-112 $55,
    # CR-200-1us $55, CR-210 $77 -> modules subtotal $2,244. (List q1 prices: $65/$65/$86.)
    # Qty 12 exceeds Cremat's Amazon <=10 limit: order by email (info@cremat.com).
    "CR-112-R2.1":     {"Unit_Cost_USD": "55.00",
        "Notes": "Not a Digi-Key part. 2026-01 US list: $65 (1-9) / $55 (10-99) / $47 (100+) - qty 12 = $55 tier. Order by email (qty > Amazon's 10 limit). Long lead - order early."},
    "CR-200-1us-R2.1": {"Unit_Cost_USD": "55.00",
        "Notes": "Not a Digi-Key part. 2026-01 US list: $65 (1-9) / $55 (10-99) / $47 (100+) - qty 12 = $55 tier. Order by email. Long lead - order early."},
    "CR-210-R0":       {"Unit_Cost_USD": "77.00",
        "Notes": "Not a Digi-Key part. 2026-01 US list: $86 (1-9) / $77 (10-99) / $73.10 (100+) - qty 12 = $77 tier. XOR with JP_BLR. DNP in CR-210-bypassed variant."},
    # override the single-channel MCX metadata: it is the SAME jack in all 4 coax roles
    # (BIAS/SIPM/TEST/OUT), and the SiPM bias is now confirmed <=70V (was "<=60V").
    "CONMCX013": {"Description": "50 ohm MCX edge-mount jack (BIAS / SIPM / TEST / OUT_50) - 4 per channel",
        "Block": "IO", "Package": "MCX edge SMT", "HV_Rating": "net rated >=100V (creepage); SiPM bias <=70V",
        "Datasheet": "https://linxtechnologies.com/wp/wp-content/uploads/conmcx013-ds.pdf",
        "Unit_Cost_USD": "3.22", "Stock_Qty": "~1050 (DK, 2026-07)",
        "Notes": "Linx CONMCX013 (TE Connectivity), footprint cremat:MCX_CONMCX013-T. HV on center pin -> creepage is a DRC concern (waived edge_clearance for this fp). 48 total = 4 roles x 12 ch. DK 343-CONMCX013-ND; -T = tape-and-reel packaging of the same connector."},
}

def load_sc_meta():
    meta = {}
    with open(SC_BOM, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m = row["MPN"]
            meta.setdefault(m, {k: row[k] for k in
                ("Description", "Block", "Package", "HV_Rating", "Datasheet", "Unit_Cost_USD", "Stock_Qty", "Notes")})
    return meta

def parse_net():
    t = open(NET, encoding="utf-8").read()
    parts = {}
    for cm in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)(?=\(comp\s|\(libparts)', t, re.S):
        ref, body = cm.group(1), cm.group(2)
        g = lambda p: (re.search(p, body) or [None, ""])[1] if re.search(p, body) else ""
        val = re.search(r'\(value "([^"]*)"\)', body)
        fp = re.search(r'\(footprint "([^"]*)"\)', body)
        fields = dict(re.findall(r'\(field\s+\(name "([^"]+)"\)\s*"([^"]*)"\)', body))
        parts[ref] = {"value": val.group(1) if val else "", "fp": fp.group(1) if fp else "",
                      "MPN": fields.get("MPN", ""), "Manufacturer": fields.get("Manufacturer", ""),
                      "DigiKey_PN": fields.get("Distributor PN", "")}
    return parts

def refkey(ref):
    m = re.match(r'^([A-Za-z]+)(\d+)$', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)

def summarize_refs(refs):
    refs = sorted(refs, key=refkey)
    return refs[0] + (" .. " + refs[-1] + " (%d)" % len(refs) if len(refs) > 1 else "")

def main():
    parts = parse_net()
    b = pcbnew.LoadBoard(PCB)
    dnp = {fp.GetReference(): fp.IsDNP() for fp in b.GetFootprints()}
    sc = load_sc_meta()

    groups = {}
    for ref, p in parts.items():
        key = (p["MPN"], p["value"], p["fp"], bool(dnp.get(ref, False)))
        groups.setdefault(key, {"refs": [], **p}).setdefault("refs", []).append(ref)

    cols = ["Value", "Description", "Block", "Footprint", "MPN", "Manufacturer", "DigiKey_PN",
            "Qty", "Populate", "Unit_Cost_USD", "Ext_Cost_USD", "Stock_Qty", "Package",
            "HV_Rating", "Datasheet", "Refs", "Notes"]
    rows = []
    for (mpn, val, fp, is_dnp), g in groups.items():
        # COMMON_META overrides the single-channel metadata for listed keys (e.g. the MCX).
        meta = {**(sc.get(mpn) or {}), **COMMON_META.get(mpn, {})}
        qty = len(g["refs"])
        try: unit = float(str(meta.get("Unit_Cost_USD", "")).split()[0]); ext = "%.2f" % (unit * qty)
        except Exception: ext = ""
        rows.append({
            "Value": val, "Description": meta.get("Description", ""), "Block": meta.get("Block", ""),
            "Footprint": fp, "MPN": mpn, "Manufacturer": g["Manufacturer"], "DigiKey_PN": g["DigiKey_PN"],
            "Qty": qty, "Populate": "DNP" if is_dnp else "FIT",
            "Unit_Cost_USD": meta.get("Unit_Cost_USD", ""), "Ext_Cost_USD": ext,
            "Stock_Qty": meta.get("Stock_Qty", ""), "Package": meta.get("Package", ""),
            "HV_Rating": meta.get("HV_Rating", ""), "Datasheet": meta.get("Datasheet", ""),
            "Refs": summarize_refs(g["refs"]), "Notes": meta.get("Notes", "")})
    # Hardware with no schematic ref: the SIP-8 sockets soldered at every Cremat-module site
    # (the modules PLUG IN and are never soldered). Samtec SS-108-TT-2 is Cremat's own
    # eval-board socket (CR-160-R7 BOM lists it as DigiKey SAM1119-08-ND, now 612-SS-108-TT-2-ND);
    # its machined contact accepts 0.38-0.56 mm leads = the modules' 0.51 x 0.25 mm flat pins.
    # All specs live-verified 2026-07-11.
    rows.append({
        "Value": "SIP-8 socket", "Block": "MODULES",
        "Description": "8-pin SIP socket strip under EVERY Cremat module (CR-112/CR-200/CR-210) - solder the socket, plug the module in",
        "Footprint": "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
        "MPN": "SS-108-TT-2", "Manufacturer": "Samtec", "DigiKey_PN": "612-SS-108-TT-2-ND",
        "Qty": 36, "Populate": "FIT", "Unit_Cost_USD": "1.17", "Ext_Cost_USD": "42.12",
        "Stock_Qty": "~650 (DK, 2026-07)", "Package": "SIP-8 THT", "HV_Rating": "-",
        "Datasheet": "https://suddendocs.samtec.com/catalog_english/ss.pdf",
        "Refs": "under U1 .. U47 (36 module sites)",
        "Notes": "Cremat's own eval-board socket (CR-160 BOM SAM1119-08-ND). Machined BeCu contact, tin plating; "
                 "accepts 0.38-0.56 mm leads (module pin 0.51x0.25 mm flat). Hand-solder with a module inserted "
                 "so all 8 sockets align. Verified alt (gold flash, ~3.9k stk): Harwin D01-9970842 "
                 "(DK D01-9970842-ND, $0.75 @ 40). Do NOT sub Mill-Max/Preci-Dip 801-series (0.7-0.9 mm pins only)."})
    # order: FIT first, then by block/value
    rows.sort(key=lambda r: (r["Populate"] == "DNP", r["Block"], r["Value"]))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    fit = sum(r["Qty"] for r in rows if r["Populate"] == "FIT")
    dnpq = sum(r["Qty"] for r in rows if r["Populate"] == "DNP")
    nometa = sorted({r["MPN"] for r in rows
                     if not (sc.get(r["MPN"]) or COMMON_META.get(r["MPN"]) or r["Description"])})
    print("wrote %s: %d line items, %d parts (%d FIT + %d DNP)" % (OUT, len(rows), fit + dnpq, fit, dnpq))
    if nometa: print("  MPNs missing metadata:", nometa)

if __name__ == "__main__":
    main()
