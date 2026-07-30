# LCSC / JLCPCB assembly stock check — 2026-07-28

Live check of the 12 assembled SMD line items in
[`design/fab/jlc/bom-twelve-channel-jlc.csv`](../design/fab/jlc/bom-twelve-channel-jlc.csv)
ahead of a JLCPCB SMT assembly order. Stock figures are **LCSC retail** (via web, 2026-07-28).
Quantities are the whole 12‑channel board × the planned **2‑board** assembly build.

> **CRITICAL — read before acting on "Out of Stock" below.**
> **LCSC retail stock and JLCPCB SMT‑assembly stock are SEPARATE inventory pools for the same
> C‑number.** JLC stocks its assembly feeders independently of LCSC's retail reels — a part can
> read "Out of Stock" for LCSC retail purchase and still be fully available for JLC SMT assembly
> (this is normal for JLC **Basic** parts). The figures below are therefore an *indicator*, not
> the assembly-side truth. **The authoritative check is uploading this BOM to JLCPCB's SMT order
> tool**, which validates each part against the *assembly* pool and auto-suggests replacements.

## Resolution (2026-07-28, same day)

The three LCSC-OOS lines were re-sourced to fetch-verified in-stock parts and the BOM
[`bom-twelve-channel-jlc.csv`](../design/fab/jlc/bom-twelve-channel-jlc.csv) updated in place
(placement count unchanged at 246). Each replacement was confirmed by fetching its LCSC page twice
(sourcing agent + independent re-fetch):

| Line | Was (OOS) | Now | Mfr / MPN | LCSC stock | JLC class |
|---|---|---|---|--:|---|
| 10 k 1% 0805 | C17414 | **C84376** | YAGEO RC0805FR-0710KL | 1,032,300 | Basic |
| 4.7 Ω 0805 | C17675 | **C2933459** | FOJAN FRC0805F4R70TS (±1%) | 347,700 | **Extended** ⚠ |
| 470 µF 35 V | *(kept)* | **C494847** | Panasonic EEE-FN1V471UP | LCSC 0 / **JLC-assembly YES** | Extended |

- **10 k → C84376**: the design's own DigiKey MPN (YAGEO RC0805FR-0710KL) and a JLC Basic part —
  ideal drop-in.
- **4.7 Ω → C2933459**: the only Basic 4.7 Ω (C17675) is gone, so this is Extended (+$3 feeder).
  **Revert to C17675 at upload if JLC's assembly pool still has it Basic** — see ORDERING.md ⚠.
- **470 µF → kept C494847** (Panasonic). *Correction (2026-07-28, at JLC upload):* the earlier
  LCSC-retail substitute **C72519 came up "unmatched"** in JLC's Economic assembly tier — verified
  via jlcpcb.com/partdetail that C72519 is **"Standard-only" PCBA** (not in the Economic feeder
  library), whereas **C494847 is "Economic + Standard" PCBA**. For a JLC *assembly* order the part
  must be in JLC's assembly library; **LCSC-retail stock is the wrong criterion for electrolytics**
  (JLC assembles from its own feeder pool — C494847's LCSC-retail 0 does not matter). Reverted the
  BOM to C494847. The 10 k (C84376) and 4.7 Ω (C2933459) matched fine, so they stay.
  **General rule for JLC assembly BOMs: pick parts that jlcpcb.com/partdetail lists as
  "Economic and Standard" PCBA, not just LCSC-in-stock.**

Higher-grade alternates on file if wanted: 4.7 Ω YAGEO RC0805FR-074R7L = **C137513** (48 k, 1%);
470 µF AEC-Q200 ROQANG = **C5162352** (D10×10.5, 2.6 k). All fetch-verified in stock 2026-07-28.

### Test-cap precision upgrade (C_test, 1 pF → 10 pF ±1%)

Per user: the test input is a **calibration** injector (`C_test` couples `TEST_IN → CSP_IN`,
Q = C·V_step), so it needs a precision, well-defined value — not the ±0.25 pF/±25% of the 1 pF part.
Changed to **10 pF ±1% C0G** = **C541512** (YAGEO CC0805FRNPO9BN100): ±1% = ±0.1 pF, a 10× better
charge-injection accuracy. Verified LCSC 750 in stock **and** JLC **"Economic and Standard" PCBA**
(assembly pool 2,238) — it is the only true ±1% 10 pF/0805/C0G in JLC's library. Same 0805
footprint; +9 pF on the CSP input node is negligible vs the ~1.28 nF SiPM. **JLC BOM + the
single-channel SPEC (`gen_sch.py` `C_test`) updated.** The schematic/PCB *value labels* still read
"1 pF" until a regeneration — cosmetic only (documentation-layer text; copper, CPL and the
assembled part are all driven by the BOM/footprint, which are correct). Regenerate to sync labels
when the order settles.

### MCX edge jack → JLC assembly, STANDARD tier (2026-07-30)

Per user, the MCX edge jack is SMD and JLC assembles it — it was previously a DigiKey hand-solder
line. Sourced to **BAT WIRELESS BWMCX-KEF = C5250059** (LCSC 4,853 in stock, $0.4857), the only
true-MCX (not MMCX) part in JLC's library. Verified on jlcpcb.com/partdetail 2026-07-30:
**PCBA type "Standard Only", "High" assembly difficulty** — it is *not* in the Economic-tier
feeder library, so an Economic-tier order rejects all 48 as UNMATCHED (same trap as the 470 µF).
The other 4 candidates were all rejected — C47324993 (BWMMCX-KEF-B) is Economic+Standard but
**MMCX** (wrong, smaller family); C910124 / C5250057 / C5451762 are all MMCX *and* Standard-only:

| LCSC | Part | Family | JLC PCBA tier |
|---|---|---|---|
| **C5250059** | BWMCX-KEF | **MCX** ✓ | **Standard Only** |
| C47324993 | BWMMCX-KEF-B | MMCX ✗ | Economic + Standard |
| C910124 | KH-MMCX-PBS | MMCX ✗ | Standard Only (+ fixture) |
| C5250057 | BWMMCX-KEF | MMCX ✗ | Standard Only |
| C5451762 | HJ-MMCX008 | MMCX ✗ | Standard Only |

**Decision (user): order the whole board's assembly in JLC's STANDARD tier** so JLC places all 48
MCX. Added to the JLC BOM (line 13, designators **J1–J48**) and CPL (246 → **294** placements).
Kept the existing Linx **CONMCX013** land pattern (footprint geometry unchanged → **gerbers
unchanged**); BWMCX-KEF is a user-verified drop-in on that land (mechanical-drawing comparison).
Removed from the DigiKey hand-BOM; footprint MPN properties + the single-channel SPEC
(`gen_sch.py` PARTS: J_BIAS/J_SIPM/J_TEST/J_OUT50) updated to the BAT part.

**CPL corrections for the BWMCX-KEF part (2026-07-30):** JLC-preview checks showed the MCX (1) 90°
off and (2) ~1.8 mm off its pads. Two CPL-only fixes: **(1) rotation +90° CCW** — left-edge jacks
−90°→**0°**, right-edge jacks +90°→**180°**; **(2) `Mid X` shifted 1.8 mm inboard** (left 6.3→8.1,
right 206.9→205.1) — the BAT part's mounting reference sits ~1.8 mm off the Linx CONMCX013 land.
⚠ Both live **only in `cpl-twelve-channel-jlc.csv`**; the board and raw KiCad `pick-and-place.csv`
keep the true land geometry. **Re-apply BOTH (+90° and 1.8 mm inboard) if the CPL is ever
regenerated.** Confirm in the JLC preview: barrel off the edge, part seated on its pads.

**D1/D2 diode polarity (2026-07-30):** the KiCad→JLC diode-convention flip left D1/D2 placed 180°
reversed. CPL rotation corrected −90°→**90°** (+180°) so the cathode band lands on pad 1 (D1 pad1 =
+VDC, D2 pad1 = −VDC_F, per `D_Schottky` pin1 = K), and a **bold silk cathode stripe** was added at
pad 1 on both (board + gerber zip regenerated — top silk only, copper/drill unchanged).
⚠ Re-apply the +180° if the CPL is regenerated. C133/C134 (electrolytic) were already correct.

## Stock table

| LCSC # | Value | Qty/board | Qty ×2 | LCSC retail stock | Status |
|---|---|--:|--:|--:|---|
| C17720 | 49.9 Ω 1% 0805 | 12 | 24 | 723,100 | ✅ |
| C2167405 | 0.22 µF 100 V X7R 0805 | 12 | 24 | 3,505 | ✅ (lowest — watch) |
| C17477 | 0 Ω jumper 0805 | 12 | 24 | 4,379,600 | ✅ |
| C28233 | 100 nF 100 V X7R 0805 | 12 | 24 | 758,650 | ✅ |
| **C17414** | **10 k 1% 0805** | 24 | 48 | **0 (OOS)** | ⚠️ LCSC OOS — but **JLC Basic** (assembles) |
| C15850 | 10 µF 25 V X5R 0805 | 72 | 144 | 247,900 | ✅ |
| C513668 | 1 pF 50 V C0G 0805 | 12 | 24 | 19,900 | ✅ |
| **C17675** | **4.7 Ω 0805** | 72 | 144 | **0 (OOS)** | ⚠️ LCSC OOS — jellybean, verify at upload |
| C17714 | 47 Ω 1% 0805 | 12 | 24 | 308,400 | ✅ |
| **C494847** | **470 µF 35 V SMD 10×10.5** | 2 | 4 | **0 (OOS)** | ❌ likely **Extended** — real risk |
| C207066 | PTC 1.1 A 24 V 1812 | 2 | 4 | 2,680 | ✅ |
| C8678 | Schottky 40 V SMA | 2 | 4 | 1,642,120 | ✅ (but see note) |

## Flagged items

**C17414 (10 k 1% 0805) — LCSC OOS, but a JLC Basic part.** Confirmed present in JLCPCB's
Assembly Parts Library tagged *Basic* (UNI-ROYAL 0805W8F1002T5E — the canonical JLC basic 10 k).
Basic parts are stocked for assembly regardless of LCSC retail. **Expected to assemble fine;**
confirm at BOM upload. This is the single highest-count resistor value on the board.

**C17675 (4.7 Ω 0805) — LCSC OOS.** A jellybean value (UNI-ROYAL 0805W8F470KT5E), needed in the
largest quantity (144 for 2 boards — the Cremat per-rail supply filter). Almost certainly a JLC
Basic/preferred value; if JLC's tool flags it, it auto-suggests an identical in-stock 4.7 Ω 0805.
Trivial to substitute (any 4.7 Ω 0805, ≥1/8 W) — no design impact.

**C494847 (470 µF 35 V, Panasonic EEE-FN1V471UP) — LCSC OOS, likely an Extended part → the one
genuine risk.** Only 2/board (4 total), on the bulk-rail decoupling `C133/C134`. Because it is an
electrolytic with a **specific 10×10.5 mm footprint** (`Capacitor_SMD:CP_Elec_10x10.5`), it can't
be blindly auto-swapped — a replacement must match Ø10 × 10.5 mm (or 10 × 10). Recommend picking a
verified in-stock 470 µF 35 V SMD in that can size before ordering rather than letting the tool
guess. (A lower-value bulk, e.g. 330 µF 35 V, would also be acceptable given it only backs the
distributed 10 µF — but confirm before changing.)

**C8678 (Schottky) — identity note, not a stock problem.** The JLC BOM part C8678 is **MDD SS34
(40 V / 3 A, SMA)**, whereas the sourcing doc / DigiKey hand-BOM names **onsemi SSA24 (40 V / 2 A,
SMA)**. Same package (DO-214AC/SMA), same reverse-block role; SS34's 3 A rating is *more* margin
than the ~0.5 A per-diode load needs. Electrically a fine drop-in — just a naming inconsistency
between the assembled-BOM and the doc. In stock, no action needed.

## Recommended next step

Upload [`design/fab/jlc/bom-twelve-channel-jlc.csv`](../design/fab/jlc/bom-twelve-channel-jlc.csv)
+ [`cpl-twelve-channel-jlc.csv`](../design/fab/jlc/cpl-twelve-channel-jlc.csv) to JLCPCB's SMT
order tool. It marks each part against the *assembly* pool and offers one-click replacements for
anything short. The only item worth pre-resolving by hand is **C494847** (footprint-constrained
electrolytic); the resistors are safe to let JLC match.
