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
        meta = sc.get(mpn) or COMMON_META.get(mpn) or {}
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
    # order: FIT first, then by block/value
    rows.sort(key=lambda r: (r["Populate"] == "DNP", r["Block"], r["Value"]))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    fit = sum(r["Qty"] for r in rows if r["Populate"] == "FIT")
    dnpq = sum(r["Qty"] for r in rows if r["Populate"] == "DNP")
    nometa = sorted({r["MPN"] for r in rows if not (sc.get(r["MPN"]) or COMMON_META.get(r["MPN"]))})
    print("wrote %s: %d line items, %d parts (%d FIT + %d DNP)" % (OUT, len(rows), fit + dnpq, fit, dnpq))
    if nometa: print("  MPNs missing metadata:", nometa)

if __name__ == "__main__":
    main()
