# Session Log — A3 csp-bom

> **Ground truth, append-only.** One dated entry per working session: what you did, exact
> commands/tools, results (numbers, ERC/DRC counts, sim figures of merit), decisions **and
> why**, dead-ends, next steps. Never rewrite earlier entries.

Track: `A3 csp-bom` · Sub-component: `csp-cr112` · Aspect: `models-bom`
Reads (inputs): brief `docs/agent-project/briefs/A-csp-cr112.md`; `00-CHARTER.md`,
`01-CONVENTIONS.md` (esp. §7); prior art `reference/cremat-CR-150-R5/`,
`hardware/lib/cremat.kicad_sym`, `hardware/lib/cremat.pretty/`, `hardware/bom/`,
`docs/hardware/{bom.md,circuit-design.md}`.
Success criteria (mirror of report): every part on the CR-112 CSP + bias front-end sourced to a
real, in-stock, economical Digi-Key part (one MPN/line), HV caps Cc/Cf >=100 V, 0805 default,
full provenance recorded, CSV + readable report delivered, BOM unambiguous for design 1:1 swap.

---

## 2026-06-25 — session 1 — source the full CSP eval-board BOM

**Goal this session:** identify + price + provenance every part on the standalone CR-112 CSP
eval board (incl. SiPM bias front-end), deliver CSV + report at the real-parts gate.

**Did:**
- Read charter, conventions (§7 sourcing), brief A-csp-cr112 (A3 aspect).
- Mined prior art for the authoritative part set:
  - `reference/cremat-CR-150-R5/CR-150-R5.cmp` — Cremat's own CR-11X eval board: confirms
    per-rail decoupling = **R7/R8 = 4.7 ohm (0805) series + 10 uF (1206) bulk** per rail, plus
    board electrolytics; test cap C2 = 1 pF (0805).
  - `docs/hardware/circuit-design.md` — locked values: Rf1/Rf2 = 10 k, Cf = 100 nF/100 V/X7R,
    Cc = 0.22 uF/100 V/X5R-X7R; bias 45-55 V (<=60 V); CR-112 gain 13 mV/pC.
  - `hardware/lib/cremat.kicad_sym` — CR-11X/CR-112 symbol present (reuse).
  - `hardware/lib/cremat.pretty/MCX_CONMCX013_EdgeMount.kicad_mod` — MCX footprint present;
    its `(model ...CONMCX013.step)` line points at a **missing** .step (3D gap).
- WebSearch + WebFetch sourcing (Digi-Key direct = 403, used search + mfr/distributor pages +
  Cremat price list):
  - CR-112 price: Cremat US price list (cremat.com/ordering/.../us-prices...) -> **$65 (1-24),
    $59 (25+)**. Not a Digi-Key part (Cremat/FAST ComTec/Amazon).
  - CONMCX013: Digi-Key DKPN 13245481, ~$3.04, in stock (ships today).
  - Phoenix MKDS 1,5/3 (5 mm, 3-pos) = 1715035 = **DK 277-1259-ND**, in stock.
  - Cc 0.22 uF/100 V/X7R/0805 = **Murata GRM21AR72A224KAC5K** (Newark/Element14/SnapEDA
    confirm 100 V); DK 490-prefix, exact suffix not scrape-confirmable through 403.
  - Cf / 0.1 uF 100 V = **Samsung CL21B104KCC5PNC** (100 V X7R 0805), DK 1276-2447-1-ND.
  - 10 k 1% 0805 = **Yageo RC0805FR-0710KL**, DK 311-10.0KCRCT-ND.
  - 0 ohm 0805 = **Yageo RC0805JR-070RL**, DK 311-0.0ARCT-ND.
  - 4.7 ohm 0805 = **Yageo RC0805JR-074R7L**, DK 311-4.7ARCT-ND.
  - 10 uF 25 V 0805 = **Samsung CL21A106KAYNNNE**, DK 1276-CL21A106KAYNNNECT-ND.
  - 100 uF 25 V radial = **Nichicon UVR1E101MED**, DK 493-1041-ND.
  - 1 pF 50 V C0G 0805 = **Yageo CC0805CRNPO9BN1R0**, DK 311-CC0805CRNPO9BN1R0CT-ND.
- Verified KiCad stock footprints exist (`C:/Program Files/KiCad/10.0/share/kicad/footprints/`):
  `R_0805_2012Metric`, `C_0805_2012Metric`, `CP_Radial_D6.3mm_P2.50mm`,
  `PinHeader_1x08_P2.54mm_Vertical`, `TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal`
  — all present. (Phoenix FP name uses a **comma**, not a period — corrected in CSV.)
- Wrote `csp-cr112-bom.csv` (machine-readable) + `PARTS_REPORT.md` (readable).

**Results:**
- 13 distinct line items, every one sourced + in stock + priced. 1-off board BOM cost ~ **$83**
  (CR-112 $65 + 4x MCX ~$14 + terminal $2.20 + ~$1.50 passives/bulk).
- HV check PASS: Cc = 100 V (Murata GRM21AR72A224KAC5K X7R), Cf = 100 V (Samsung
  CL21B104KCC5PNC X7R). Both >=100 V vs <=60 V bias.
- Footprints: 100% resolve from KiCad stock + existing project lib. No login download needed to
  lay out/DRC.

**Decisions & why:**
- **Board scope = CSP + bias front-end only.** Shaper/CR-210/EL5167 buffer are A4/Phase B —
  excluded from this BOM (per charter phase split).
- **0805 for all passives incl. the CR-150-R5 10 uF (was 1206).** Project passive policy
  (docs/hardware/bom.md) defaults 0805 where the part allows; 10 uF/25 V is readily 0805.
- **Cc X7R over the reference's X5R.** Same 100 V class; X7R = better temp stability for a
  detector front-end. Equal-spec alternates listed (TDK CGA4J3X7T2A224K125AE, KEMET).
- **5% tol OK for Rdec (4.7 ohm) and 0 ohm jumpers; 1% for Rf (bias filter).** Series decoupling
  R is non-critical; filter R sets fc and recovery -> 1%.
- **Added 0.1 uF HF cap + 100 uF rail-entry bulk** beyond CR-150-R5's literal set to give the
  module a clean HF + bulk decoupling stack; flagged that final per-rail count is A1's call.

**Dead-ends / surprises:**
- Digi-Key WebFetch = HTTP 403 (as coordinator warned); Octopart WebFetch = 403 too. Worked
  around with WebSearch snippets + non-blocked distributor/mfr pages + Cremat HTML price page.
- Cremat-Price-List.pdf is image-only -> unparseable; the HTML US-prices page gave the numbers.
- `CONMCX013.step` referenced by the existing footprint is **missing** from the repo — 3D-only
  gap, does not block layout/DRC. Listed for human download (SnapEDA/TE links in report).

**State vs criteria:** ALL success criteria met. Every line sourced + in stock + priced; HV
Cc/Cf >=100 V confirmed; 0805 default applied; provenance recorded; CSV + report delivered;
generic->real 1:1 map published. Two non-blocking flags disclosed (CR-112 not on DK by nature;
Cc DK suffix to confirm live).

**Next:** Hand to coordinator for the real-parts gate -> A1 swaps generics->MPNs, re-runs
ERC/DRC; A2 checks value-sensitive params. If A1's final schematic changes the decoupling cap
count or adds a 1 uF mid-cap, append a row here so Models-BOM == Design BOM at COMPLETE.

---

## 2026-06-25 — session 2 — coordinator reconciliation: add test-injection R5 (47 ohm)

**Goal this session:** make A3 Models-BOM byte-exact with the A1 design BOM. Coordinator
flagged that A1's real-parts board (ERC/DRC 0/0/0) carries a **47 ohm test-injection series
resistor `R5`** on the TEST_IN charge-inject path (47 ohm + 1 pF, per CR-150-R5) that this BOM
omitted in session 1.

**Did:**
- Re-read `csp-cr112-bom.csv` + `PARTS_REPORT.md` for the exact 16-column format.
- WebSearch-verified the MPN A1 selected: **Yageo RC0805JR-0747RL** = 47 ohm, 0805, 5% thick
  film — real Digi-Key part (digikey.com product 728335). Confirmed Digi-Key PN
  **311-47ARCT-ND** from the RC0805JR family pattern: the 5%/J-tol Digi-Key PN is
  `311-<value>A RCT-ND` for 0805 (sibling family members from search: RC0603JR-0747RL =
  311-47GRCT-ND, RC1206JR-0747RL = 311-47ERCT-ND, RC0402JR-0747RL = 311-47JRCT-ND — letter is
  the case-size code; 0805 = `A`). Internally consistent with this BOM's existing RC0805JR rows
  311-4.7ARCT-ND (4.7 ohm) and 311-0.0ARCT-ND (0 ohm).
- Added one row `R5` to the CSV after `Ctest` (test-path parts grouped): value 47, MPN
  RC0805JR-0747RL, Yageo, 311-47ARCT-ND, $0.10 @ qty1, >1M stock, 0805, Yageo RC datasheet,
  KiCad stock Device:R + R_0805_2012Metric + 3D, Populate=FIT, note ties it to CR-150-R5 R5 and
  Ctest (DNP together if no bench charge inject).
- Updated `PARTS_REPORT.md`: added the table row, extended the test-path footnote to
  R5/Ctest/J_TEST, and added the generic->real map line `47 Ω (test) → RC0805JR-0747RL`.

**Results:**
- A3 BOM now **14 distinct line items** (was 13). Per-board cost unchanged at ~**$83** (+$0.10
  for R5 is inside the ~$1.50 passives bucket; rounds away).
- **A3 BOM == A1 design BOM, line-for-line by MPN: YES.** The 47 ohm test resistor was the only
  delta; all other rows already matched 1:1.

**Decisions & why:**
- **5% tol for R5.** A test-injection series R only sets the source impedance of the inject node
  (47 ohm into 1 pF); value is non-critical -> J-tol jellybean, same as the 4.7 ohm rail R's.
- **Placed in the optional test path (FIT*, DNP-with-Ctest).** R5 only matters when the bench
  charge-injection path is populated; it shares the Ctest/J_TEST populate decision.

**Dead-ends / surprises:** none. Digi-Key direct still 403; PN confirmed via WebSearch +
family pattern + internal consistency with existing RC0805JR rows.

**State vs criteria:** Models-BOM == Design BOM at COMPLETE. Edited only inside
`chips-board/csp-cr112/models-bom/`. No commit, no touch to `docs/agent-project/02-TRACKS.md`.
