# Session Report — A6 shaper-bom

> **The summary other tracks read instead of my log.** Keep current (overwrite). A
> consumer must be able to integrate from this + `INTERFACE.md` alone.

Track: `A6 shaper-bom` · Aspect: `models-bom` · Status: `criteria-met (M1+M2); design BOM == A6 BOM confirmed (incl. DNP)`
Last updated: `2026-06-25`

## Objective
Real, in-stock, economical Digi-Key parts (Cremat modules via Cremat-direct) for the
standalone CR-200 shaper + CR-210 BLR single-channel eval board, across both milestones
(M1 = CR-200 only; M2 = + CR-210 with 0R populate-or-bypass jumper). Deliver a BOM CSV +
report with full per-line provenance and an explicit DNP table, plus a 1:1 generic→real
mapping for the design/sim tracks.

## Success / failure criteria
- ✅ Every M1 + M2 part sourced to a real Digi-Key part (modules Cremat-direct), with value,
  MPN, mfr, DK-PN, unit cost @ qty, stock, package, datasheet, sym/fp/3D source. **0 unsourced.**
- ✅ All Digi-Key lines **in stock**, none obsolete/NRND. (Verified 2026-06-25.)
- ✅ Passives default to **0805** where the part allows (modules/trimpot/screw-term/electrolytic THT).
- ✅ **DNP / populate-or-bypass table explicit** per ref for CR-210-populated vs CR-210-bypassed.
- ✅ Economical choices justified (jellybean Yageo RC / Samsung CL21 / Bourns 3296W; ≤$15 passives/board).
- ✅ **1:1 generic→real mapping** delivered for A4/A5.
- ✅ **BOM == design BOM** — confirmed for M1 and M2 (incl. the DNP table) after the
  2026-06-25 reconciliation (see below).

## Current state
M1 **and** M2 fully sourced (the sub-component reaches its end milestone, M2). All parts in
stock, full provenance recorded.

**2026-06-25 coordinator reconciliation — 100k `R_PZ2` removed.** The 100k "P/Z fixed R" was
removed from this BOM: its CR-160-R7 `R9` citation was wrong (`R9` is on net code 10 → MAX4649
mux `U7` pin6 + gain-DIP `SW1` pin1, the buffer section A6 excludes — not the CR-200 P/Z). The
**CR-200 pole-zero is the 200k trimpot `R_PZ` alone** (CR-160-R7 `R7`). A4 removed the matching
part and re-gated both milestones (ERC 0/0, DRC 0/0/0/0); **design BOM == A6 BOM for M1 and M2,
incl. DNP**. Cost roll-up revised −$0.10/variant. See `BOM-REPORT.md` reconciliation note.

## Deliverables (what & where)
- [`shaper-bom.csv`](shaper-bom.csv) — machine-readable BOM, one row per ref, with
  `Milestone` + two populate columns (`Pop_CR210_populated`, `Pop_CR210_bypassed`).
- [`BOM-REPORT.md`](BOM-REPORT.md) — readable report: parts tables, **DNP table**, cost
  roll-up (M1 $72.19 / M2-pop $149.91 / M2-byp $72.29 qty1), economy justification,
  deviations from CR-160-R7, sym/fp/3D status, and the **generic→real mapping**.

## Interface I expose / consume
- Expose: the real-parts list (this is the **real-parts gate** output). Consumers = A4
  (design, swap generics→MPN 1:1) and A5 (sim, value-sensitive params: P/Z = 200k trim alone,
  49.9Ω term, ±12V rails, real MLCC).
- Consume: A4 `INTERFACE.md` + design BOM (for the final consistency check). Topology
  derived from `reference/cremat-CR-160-R7/CR-160-R7.net` (Cremat OSHW eval board).

## How to use my output
A4/A5: take the **generic→real mapping** table at the bottom of `BOM-REPORT.md` and swap each
generic value to the listed MPN/footprint 1:1; honor the DNP table (U_BLR XOR JP_BLR).

## Open issues / asks
- **No login-gated model downloads needed** — CR-200/CR-210 symbols, MCX footprint+STEP, and
  all passive sym/fp/3D are already in the repo (`hardware/lib/`) or KiCad stock libs.
- **Cremat modules are not Digi-Key parts** (sold direct, made-to-order, long lead). Order
  CR-200-1us-R2.1 and CR-210-R0 early from cremat.com.
- Confirm with A4 that the simplified per-rail decoupling (4.7Ω+10µF+0.1µF, modules off ±12V
  directly) matches the design's chosen topology — I excluded CR-160-R7's discrete rail
  regulator + buffer chain as out of A6 scope (belongs to the single-channel/buffer track).
