#!/usr/bin/env python3
"""Generate the purchase-ready package from the engineering BOM + verified sourcing.

Reads twelve-channel-bom.csv (netlist-derived) and joins SOURCING (DigiKey/Mouser/vendor
links + live status/price/stock, verified 2026-07-11 by the bom-sourcing-links workflow) to
emit:
  - PURCHASING.md                 human-facing buy sheet (clickable links, cart block, totals)
  - twelve-channel-purchasing.csv machine-readable, with URL columns

Plain Python (no KiCad). Run:  python gen_purchasing.py
"""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
BOM = os.path.join(HERE, "twelve-channel-bom.csv")
MD = os.path.join(HERE, "PURCHASING.md")
CSVOUT = os.path.join(HERE, "twelve-channel-purchasing.csv")
VERIFIED = "2026-07-11"

# ---- verified sourcing, keyed by MPN (from the bom-sourcing-links workflow, 2026-07-11) ----
# price = live DigiKey qty-1 USD. All DigiKey PNs confirmed Active on the product page unless noted.
SRC = {
 "RC0805FR-0749R9L": dict(dk="311-49.9CRCT-ND", url="https://www.digikey.com/en/products/detail/yageo/RC0805FR-0749R9L/727984", price="0.10", stock="358,924", status="Active", mpn_url="", mou="603-RC0805FR-0749R9L", mou_url="https://www.mouser.com/ProductDetail/YAGEO/RC0805FR-0749R9L"),
 "RC0805JR-070RL": dict(dk="311-0.0ARCT-ND", url="https://www.digikey.com/en/products/detail/yageo/RC0805JR-070RL/731163", price="0.10", stock="1,165,597", status="Active", mou="603-RC0805JR-070RL", mou_url="https://www.mouser.com/ProductDetail/YAGEO/RC0805JR-070RL"),
 "RC0805FR-0710KL": dict(dk="311-10.0KCRCT-ND", url="https://www.digikey.com/en/products/detail/yageo/RC0805FR-0710KL/730482", price="0.10", stock="3,586,722", status="Active", mou="603-RC0805FR-0710KL", mou_url="https://www.mouser.com/ProductDetail/YAGEO/RC0805FR-0710KL"),
 "RC0805JR-074R7L": dict(dk="311-4.7ARCT-ND", url="https://www.digikey.com/en/products/detail/yageo/RC0805JR-074R7L/731273", price="0.10", stock="~142,966", status="Active", mou="603-RC0805JR-074R7L", mou_url="https://www.mouser.com/ProductDetail/YAGEO/RC0805JR-074R7L"),
 "RC0805JR-0747RL": dict(dk="311-47ARCT-ND", url="https://www.digikey.com/en/products/detail/yageo/RC0805JR-0747RL/728335", price="0.10", stock="95,764", status="Active", mou="603-RC0805JR-0747RL", mou_url="https://www.mouser.com/ProductDetail/YAGEO/RC0805JR-0747RL"),
 "RC0805FR-07976RL": dict(dk="311-976CRCT-ND", url="https://www.digikey.com/en/products/detail/yageo/RC0805FR-07976RL/728214", price="0.10", stock="48,730", status="Active", mou="603-RC0805FR-07976RL", mou_url="https://www.mouser.com/ProductDetail/YAGEO/RC0805FR-07976RL"),
 "C0805C224K1RACTU": dict(dk="399-C0805C224K1RACTUCT-ND", url="https://www.digikey.com/en/products/detail/kemet/C0805C224K1RACTU/2211772", price="0.49", stock="~95k", status="Active", mou="80-C0805C224K1RAC", mou_url="https://www.mouser.com/ProductDetail/KEMET/C0805C224K1RACTU", note="PRIMARY since 2026-07-11 (Murata GRM21AR72A224KAC5K went DK 0-stock, 17-wk lead; Murata = equal-spec alt via Mouser 81-GRM21AR72A224KAC5K). 100V X7R 0805 HV coupling."),
 "CL21B104KCFNNNE": dict(dk="1276-6840-1-ND", url="https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL21B104KCFNNNE/5961324", price="0.10", stock="566,243", status="Active", mou="187-CL21B104KCFNNNE", mou_url="https://www.mouser.com/ProductDetail/Samsung-Electro-Mechanics/CL21B104KCFNNNE"),
 "C0805C106K3PACTU": dict(dk="399-11939-1-ND", url="https://www.digikey.com/en/products/detail/kemet/C0805C106K3PACTU/5267604", price="0.23", stock="253,633", status="Active", mou="C0805C106K3PACTU", mou_url="https://www.mouser.com/ProductDetail/KEMET/C0805C106K3PACTU"),
 "CC0805CRNPO9BN1R0": dict(dk="311-1089-1-ND", url="https://www.digikey.com/en/products/detail/yageo/CC0805CRNPO9BN1R0/302823", price="0.11", stock="43,415", status="Active", mou="", mou_url="https://www.mouser.com/c/?q=CC0805CRNPO9BN1R0"),
 "EEE-FN1V471UP": dict(dk="10-EEE-FN1V471UPCT-ND", url="https://www.digikey.com/en/products/detail/panasonic-industry/EEE-FN1V471UP/11657045", price="1.17", stock="2,569", status="Active", mou="667-EEE-FN1V471UP", mou_url="https://www.mouser.com/ProductDetail/Panasonic/EEE-FN1V471UP"),
 "1812L110/24DR": dict(dk="F5632CT-ND", url="https://www.digikey.com/en/products/detail/littelfuse-inc/1812L110-24DR/2520731", price="0.78", stock="1,503", status="Active", mou="576-1812L110/24DR", mou_url="https://www.mouser.com/ProductDetail/Littelfuse/1812L110-24DR"),
 "SSA24": dict(dk="SSA24CT-ND", url="https://www.digikey.com/en/products/detail/onsemi/SSA24/5305051", price="0.84", stock="15,991", status="Active", mou="512-SSA24", mou_url="https://www.mouser.com/ProductDetail/onsemi-Fairchild/SSA24"),
 "THS3491IDDAT": dict(dk="296-49085-1-ND", url="https://www.digikey.com/en/products/detail/texas-instruments/THS3491IDDAT/9091882", price="18.28", stock="680", status="Active", mou="595-THS3491IDDAT", mou_url="https://www.mouser.com/c/?q=THS3491IDDAT", note="CUT TAPE 296-49085-1-ND ($18.28 q1). Do NOT order 296-49085-2-ND - that is a 250-pc reel (~$3k). TI-direct: ti.com THS3491IDDAT."),
 "CONMCX013": dict(dk="343-CONMCX013-ND", url="https://www.digikey.com/en/products/detail/te-connectivity-linx/CONMCX013/13245481", price="3.22", stock="1,050", status="Active", mou="CONMCX013-T", mou_url="https://www.mouser.com/ProductDetail/Linx-Technologies/CONMCX013-T", note="Board fp is -T (tape&reel packaging of same jack). TE-direct: te.com CONMCX013."),
 "1715734": dict(dk="277-1264-ND", url="https://www.digikey.com/en/products/detail/phoenix-contact/1715734/260632", price="1.71", stock="1,986", status="Active", mou="651-1715734", mou_url="https://www.mouser.com/ProductDetail/Phoenix-Contact/1715734"),
 "3296W-1-204LF": dict(dk="3296W-204LF-ND", url="https://www.digikey.com/en/products/detail/bourns-inc/3296W-1-204LF/1088052", price="2.44", stock="80 (DK; ~1.5k Mouser, 19 wk DK lead)", status="Active", mou="652-3296W-1-204LF", mou_url="https://www.mouser.com/ProductDetail/Bourns/3296W-1-204LF"),
 "SS-108-TT-2": dict(dk="612-SS-108-TT-2-ND", url="https://www.digikey.com/en/products/detail/samtec-inc/SS-108-TT-2/1105712", price="1.17", stock="649 (DK; ~4.4k all distys)", status="Active", mou="200-SS108TT2", mou_url="https://www.mouser.com/ProductDetail/Samtec/SS-108-TT-2", note="SIP-8 socket under every Cremat module (solder socket, plug module). Cremat's own eval-board part (CR-160 BOM SAM1119-08-ND). $1.37 (1) / $1.17 (10-99) / $0.99 (100+). Verified alt: Harwin D01-9970842 (gold flash, DK D01-9970842-ND, ~3.9k stk, $0.75 @ 40). Mouser has only 6 pcs - buy from DigiKey."),
 # Cremat-direct modules (not distributor-stocked)
 "CR-112-R2.1": dict(dk="", url="https://www.cremat.com/home/charge-sensitive-preamplifiers/", price="55.00", stock="made-to-order", status="Cremat-direct", cremat=True, breaks="2026-01 list: $65 (1-9) / $55 (10-99) / $47 (100+); qty 12 = $55"),
 "CR-200-1us-R2.1": dict(dk="", url="https://www.cremat.com/home/cr-200-x-shaper-modules/", price="55.00", stock="made-to-order", status="Cremat-direct", cremat=True, breaks="2026-01 list: $65 (1-9) / $55 (10-99) / $47 (100+); qty 12 = $55"),
 "CR-210-R0": dict(dk="", url="https://www.cremat.com/home/cr-210-baseline-restorer-blr/", price="77.00", stock="made-to-order", status="Cremat-direct", cremat=True, breaks="2026-01 list: $86 (1-9) / $77 (10-99) / $73.10 (100+); qty 12 = $77"),
}

# enclosure: 1U, ONE CASE PER BOARD (was 2U holding a stacked pair). Vented covers chosen
# because the board dissipates ~13.4 W (+584/-536 mA on +/-12 V) inside a 40 mm-tall box.
# All dims verified against the factory drawing 2026-07-11 (hammfg.com/files/parts/pdf/RM1U1908VBK.pdf):
# internal depth 196.85 mm [7.750] EXACT, internal height 40.09 mm [1.578], internal width 415.30 mm;
# front/rear panels are separate flat 3.2 mm plates, removable & interchangeable (machine the MCX
# holes off-chassis; assemble by sliding a panel on over the jack barrels). Module stack incl.
# SIP-8 socket tops out ~32 mm above the case floor -> ~8 mm clearance under the top cover.
CASE = dict(mpn="RM1U1908VBK", mfr="Hammond Manufacturing", dk="HM1004-ND",
    url="https://www.digikey.com/en/products/detail/hammond-manufacturing/RM1U1908VBK/2094741",
    price="169.21", stock="70 (+26 factory)", status="Active", mou="546-RM1U1908VBK",
    mou_url="https://www.mouser.com/ProductDetail/Hammond-Manufacturing/RM1U1908VBK",
    vendor_url="https://www.hammfg.com/part/RM1U1908VBK",
    note="1U 19-in rack case, VENTED black (Ø4.3 mm holes, 7.9 mm pitch - EMI-negligible apertures in the "
         "1.6k-130 kHz signal band, needed for the ~13 W dissipation). ONE case per 12-ch board. "
         "Ext 203.2 D x 421.6 W x 43.7 H mm; internal depth 196.85 mm / height 40.09 mm / width 415.30 mm "
         "(factory drawing, verified 2026-07-11). Solid-cover alt: RM1U1908SBK (DK HM995-ND, $162.45, 123 stk). "
         "13-in-deep alt if ever needed: RM1U1913SBK. Board W vs 196.85 mm interior sets the MCX recess at the "
         "panels - see design/SESSION_LOG.md session 13. Mount on standoffs off the bottom cover (no PCB bosses).")


def money(x):
    try: return float(str(x).split()[0])
    except Exception: return 0.0


def dklink(s):
    if s.get("cremat"): return "Cremat-direct"
    return f"[{s['dk']}]({s['url']})" if s.get("dk") else (f"[search]({s.get('url','')})" if s.get("url") else "-")


def moulink(s):
    if s.get("mou_url"): return f"[{s['mou'] or 'link'}]({s['mou_url']})"
    return "-"


def main():
    rows = list(csv.DictReader(open(BOM, newline="", encoding="utf-8")))
    for r in rows:
        r["_src"] = SRC.get(r["MPN"], {})
        r["_price"] = money(r["_src"].get("price") or r.get("Unit_Cost_USD"))
        r["_ext"] = r["_price"] * int(r["Qty"])

    fit = [r for r in rows if r["Populate"] == "FIT"]
    dnp = [r for r in rows if r["Populate"] == "DNP"]
    cremat = [r for r in fit if r["_src"].get("cremat")]
    catalog = [r for r in fit if not r["_src"].get("cremat")]

    def order(rs):  # Cremat modules first-costly, then by ext desc
        return sorted(rs, key=lambda r: (-r["_ext"], r["Value"]))

    fit_total = sum(r["_ext"] for r in fit)
    dnp_total = sum(r["_ext"] for r in dnp)
    cat_total = sum(r["_ext"] for r in catalog)
    crem_total = sum(r["_ext"] for r in cremat)
    case_price = money(CASE["price"])

    L = []
    L.append("# Purchase-ready BOM — 12-channel Cremat amplifier (`twelve-channel`)\n")
    L.append(f"> Sourcing verified **{VERIFIED}** (DigiKey PNs/prices/stock read live; Mouser second-source "
             "URLs confirmed, some prices distributor-blocked from scraping). Prices are **DigiKey qty-1 USD** "
             "— passives are far cheaper at strip/reel quantities. Generated by `gen_purchasing.py` from "
             "`twelve-channel-bom.csv`.\n")
    L.append("**Board:** 213.2 x 334.7 mm, 4-layer, 500 placed parts incl. sockets. **One 1U case per board** "
             "(daisy-chained power).\n")

    # ---- cost summary ----
    L.append("## Cost summary (one board)\n")
    L.append("| Group | Qty (parts) | Subtotal (qty-1) |")
    L.append("|---|--:|--:|")
    L.append(f"| Cremat modules (CR-112 / CR-200 / CR-210) | {sum(int(r['Qty']) for r in cremat)} | ${crem_total:,.2f} |")
    L.append(f"| DigiKey/Mouser catalog parts (FIT) | {sum(int(r['Qty']) for r in catalog)} | ${cat_total:,.2f} |")
    L.append(f"| **Default build subtotal (FIT only)** | **{sum(int(r['Qty']) for r in fit)}** | **${fit_total:,.2f}** |")
    L.append(f"| Optional output-buffer block (THS3491 + 976R, DNP) | {sum(int(r['Qty']) for r in dnp if r['Block']=='BUFFER')} | ${sum(r['_ext'] for r in dnp if r['Block']=='BUFFER'):,.2f} |")
    L.append(f"| Other DNP (variant jumpers/spares) | {sum(int(r['Qty']) for r in dnp if r['Block']!='BUFFER')} | ${sum(r['_ext'] for r in dnp if r['Block']!='BUFFER'):,.2f} |")
    L.append(f"| Enclosure (Hammond {CASE['mpn']}, ONE per board) | 1 | ${case_price:,.2f} |")
    L.append("")
    L.append(f"- **One board, default build + case share:** ~${fit_total + case_price/2:,.2f} "
             f"(${fit_total:,.2f} parts + half a ${case_price:,.0f} case).")
    L.append(f"- **Fully buffered board (add THS3491 block):** ~${fit_total + sum(r['_ext'] for r in dnp if r['Block']=='BUFFER'):,.2f} parts.")
    L.append("- The BOM is **Cremat-module dominated** (~%.0f%% of parts cost); passives are noise.\n"
             % (100 * crem_total / fit_total))

    # ---- Cremat table ----
    L.append("## 1. Cremat modules — order direct from Cremat Inc\n")
    L.append("Not DigiKey/Mouser parts. Order at [cremat.com](https://www.cremat.com/ordering/united-states/): "
             "**Amazon** store for <=10 pcs, or **email** Cremat (info@cremat.com — verify on site; one page lists "
             "Cremat.Inc@gmail.com) with PNs+qty for >10 pcs; they invoice (card). Ph +1 617-527-6590. "
             "**Long lead — order these first.**\n")
    L.append("| Value | MPN | Qty | $ea (q1) | $ext | Qty breaks | Product page |")
    L.append("|---|---|--:|--:|--:|---|---|")
    for r in order(cremat):
        s = r["_src"]
        L.append(f"| {r['Value']} | {r['MPN']} | {r['Qty']} | ${r['_price']:.2f} | ${r['_ext']:,.2f} | {s.get('breaks','')} | [{('cremat.com')}]({s['url']}) |")
    L.append("")

    # ---- catalog table ----
    L.append("## 2. DigiKey / Mouser catalog parts (default-populated)\n")
    L.append("| Value | MPN | DigiKey PN | Qty | $ea | $ext | Mouser | Stock | Notes |")
    L.append("|---|---|---|--:|--:|--:|---|--:|---|")
    for r in order(catalog):
        s = r["_src"]
        L.append(f"| {r['Value']} | {r['MPN']} | {dklink(s)} | {r['Qty']} | ${r['_price']:.2f} | ${r['_ext']:,.2f} "
                 f"| {moulink(s)} | {s.get('stock','')} | {s.get('note','')} |")
    L.append("")

    # ---- DNP table ----
    L.append("## 3. Not-populated by default (buffer option + variant jumpers)\n")
    L.append("The **output buffer** (THS3491 + 976R Rf) is DNP — bypassed by a 0R jumper. Populate the whole "
             "block for the +2 gain stage (OUT_50 ~134 mV/pC vs ~67 mV/pC bypassed). Other DNP rows are the "
             "filter-bypass / spare passives.\n")
    L.append("| Value | MPN | DigiKey PN | Qty | $ea | $ext | Block | Notes |")
    L.append("|---|---|---|--:|--:|--:|---|---|")
    for r in sorted(dnp, key=lambda r: (r["Block"] != "BUFFER", -r["_ext"])):
        s = r["_src"]
        L.append(f"| {r['Value']} | {r['MPN']} | {dklink(s)} | {r['Qty']} | ${r['_price']:.2f} | ${r['_ext']:,.2f} "
                 f"| {r['Block']} | {s.get('note','')} |")
    L.append("")

    # ---- enclosure ----
    L.append("## 4. Enclosure — Hammond 2U rack case (one per two stacked boards)\n")
    L.append(f"- **Order:** {CASE['mfr']} **{CASE['mpn']}** — DigiKey [{CASE['dk']}]({CASE['url']}) "
             f"**${CASE['price']}** ({CASE['stock']} in stock) · Mouser [{CASE['mou']}]({CASE['mou_url']}) "
             f"· Hammond [part page]({CASE['vendor_url']}).")
    L.append(f"- {CASE['note']}\n")

    # ---- DigiKey cart paste block ----
    L.append("## 5. DigiKey quick-add (default build, one board)\n")
    L.append("Paste into DigiKey **myLists > Quick Add** (`PN, qty` per line). Buffer parts omitted (DNP); "
             "add `296-49085-1-ND, 12` and `311-976CRCT-ND, 24` if populating the buffer. Passive qtys are "
             "exact-fit — pad for spares / buy strips.\n")
    L.append("```")
    for r in order(catalog):
        s = r["_src"]
        if s.get("dk"):
            L.append(f"{s['dk']}, {r['Qty']}")
    L.append(f"{CASE['dk']}, 1")
    L.append("```")
    L.append("")
    L.append("_Cremat modules (CR-112 x12, CR-200-1us x12, CR-210 x12) are ordered separately from cremat.com._\n")

    open(MD, "w", encoding="utf-8").write("\n".join(L))

    # ---- purchasing CSV ----
    cols = ["Value", "MPN", "Manufacturer", "Populate", "Block", "Qty", "DigiKey_PN", "DigiKey_URL",
            "DigiKey_Price_qty1_USD", "DigiKey_Stock", "Status", "Mouser_PN", "Mouser_URL",
            "Ext_Cost_USD", "Footprint", "Refs", "Notes"]
    with open(CSVOUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows:
            s = r["_src"]
            w.writerow({"Value": r["Value"], "MPN": r["MPN"], "Manufacturer": r["Manufacturer"],
                "Populate": r["Populate"], "Block": r["Block"], "Qty": r["Qty"],
                "DigiKey_PN": s.get("dk", ""), "DigiKey_URL": s.get("url", ""),
                "DigiKey_Price_qty1_USD": r["_price"], "DigiKey_Stock": s.get("stock", ""),
                "Status": s.get("status", ""), "Mouser_PN": s.get("mou", ""), "Mouser_URL": s.get("mou_url", ""),
                "Ext_Cost_USD": "%.2f" % r["_ext"], "Footprint": r["Footprint"], "Refs": r["Refs"],
                "Notes": (r["_src"].get("note", "") or r["Notes"])[:200]})
        w.writerow({"Value": "ENCLOSURE (one per board)", "MPN": CASE["mpn"], "Manufacturer": CASE["mfr"],
            "Populate": "FIT", "Block": "MECH", "Qty": 1, "DigiKey_PN": CASE["dk"], "DigiKey_URL": CASE["url"],
            "DigiKey_Price_qty1_USD": CASE["price"], "DigiKey_Stock": CASE["stock"], "Status": CASE["status"],
            "Mouser_PN": CASE["mou"], "Mouser_URL": CASE["mou_url"], "Ext_Cost_USD": CASE["price"],
            "Footprint": "", "Refs": "", "Notes": CASE["note"][:200]})

    print("wrote %s + %s" % (os.path.basename(MD), os.path.basename(CSVOUT)))
    print("  default-build FIT subtotal (qty-1): $%,.2f  (Cremat $%,.2f + catalog $%,.2f)".replace("$%,", "$%")
          % (fit_total, crem_total, cat_total))
    print("  + buffer option: $%.2f ; enclosure: $%.2f" %
          (sum(r["_ext"] for r in dnp if r["Block"] == "BUFFER"), case_price))
    miss = sorted({r["MPN"] for r in rows if not r["_src"]})
    if miss: print("  MPNs with no verified sourcing:", miss)


if __name__ == "__main__":
    main()
