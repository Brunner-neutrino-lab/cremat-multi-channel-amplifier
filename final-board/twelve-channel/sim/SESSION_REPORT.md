# Session Report — C3 board-sim

> **The summary other tracks read instead of my log.** Keep current (overwrite).

Track: `C3 board-sim` · Aspect: `sim` · Status: `criteria-met`
Last updated: `2026-06-28`

## Objective
A **system-level confidence pass** for the 12-channel final board (the per-channel
response is already proven in Phase B). Three checks: (1) one channel's OUT_50 response
is unchanged in the multiplied context; (2) the 12-channel shared-rail load vs. the
decoupling + bulk is adequate; (3) channel-to-channel (shared-rail) crosstalk is bounded.
No full EM model — confidence level, per the C3 brief.

## Success / failure criteria (stated before work)
- ✅ **C1 — one-channel response unchanged vs Phase B.** PASS: OUT_50 = **+66.998 mV** for
  0.5 pC into 50 Ω, peaking 2.473 µs, FWHM 2.527 µs, 134.0 mV/pC — **bit-identical to B2's
  67.00 mV / 134 mV/pC / 2.47–2.53 µs** (same models, same deck of record).
- ✅ **C2 — 12-ch supply current computed; rail/decoupling/bulk adequate.** PASS:
  **+12 V = 584 mA, −12 V = 536 mA** (≈13.5 W); per-part 4.7 Ω decoupling drop ≤ 80 mV
  (independent of channel count); 100 µF bulk + 480 µF distributed local hugely over-spec'd
  for the signal transient. No rail sag / instability.
- ✅ **C3 — channel-to-channel crosstalk negligible.** PASS: shared-rail dynamic ripple
  ≈ 42 µV → victim ≈ 0.13 µV = **0.0002 % of full-scale** (conservative 50 dB PSRR);
  even 12×-simultaneous worst case = 0.0024 % FS.
- **Failure (none triggered):** would have been rail sag/instability with 12 channels, or the
  one-channel response regressing vs single channel.

## Current state
**ALL THREE CRITERIA MET.** The frozen single channel is confirmed to survive the ×12
context; the shared ±12 V rails, per-part decoupling, and bulk are adequate with margin; and
shared-rail crosstalk is far below any meaningful level. No design change is *required* of
C1/C2 — three optional/advisory flags below.

## Key numbers (the system-check FoM)

### One channel in the ×12 context (criterion 1) — `data/chain_fom.json`
| stage | peak | peaking | FWHM |
|---|---|---|---|
| CSP_OUT (CR-112) | −6.445 mV | — | — |
| SHOUT (CR-200) | −67.16 mV | 2.44 µs | 2.53 µs |
| BLR_OUT (CR-210) | +66.99 mV | 2.47 µs | 2.52 µs |
| BUF_OUT (THS3491) | +133.86 mV | 2.47 µs | 2.53 µs |
| **OUT_50 (50 Ω)** | **+66.998 mV** | 2.47 µs | 2.53 µs |
Charge→OUT_50 = **134.0 mV/pC**. **vs Phase B (B2): 67.00 mV / 134 mV/pC — match (Δ < 0.01 %).**

### Shared-rail loading (criterion 2) — `scripts/rail_budget.py`
| part (per channel) | +rail mA | −rail mA | source |
|---|---|---|---|
| CR-112 CSP | 8.0 | 8.0 | datasheet ~5 mA @ ±6V; 8 mA conservative @ ±12V |
| CR-200 shaper | 7.0 | 7.0 | datasheet quiescent 7 mA @ Vs=±13V |
| CR-210 BLR | **17.0** | 13.0 | datasheet pos 17 / neg 13 mA (asymmetric) |
| THS3491 buffer | 16.7 | 16.7 | TI IQ 16.7 mA @ ±15V |
| **per channel** | **48.7** | **44.7** | |
| **×12 board** | **584 mA** | **536 mA** | board power ≈ **13.5 W** |

- **4.7 Ω per-part decoupling IR drop** (each R carries *one* part's current — **not** ×12):
  worst = CR-210 +rail = **79.9 mV** (THS3491 78.5 mV) → local part rail ≈ **11.92 V**, far
  above the CR-11X ±6 V minimum and irrelevant to the THS3491 (its headroom is on the
  ≤±0.2 V output swing, not the rail). **Adequate.**
- **Shared-feed (plane/pour) IR drop:** 12 mV @ 20 mΩ … 58 mV @ 100 mΩ (pessimistic). A
  4-layer pour gives mΩ-scale R → sub-100 mV static droop; signal-independent. **Adequate.**
- **Bulk adequacy:** single-event dynamic charge ≈ 3.4 nC/channel → 0.34 mV on a 10 µF local
  cap; all-12-at-once 40 nC → 0.40 mV on the 100 µF bulk. **The single 100 µF board bulk is
  adequate; the 10 µF/part local caps dominate the transient.**

### Channel-to-channel crosstalk (criterion 3) — `data/xtalk_fom.json`, `plots/xtalk_rail_ripple.png`
- Aggressor **dynamic** supply-current swing during a 0.5 pC event = **−1.38 mA peak** (+rail)
  / 0.025 mA (−rail) — only the THS3491 sourcing into 50 Ω; the rest is quiescent (DC).
- Driving that into the shared 100 µF bulk (30 mΩ ESR) + 100 mΩ feed → **rail ripple ≈ 42 µV**
  (≈ i_peak×ESR; the bulk shunts the AC). Closed-form cross-check 41.46 µV ≈ ODE 41.6 µV.
- Through THS3491 PSRR (datasheet 78/77 dB min DC; **conservative 50 dB in-band**) →
  **victim crosstalk ≈ 0.13 µV = 0.0002 % of the 67 mV OUT_50 full-scale.** Negligible.
- 12×-simultaneous fully-correlated worst case: ripple ≈ 0.50 mV → victim ≈ 1.6 µV = 0.0024 % FS.

## Deliverables (what & where) — all under `final-board/twelve-channel/sim/`
- **Decks:** `decks/chain_single_event.cir` (criterion 1, = Phase-B deck of record),
  `decks/chain_isupply.cir` (= proven deck + `.save I(Vp) I(Vn)`; the crosstalk-source capture).
  Models/libs `decks/{cr112_csp,cr200_1us,cr210}.sub`, `ths3491_rgt.lib`, `models.inc` (copies).
- **Scripts:** `scripts/analyze_chain.py` (criterion 1 FoM+plots), `scripts/rail_budget.py`
  (criterion 2 budget), `scripts/xtalk_analyze.py` (criterion 3 ripple→PSRR bound),
  `scripts/{ltspice_raw.py, run_ltspice.ps1, run_all.ps1}`. **One-shot:** `powershell -File scripts\run_all.ps1`.
- **Plots:** `plots/chain_{per_stage,normalised_overlay,out50_detail,input_charge}.png`,
  `plots/xtalk_rail_ripple.png`.
- **FoM data:** `data/chain_fom.json`, `data/xtalk_fom.json`.
- **Engine:** LTspice 24.x batch (`-b -Run`), parsed with `ltspice_raw.py` (numpy). Staging via
  `run_ltspice.ps1` (LTspice batch fails on OneDrive space-paths → run in `C:\Temp\ltspice_12ch`).

## Interface I expose / consume
- **Verifies-by (for the twelve-channel INTERFACE):** the ×12 board delivers the **unchanged
  per-channel +67 mV/0.5 pC** OUT_50; the shared ±12 V rails carry **+584 / −536 mA**
  (≈13.5 W) with ≤80 mV per-part decoupling drop and ≤0.0002 % FS channel-to-channel crosstalk.
- **Consume:** `integration/single-channel/INTERFACE.md` (frozen channel topology, decoupling =
  4.7 Ω+10 µF+0.1 µF per part + ONE 100 µF bulk pair, THS3491 buffer); B2 sim (FoM, deck of
  record, TI THS3491 model); CR-112/CR-200/CR-210 + THS3491 datasheets (quiescent currents, PSRR).

## How to use my output
**C1/C2:** the design is electrically sound at ×12 — no required change. Budget the **±12 V
supply at ~0.6 A/rail / 13.5 W** (pick ≥1 A/rail). The system check passes; PROJECT-DONE
criterion for C3 is met once C1 (DRC-clean fab) + C2 (priced BOM == board) agree.

## Open issues / asks (advisory only — no design change required)
1. **Supply sizing:** the board draws **0.58 A (+) / 0.54 A (−), ≈13.5 W** quiescent — ensure
   the chosen ±12 V supply and the screw-terminal/feed-copper handle ≥1 A/rail (C2/mechanical).
2. **+rail is ~10 % heavier than −rail** (CR-210 BLR is asymmetric, 17 vs 13 mA, ×12 → +144 mA
   extra on +12 V). The +VDC rail is the one carried by a **B.Cu pour** (no full inner plane) —
   keep that pour generous/continuous to the far channels (C1). Still sub-100 mV droop.
3. **Bulk:** the single 100 µF board bulk is adequate by the analysis; a 2nd 100 µF bulk near
   the far channel rows is an **optional** margin improvement, not a requirement.
- **Modeling caveat:** crosstalk bounded analytically (real captured I(rail) → shared-rail RC →
  datasheet PSRR), cross-checked closed-form; a two-channel nonlinear LTspice solve was not
  feasible (two THS3491 macromodels on a soft RC rail give a singular DC op-point) and is
  unnecessary at the resulting <0.001 % FS level. CR-112 modeled on its ±6 V op-point rail (as
  in B2); its ~8 mA/rail is added to the budget analytically.
