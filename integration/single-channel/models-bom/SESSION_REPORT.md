# Session Report — B3 `chan-bom` (single-channel Models-BOM)

> The summary other tracks read instead of my log.

Track: `B3 chan-bom` · Aspect: `models-bom` · Status: **criteria-met** (awaiting B1 design-BOM diff for COMPLETE)
Last updated: `2026-06-25`

## Objective
One consolidated **single-channel BOM**: the two proven Phase-A BOMs (CSP CR-112 + bias
front-end; CR-200 shaper + CR-210 BLR) **merged + deduped**, plus the **CFA output buffer**
(op-amp + Rf/Rg + 49.9 Ω + decoupling) added — every line real/in-stock/economical on
Digi-Key. I am the **buffer real-parts gate**: B1 swaps its generic buffer parts → my MPNs 1:1.

## Success / failure criteria
- ✅ S1 one consolidated BOM, Phase-A BOMs merged + shared jellybeans deduped — **48 ref lines → 19 distinct MPNs**.
- ✅ S2 buffer parts added (CFA + Rf/Rg + 49.9 Ω + per-rail 4.7 Ω/0.1 µF/10 µF decoupling).
- ✅ S3 every line sourced/in-stock/priced (primary buffer THS3491 = 695 in stock — no lead-time risk).
- ✅ S4 passives default 0805 (every R/C 0805).
- ✅ S5 buffer op-amp chosen + justified: CFA, 900 MHz BW + 620 mA drive for 50 Ω back-term.
- ✅ S6 op-amp symbol/FP/3D collected; **footprint verified present** in KiCad stock.
- ✅ S7 one-MPN-per-line mapping so B1 swaps generics → real 1:1.
- Disclosure (not a fail): the locked **EL5167 is OBSOLETE** → replaced with equivalent
  **active CFA** (brief permits "justify an equivalent CFA"). Replacement exceeds EL5167.

## Current state
BOM complete for the **CR-210-populated default** plus the **CR-210-bypassed** and
**filter-bypassed** variants (DNP rules carried from Phase A). Ready for B1 to consume and for
the Coordinator's COMPLETE check (Models-BOM == Design BOM once B1 publishes).

## Deliverables (what & where)
- `integration/single-channel/models-bom/single-channel-bom.csv` — the consolidated BOM (17 fields/line).
- `integration/single-channel/models-bom/BOM-REPORT.md` — justification, dedupe accounting, cost roll-up, generic→real map.
- `integration/single-channel/models-bom/SESSION_LOG.md` — full provenance.

## Buffer pick (the gate output) — FINAL per Coordinator (2026-06-25)
- **PRIMARY: TI THS3491** (`THS3491IDDAT`, DK `296-49085-2-ND`) — CFA, ±7–16 V (runs **direct
  on ±12 V**, no regulator), **620 mA** out, **900 MHz**, slew 8000 V/µs, SOIC-8 PowerPAD,
  **ACTIVE, 695 in stock**, $18.28 q1 / $13.60 q25. Chosen for in-stock + rail-safe.
- **Documented alt: TI THS3091** (`THS3091DDAR`, DK `296-46216-1-ND`) — same HV-CFA family/FP,
  ±5–15 V, 280 mA, ACTIVE, cheaper ($11.91 q1 / $7.98 q100) but **0 DK-direct stock / ~6-wk
  lead** — cost option for Phase C if it returns to stock.
- Gain **+2** (`Rfb = Rgain = 976 Ω` 1% 0805, Yageo RC0805FR-07976RL, DK 311-976CRCT-ND) →
  recovers the 50 Ω back-term 6 dB → unity into 50 Ω. **976 Ω is PINNED** = THS3491 datasheet
  G=+2 recommended Rf (CFA: Rf governs loop stability), B2-validated vs TI's official SPICE
  model (2026-06-25).
- Footprint **`Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm`** (exposed pad → V−). **NOT**
  the EL5167 SOT-23-5 — the existing `hardware/lib` EL5167 symbol's Footprint is empty; use the
  KiCad 8-pin op-amp symbol (or add a THS3491 project symbol).

## Cost (qty 1, single channel) — THS3491 primary
- **CR-210 populated: $242.08** (modules $201 + buffer IC THS3491 $18.28 + DK passives/conn $22.80).
- **CR-210 bypassed: $164.46.** (With the THS3091 alt buffer: populated $235.71.) Modules ~83% of cost.

## Merge / dedupe result
- Shared passives/jacks/terminal collapsed to single buy lines (4.7 Ω ×8, 0.1 µF ×8, 10 µF ×8,
  0R ×3, MCX ×4, 976 Ω ×2, 100 µF ×2).
- Removed **2 MCX** (CSP_OUT↔shaper IN → internal net) and **1× 49.9 Ω** (shaper edge term →
  single buffer OUT_50 term).
- Reconciled 2 same-role conflicts: board bulk → **UWT1V101MCL1GS** (SMD 35 V); power terminal
  → Phoenix **1715734** (5.08 mm). **B1 must use the reconciled PNs.**

## Interface I expose / consume
- **Expose:** the consolidated per-channel parts list (the buffer real-parts gate). 1-MPN-per-
  generic map in `BOM-REPORT.md §6`. The channel output is `OUT_50` (Zout = 50 Ω) — buffer +
  49.9 Ω series.
- **Consume:** both Phase-A models-bom CSVs/reports (CSP A3, shaper A6); the buffer app circuit
  from `reference/cremat-x6-board` + TI THS3091/3491 datasheets.

## How to use my output
> B1: load `single-channel-bom.csv`; set the buffer `U_BUF = THS3491IDDAT` (primary; alt
> THS3091DDAR) on `SOIC-8-1EP…EP2.29x3mm` (EP→V−), `Rfb=Rgain=976 Ω` (RC0805FR-07976RL),
> `R_OUT=49.9 Ω`, add 4.7 Ω/0.1 µF/10 µF buffer decoupling; use the reconciled bulk
> (UWT1V101MCL1GS) + terminal (1715734); everything else = committed Phase-A parts. Then
> Models-BOM == Design BOM.

## Open issues / asks
- **B1 confirm** the buffer pick (THS3091 vs in-stock THS3491) and the **exact `Rf`** from the
  chosen part's datasheet Table 8-1; **B2** drop that part's SPICE model and re-sim with the
  pinned `Rf`. If B1 changes decoupling-cap count at the buffer, tell me to sync rows.
- **No login-gated download blocks the buffer.** (Carried Phase-A nice-to-haves only: optional
  `Cc` Murata 3D — generic KiCad 0805 3D is fine; MCX `CONMCX013.step` already in
  `hardware/lib/cremat.pretty/`.)
