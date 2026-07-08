# Single-channel BOM — sourcing & lifecycle verification (2026-07-07)

Distributor/lifecycle sweep of **all 19 distinct MPNs** in
[`single-channel-bom.csv`](single-channel-bom.csv). Every status/stock/price claim below
was read from a distributor or manufacturer page actually fetched on 2026-07-07 (URLs in the
last column). Prices are qty-1 list unless a break is noted; stock figures are page snapshots
(round numbers). Digi-Key is the primary distributor (project standard); cremat.com is
authoritative for the three made-to-order Cremat modules.

## 1. Per-MPN verification table

| MPN | Value / Role | Mfr status | Distributor + PN | Stock | $ q1 | $ q25/100 | Source URL(s) | Verdict |
|---|---|---|---|---|---|---|---|---|
| **CR-112-R2.1** | Cremat CSP module | Current catalog (Cremat-direct) | Cremat.com (made-to-order) | m-t-o | $65 (1-24) | $59 (25+) | cremat.com/ordering/united-states/us-prices-and-ordering-information/ ; cremat.com/home/charge-sensitive-preamplifiers/ | ✅ Active catalog; not a distributor part |
| **CR-200-1us-R2.1** | Cremat 1µs shaper | Current catalog | Cremat.com (m-t-o) | m-t-o | $59 (1-24) | $55 (25+) | cremat.com/us-prices… ; cremat.com/home/cr-200-x-shaper-modules/ | ✅ Active catalog |
| **CR-210-R0** | Cremat BLR (optional) | Current catalog | Cremat.com (m-t-o) | m-t-o | $77 (1-24) | $69 (25+) | cremat.com/us-prices… ; cremat.com/home/cr-210-baseline-restorer-blr/ | ✅ Active catalog |
| **THS3491IDDAT** | Output buffer CFA | **Active** (TI, 26-wk factory lead) | Digi-Key **296-49085-2-ND** | ~690 | $18.28 | $13.60 q25 / $12.67 q100 | digikey.com/en/products/detail/texas-instruments/THS3491IDDAT/9091882 | ✅ Active, in stock |
| **RC0805FR-07976RL** | 976 Ω 1% (Rfb, Rgain) | **Active** | Digi-Key **311-976CRCT-ND** | ~48.7k | $0.10 | — | digikey.com/en/products/detail/yageo/RC0805FR-07976RL/237962 | ✅ suffix confirmed |
| **RC0805FR-0749R9L** | 49.9 Ω 1% (R_OUT) | **Active** | Digi-Key **311-49.9CRCT-ND** | ~360k | $0.10 | — | digikey.com/en/products/detail/yageo/RC0805FR-0749R9L/727984 | ✅ |
| **RC0805FR-0710KL** | 10 kΩ 1% (Rf1, Rf2) | **Active** | Digi-Key **311-10.0KCRCT-ND** | ~3.67M | $0.10 | — | digikey.com/en/products/detail/yageo/RC0805FR-0710KL/727535 | ✅ |
| **CL21B104KCC5PNC** | 0.1 µF 100 V X7R (**Cf**, HV) | **NRND** (Samsung, Not-For-New-Designs) | Digi-Key 1276-2447-1-ND | ~11.6k | $0.23 | $0.082 q100 | digikey.com/en/products/detail/CL21B104KCC5PNC/1276-2447-1-ND/3890533 | ⚠️ **NRND → replace** (see §2) |
| **GRM21AR72A224KAC5K** | 0.22 µF 100 V X7R (**Cc**, HV) | **Active** | Digi-Key **490-8306-1-ND** | ~94k | $0.24 | $0.087 q100 | digikey.com/en/products/detail/murata-electronics/GRM21AR72A224KAC5K/2546586 | ✅ gap closed (was "490-… verify") |
| **RC0805JR-070RL** | 0 Ω jumper (JP_Rf1/2, JP_BLR) | **Active** | Digi-Key **311-0.0ARCT-ND** | ~1.2M | $0.10 | — | digikey.com/en/products/detail/yageo/RC0805JR-070RL/728216 | ✅ |
| **3296W-1-204LF** | 200 kΩ 25-turn trimpot (R_PZ) | **Active** | Digi-Key **3296W-204LF-ND** | ~95 (LOW) | $2.44 | $1.89 q25 / $1.69 q100 | digikey.com/product-detail/en/bourns-inc/3296W-1-204LF/3296W-204LF-ND/1088052 | ✅ Active; ⚠ thin stock — see §2 |
| **RC0805JR-074R7L** | 4.7 Ω rail R (×8) | **Active** | Digi-Key **311-4.7ARCT-ND** | ~143k | $0.10 | — | digikey.com/product-detail/en/RC0805JR-074R7L/311-4.7ARCT-ND/731273 | ✅ |
| **CL21B104KBCNNNC** | 0.1 µF 50 V X7R decoupling (×8) | **Active** | Digi-Key **1276-1003-1-ND** | ~7.8M | $0.10 | $0.022 q100 | digikey.com/en/products/detail/samsung-electro-mechanics/CL21B104KBCNNNC/3886661 | ✅ **PN corrected** (was 1276-1000-1-ND = a 0603 part) |
| **CL21A106KAYNNNE** | 10 µF 25 V X5R bulk (×8) | **Active** but **0 stock** (16-wk lead) | Digi-Key **1276-2891-1-ND** | 0 | $0.18 | $0.0625 q100 | digikey.com/en/products/detail/samsung-electro-mechanics/CL21A106KAYNNNE/3888549 | ⚠️ **PN corrected** (was 1276-1037-1-ND) + stock risk — see §2 |
| **UWT1V101MCL1GS** | 100 µF 35 V electrolytic (Cbulk) | **Active** | Digi-Key **493-2203-1-ND** | ~331k | $0.42 | $0.168 q100 | digikey.com/en/products/detail/nichicon/UWT1V101MCL1GS/589944 | ✅ |
| **CONMCX013** | MCX edge jack (×4) | **Active** (4-wk lead) | Digi-Key **343-CONMCX013-ND** | ~1,050 | $3.22 | ~$3.13 q250 | digikey.com/en/products/detail/te-connectivity-linx/CONMCX013/13245481 | ✅ |
| **1715734** | Phoenix 3-pos screw terminal (J_PWR) | **Active** | Digi-Key **277-1264-ND** | ~2,031 | $1.71 | (q10 $1.40) | digikey.com/product-detail/en/phoenix-contact/1715734/277-1264-ND/260632 | ✅ |
| **CC0805CRNPO9BN1R0** | 1 pF 50 V C0G (Ctest) | **Active** | Digi-Key **311-1089-1-ND** | ~47.5k | $0.11 | — | digikey.com/en/products/detail/yageo/CC0805CRNPO9BN1R0/302823 | ✅ **PN corrected** (was malformed "311-CC0805CRNPO9BN1R0CT-ND") |
| **RC0805JR-0747RL** | 47 Ω (R_test) | **Active** | Digi-Key **311-47ARCT-ND** | ~101k | $0.10 | — | digikey.com/en/products/detail/yageo/RC0805JR-0747RL/728335 | ✅ |

**Tally:** 19 distinct MPNs — **18 Active** (16 in-stock now; the 10 µF bulk is Active but
currently 0 DK stock; the Bourns trimpot is Active but low stock) + **1 NRND** (Cf). The three
Cremat modules are confirmed current catalog products with prices matching the BOM exactly and
revision suffixes (-R2.1, -R2.1, -R0) matching what Cremat currently ships. **No fully obsolete
distributor part** other than the already-documented EL5167 (which is not in this BOM — it was
replaced by THS3491 before this sweep).

## 2. Obsolete / at-risk parts + recommended replacements

### 2a. NRND — `Cf` = Samsung CL21B104KCC5PNC (0.1 µF **100 V** X7R 0805) — HV-critical
- **Finding:** Digi-Key marks this **NRND (Not For New Designs)**; stock is depleting (~11.6k).
  It sits in the **SiPM bias filter shunt** — an **HV node**, so any replacement **must stay
  ≥100 V** (Iron Rule 4).
- **Recommended drop-in:** **Samsung `CL21B104KCFNNNE`** — 0.1 µF **100 V** X7R 0805,
  **Active**, Digi-Key **1276-6840-1-ND**, **~552k in stock**, **$0.10 q1 / $0.024 q100**.
  Verified: digikey.com/en/products/detail/samsung-electro-mechanics/CL21B104KCFNNNE/5961324.
  Same value/package/dielectric/voltage → **no schematic or footprint change** (identical
  0805, 100 V X7R). Also **cheaper** than the NRND part.
- **Action taken:** CSV `Cf` row keeps the original MPN (design-owning session decides the
  swap) with its `Notes` updated to OBSOLETE/NRND + the replacement PN, per the project rule
  not to silently swap design-critical MPNs. **Recommendation to the design session: adopt
  CL21B104KCFNNNE for Cf.**

### 2b. Active-but-out-of-stock — 10 µF 25 V X5R bulk = Samsung CL21A106KAYNNNE (×8)
- **Finding:** Part is **Active** but Digi-Key shows **0 stock, 16-week factory lead** today.
  Not an obsolescence, but a build-availability risk for the local-bulk cap on every rail
  (used ×8 in one channel, ×96 across the 12-channel board).
- **In-stock equal-spec alternate:** **Taiyo Yuden `TMK212BBJ106KG-T`** — 10 µF 25 V X5R 0805
  ±10%, **Active**, Digi-Key **587-2985-1-ND**, ~753 in stock, ~$0.17 q1 / ~$0.059 q100
  (digikey.com/product-detail/en/taiyo-yuden/TMK212BBJ106KG-T/587-2985-1-ND/2714178).
  Murata GRM21BR61E106KA73L and TDK C2012X5R1E106K125AB are also Active but likewise
  0-stock/backorder today — the Taiyo Yuden part is the one currently orderable.
- **Action taken:** CSV rows corrected to the real DK PN **1276-2891-1-ND** and `Stock_Qty`
  flagged "0 DK-stock 2026-07 (16wk lead)". **This cap is not HV-critical** (25 V rail bulk),
  so the design session may either keep the Samsung PN and reorder, or substitute the Taiyo
  Yuden part for immediate builds.
- **RESOLVED 2026-07-08 — fitted part swapped to KEMET `C0805C106K3PACTU`** (DK **399-11939-1-ND**,
  10 µF 25 V X5R ±10% 0805, drop-in). Re-verified in-stock on Digi-Key: **~255,000 units**,
  **Active** (no NRND), $0.23 q1 / **$0.0833 q100** — deep, cheap, jellybean, best of the
  candidates (Taiyo Yuden 587-2985-1-ND was in stock but only ~600 pcs; TDK's stocked 10 µF is
  NRND; Murata/Yageo were 0-stock). Value-only swap in `gen_sch.py` + the 8 CSV bulk rows; the
  0805 footprint and PCB are unchanged. **Alternates kept:** Samsung CL21A106KAYNNNE
  (1276-2891-1-ND, the original, currently 0-stock) and same-mfr Samsung CL21A106KACLRNC
  (1276-2397-1-ND, ~71 k in stock).

### 2c. Low-stock watch (not obsolete, no substitution required)
- **Bourns 3296W-1-204LF** 200 kΩ trimpot (`R_PZ`): Active, but only ~95 pcs in Digi-Key
  stock. Fine for the single channel; for the ×12 board (12+ trimpots) source ahead or draw on
  Mouser/Newark (identical MPN) — normal factory lead, no lifecycle concern.

## 3. Gaps closed (previously-unverified fields now pinned)

| Field (was) | Now (confirmed) | Source |
|---|---|---|
| `Cc` DigiKey_PN = "490-GRM21AR72A224KAC5K (verify)" | **490-8306-1-ND** (Active, ~94k, $0.24 q1) | digikey.com/…/GRM21AR72A224KAC5K/2546586 |
| `Cc` equal-spec alternate PN (unpinned; report's TDK "CGA4J3X7T2A224K125AE" did **not** resolve on Digi-Key) | **KEMET C0805C224K1RACTU** = DK **399-C0805C224K1RACTUCT-ND** (Active, ~98k, 0.22µF/100V/X7R/0805) | digikey.com/…/kemet/C0805C224K1RACTU/2212302 |
| `Rfb`/`Rgain` DigiKey_PN = "311-976CRCT-ND (verify suffix)" | **311-976CRCT-ND** confirmed (Active, ~48.7k) | digikey.com/…/RC0805FR-07976RL/237962 |
| `0.1 µF 50 V` DigiKey_PN = 1276-1000-1-ND (**wrong** — that PN is a 0603 CL10B104KB8NNNC) | **1276-1003-1-ND** (0805, 50 V, Active, ~7.8M) | digikey.com/…/CL21B104KBCNNNC/3886661 |
| `10 µF 25 V` DigiKey_PN = 1276-1037-1-ND (unverifiable) | **1276-2891-1-ND** (0805, 25 V, Active, 0 stk) | digikey.com/…/CL21A106KAYNNNE/3888549 |
| `Ctest 1 pF` DigiKey_PN = "311-CC0805CRNPO9BN1R0CT-ND" (malformed) | **311-1089-1-ND** (Active, ~47.5k) | digikey.com/…/CC0805CRNPO9BN1R0/302823 |
| Cremat module lead time (unstated) | Cremat publishes **no lead time**; fulfillment via Amazon (≤10 pcs) or invoice/email for bulk — consistent with made-to-order. Prices/revisions match BOM. | cremat.com/ordering/united-states/us-prices-and-ordering-information/ |

## 4. Notes on method / caveats
- The Bourns q25/q100 breaks ($1.89 / $1.69), the Nichicon q100 ($0.168) and CONMCX013 q250
  ($3.13) were read from their Digi-Key pages; the Phoenix page only surfaced q1/q10.
- `Cc` unit cost in the CSV was updated $0.30 → **$0.24** (verified q1). The report §1 cost
  roll-up was **not** recomputed — the delta (a few cents on the passive subtotal, which is
  dwarfed by the $201 of Cremat modules + $18.28 buffer) is immaterial and rounding-level.
- No page was unreachable except a single transient Mouser ECONNRESET on the 10 µF part;
  its status was taken from the successfully-fetched Digi-Key page instead.
- Design-source files (`gen_sch.py`, `.kicad_sch/.kicad_pcb`) were **not touched** — this
  session only edited the BOM CSV, this file, and `BOM-REPORT.md`. The Cf-replacement and
  10 µF-alternate recommendations are logged here for the design-owning session to action.
- **CSV data-integrity fix:** the `Cbp2` row (CR-210 +Vs 0.1 µF decoupling) had two columns
  misaligned — `Symbol_FP_3D_Source` held "FIT" and `Populate_Default` held "DNP when bypassed"
  (one field shifted vs. its correct `Cbn2` counterpart). Realigned to
  `Symbol_FP_3D_Source = "KiCad Device:C + C_0805 + 3D"`, `Populate_Default = FIT`, DNP note
  moved to `Notes` — so all 48 rows now parse to the 17-column schema. Values unchanged.
