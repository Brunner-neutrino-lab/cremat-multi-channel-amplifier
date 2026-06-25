# CSP CR-112 eval board — Models-BOM parts report (Track A3)

Real, in-stock, economical Digi-Key parts for the **single-channel CR-112 CSP eval board +
SiPM bias front-end**. This is the **real-parts gate** output: the Design track (A1) swaps
its generic values to the chosen MPNs below 1:1, and the Sim track (A2) updates only
value-sensitive model params. Machine-readable copy: [`csp-cr112-bom.csv`](csp-cr112-bom.csv).

> **Board scope (Phase A, csp-cr112 only):** CR-112 + bias front-end + per-rail decoupling +
> 4× MCX + power terminal. The shaper (CR-200), CR-210 BLR, and output buffer (EL5167) are
> **NOT on this board** — they belong to sub-component A4 / Phase B and are out of this BOM.

## Sourcing method / caveat

Digi-Key direct browsing returns **HTTP 403** to automated requests, so unit prices/stock
below are from **WebSearch + manufacturer/distributor pages + the Cremat US price list**, with
the Digi-Key PN cited for ordering. Prices are representative single-unit USD (qty 1) and round
up at small quantities; treat them as budgetary, not a live quote. All passive prices are
jellybean-tier (sub-$0.15 ea in reels). **Verify the live Digi-Key cart before ordering.**

## BOM (single channel)

| Ref | Value | MPN | Mfr | Digi-Key PN | $/ea (qty1) | Pkg | HV | Populate |
|---|---|---|---|---|---|---|---|---|
| U_CSP | CR-112 | CR-112-R2.1 | Cremat | *(not DK — see below)* | **65.00** | SIP-8 THT | — | FIT |
| Rf1, Rf2 | 10 kΩ 1% | RC0805FR-0710KL | Yageo | 311-10.0KCRCT-ND | 0.10 | 0805 | — | FIT |
| Cf | 100 nF **100 V** X7R | CL21B104KCC5PNC | Samsung | 1276-2447-1-ND | 0.10 | 0805 | **100 V** | FIT |
| Cc | 0.22 µF **100 V** X7R | GRM21AR72A224KAC5K | Murata | 490-… *(verify)* | 0.30 | 0805 | **100 V** | FIT |
| JP_Rf1, JP_Rf2 | 0 Ω | RC0805JR-070RL | Yageo | 311-0.0ARCT-ND | 0.10 | 0805 | — | **DNP** |
| Rdec_P, Rdec_N | 4.7 Ω 5% | RC0805JR-074R7L | Yageo | 311-4.7ARCT-ND | 0.10 | 0805 | — | FIT |
| Cdec_P10, Cdec_N10 | 10 µF 25 V X5R | CL21A106KAYNNNE | Samsung | 1276-CL21A106KAYNNNECT-ND | 0.11 | 0805 | 25 V | FIT |
| Cdec_P01, Cdec_N01 | 0.1 µF 50 V X7R | CL21B104KBCNNNC | Samsung | 1276-CL21B104KBCNNNCCT-ND | 0.10 | 0805 | 50 V | FIT |
| Cbulk_P, Cbulk_N | 100 µF 25 V | UVR1E101MED | Nichicon | 493-1041-ND | 0.30 | radial D6.3 | 25 V | FIT |
| Ctest | 1 pF 50 V C0G | CC0805CRNPO9BN1R0 | Yageo | 311-CC0805CRNPO9BN1R0CT-ND | 0.11 | 0805 | 50 V | FIT* |
| R5 | 47 Ω 5% (test) | RC0805JR-0747RL | Yageo | 311-47ARCT-ND | 0.10 | 0805 | — | FIT* |
| J_BIAS/J_SIPM/J_OUT/J_TEST | MCX edge 50 Ω | CONMCX013 | TE/Linx | CONMCX013-ND (DKPN 13245481) | 3.04 | MCX edge SMT | net‑HV | FIT (×4) |
| J_PWR | screw term 3-pos 5 mm | 1715035 (MKDS 1,5/3) | Phoenix | 277-1259-ND | 2.20 | THT 5 mm | 400 V | FIT |

\* `R5`/`Ctest`/`J_TEST` are the optional charge-injection test path (47 Ω series + 1 pF, per
CR-150-R5) — DNP if no bench charge inject.

**Per-board (1-off) BOM cost ≈ $65 (CR-112) + ~$14 (4× MCX) + ~$2.20 (terminal) + ~$1.50
(all passives + bulk) ≈ $83.** The CR-112 and the four MCX jacks dominate; passives are noise.

## HV-rating confirmation (Iron-rule #4 / brief failure flag)

**Both HV caps carry ≥100 V — CONFIRMED:**
- `Cc` (AC coupling, sees full SiPM bias ≤60 V) = **Murata GRM21AR72A224KAC5K, 0.22 µF, 100 V
  X7R**. Reference board used 0.22 µF/100 V X5R; X7R picked for better temp stability, same
  100 V class. 100 V ≫ the 45–55 V operating bias → comfortable margin.
- `Cf` (bias-filter shunt) = **Samsung CL21B104KCC5PNC, 0.1 µF, 100 V X7R**. 100 V class.

`Rf1`/`Rf2` (10 kΩ 0805) sit in the bias path; an 0805 thick-film at 12.5 V working voltage is
fine across the ≤60 V the filter divides — no derating issue. **HV creepage on the `SIPM`/
`BIAS_IN` nets and around `Cc`/`Cf`/the MCX center pins is a layout/DRC concern owned by the
Design track**, not a part-rating gap.

## Per-rail decoupling — traceability to CR-150-R5 (the reference circuit the rapid build omitted)

Cremat's own CR-150-R5 eval board (`reference/cremat-CR-150-R5/CR-150-R5.cmp`) decouples the
CR-11X module with **R7 = R8 = 4.7 Ω (0805) series** on each rail + **10 µF (1206) bulk** caps,
plus board bulk electrolytics. This BOM reproduces that per rail:
`Rdec_* = 4.7 Ω`, `Cdec_*10 = 10 µF`, adds a `0.1 µF` HF cap at the module pin
(`Cdec_*01`), and `100 µF` rail-entry bulk (`Cbulk_*`). Sizes moved to **0805** per the
project's passive policy (CR-150-R5 used 1206 for the 10 µF). **Final per-rail cap count/values
are the Design track's call** — this BOM gives the proven default; if A1 adds a 1 µF mid-cap,
use the same Samsung 1 µF/25 V 0805 line and tell me to add the row.

## Symbol / footprint / 3D provenance

| Part | Symbol | Footprint | 3D | Status |
|---|---|---|---|---|
| CR-112 | `hardware/lib/cremat.kicad_sym` → **CR-11X** | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` (SIP-8) | KiCad header 3D | **Ready** (reuse existing lib) |
| R/C 0805 (all) | KiCad `Device:R` / `Device:C` | `Resistor_SMD:R_0805_2012Metric` / `Capacitor_SMD:C_0805_2012Metric` | KiCad built-in | **Ready** |
| 100 µF radial | KiCad `Device:CP` | `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm` | KiCad built-in | **Ready** |
| MCX CONMCX013 ×4 | KiCad `Connector_Coaxial:Conn_Coaxial` | `cremat:MCX_CONMCX013_EdgeMount` (project lib) | ⚠ `CONMCX013.step` **MISSING** | **Footprint ready; 3D missing** |
| Phoenix MKDS 1,5/3 | KiCad terminal-block symbol | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal` | KiCad built-in | **Ready** |

All KiCad stock footprints above were **verified present** in `C:/Program Files/KiCad/10.0/
share/kicad/footprints/`. No SnapEDA login download is *required* to lay out or DRC this board —
every footprint resolves from KiCad stock + the existing project lib.

## Items needing a human login download (nice-to-have, NOT blocking)

1. **`CONMCX013.step` (3D model) — referenced by the existing footprint but the file is
   absent** from `hardware/lib/cremat.pretty/`. The footprint's
   `(model "${KIPRJMOD}/lib/cremat.pretty/CONMCX013.step" …)` line points at a missing file →
   3D viewer will show a placeholder. **Layout/DRC is unaffected** (footprint pads/courtyard are
   complete). To restore the 3D: download the CONMCX013-T KiCad pack and drop `CONMCX013.step`
   into `hardware/lib/cremat.pretty/`:
   - SnapEDA (login): https://www.snapeda.com/parts/CONMCX013-T/Linx/view-part/
   - Or TE/Linx 3D STEP: https://www.te.com/en/product-CONMCX013.html
2. **`Cc` 3D model (optional):** if a part-accurate 0.22 µF Murata 3D is wanted over the generic
   KiCad 0805, the Murata SnapEDA pack is at
   https://www.snapeda.com/parts/GRM21AR72A224KAC5K/Murata%20Electronics%20North%20America/view-part/
   — but the **generic KiCad C_0805 3D is perfectly adequate**; no action needed.

## Failure flags (none blocking) — disclosure

- **CR-112 is not a Digi-Key part.** Cremat modules are sold by Cremat Inc / FAST ComTec /
  Cremat's Amazon store, not Digi-Key. Priced from the official **Cremat US price list: $65
  (1–24 units), $59 (25+)**. Made-to-order → long lead, **order early** (charter notes this).
  This is inherent to the design (D4 locked CR-112), not a sourcing miss.
- **`Cc` Digi-Key PN not 100% pinned.** GRM21AR72A224KAC5K (0.22 µF/100 V/X7R/0805) is
  confirmed real & stocked at Newark/Element14/SnapEDA; the **490-** Digi-Key prefix is the
  Murata distributor code but the exact suffix wasn't scrape-confirmable through the 403.
  Search "GRM21AR72A224KAC5K" on digikey.com to get the live PN. A drop-in equal-spec
  alternate if Murata is short: **TDK CGA4J3X7T2A224K125AE** (0.22 µF/100 V/X7R/0805) or
  **KEMET C0805C224K1RAC** — all 100 V class, all 0805.
- No obsolete or out-of-stock parts. Every chosen line shows healthy stock (passives >100k–1M;
  CONMCX013, Phoenix, Nichicon all "in stock / ships today").

## How the Design track (A1) consumes this — generic → real, 1:1

| Design generic | → chosen real part | Footprint to set |
|---|---|---|
| CR-112 SIP-8 | Cremat CR-112-R2.1 (symbol = `cremat:CR-11X`) | `…:PinHeader_1x08_P2.54mm_Vertical` |
| Rf1/Rf2 "10 kΩ" | Yageo RC0805FR-0710KL | `Resistor_SMD:R_0805_2012Metric` |
| Cf "100 nF 100 V" | Samsung CL21B104KCC5PNC | `Capacitor_SMD:C_0805_2012Metric` |
| Cc "0.22 µF 100 V" | Murata GRM21AR72A224KAC5K | `Capacitor_SMD:C_0805_2012Metric` |
| JP_Rf1/JP_Rf2 "0 Ω" | Yageo RC0805JR-070RL | `Resistor_SMD:R_0805_2012Metric` |
| rail series R "4.7 Ω" | Yageo RC0805JR-074R7L | `Resistor_SMD:R_0805_2012Metric` |
| rail bulk "10 µF" | Samsung CL21A106KAYNNNE | `Capacitor_SMD:C_0805_2012Metric` |
| rail HF "0.1 µF" | Samsung CL21B104KBCNNNC | `Capacitor_SMD:C_0805_2012Metric` |
| rail entry "100 µF" | Nichicon UVR1E101MED | `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm` |
| test "1 pF" | Yageo CC0805CRNPO9BN1R0 | `Capacitor_SMD:C_0805_2012Metric` |
| 47 Ω (test) | Yageo RC0805JR-0747RL | `Resistor_SMD:R_0805_2012Metric` |
| MCX jack ×4 | TE/Linx CONMCX013 | `cremat:MCX_CONMCX013_EdgeMount` |
| power terminal | Phoenix 1715035 (MKDS 1,5/3) | `…:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal` |

The only value A1 must confirm with me is **how many `0.1 µF`/`10 µF`/`1 µF` decoupling caps
per rail** it places at the CR-112 — the BOM lists the CR-150-R5 default set; add/remove rows
to match the final schematic so Models-BOM == Design BOM at COMPLETE.
