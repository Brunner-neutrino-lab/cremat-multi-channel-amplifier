# Session Report — A5 `shaper-sim`

> The summary other tracks read instead of my log. A consumer integrates from this + `INTERFACE.md`.

Track: `A5` · Aspect: `sim` · Status: `criteria-met (M1 + M2)`
Last updated: `2026-06-25`

## Objective
Simulate the CR-200-1µs Gaussian shaper (M1), then CR-200 + CR-210 baseline restorer (M2),
using **Cremat's official LTspice models**, and report figures of merit (peak, peaking time vs
shaping time, undershoot; M2 baseline restoration) judged against the datasheets.

## Success / failure criteria (stated before the work)
- ✅ **M1:** shaped Gaussian at OUT; peaking time ≈ shaping time (FWHM ≈ 2.4 µs per datasheet)
  within model tol; peak amplitude + undershoot reported; official Cremat model used.
- ✅ **M1:** behavioral cross-check agrees on the controlling metric (FWHM).
- ✅ **M1:** pole-zero network demonstrated (correct vs too-low vs none → datasheet Fig.3).
- ✅ **M2:** CR-210 demonstrably restores the baseline vs the un-restored case; populate-XOR
  (JU1) modeled; FOM tabulated + judged.

## Figures of merit (numbers)
**M1 — CR-200-1µs, single 0.5 pC CSP event, as-built P/Z = 51 k, ±12 V:**
| metric | value | datasheet | status |
|---|---|---|---|
| peak amplitude | 66.3 mV | — | gain ≈ 10.2 V/V (from 6.5 mV step) |
| **FWHM** | **2.50 µs** | **2.40 µs** (= 2.4·τ, τ=1 µs) | +4.2 %, within tol ✅ |
| peaking time (step→peak) | 2.50 µs | "1 µs region" | consistent w/ 4-pole shaper ✅ |
| undershoot | −0.22 % | ~0 with correct P/Z | ✅ |
| P/Z = none / 10 k (too low) | −4.9 % / +13.5 % | undershoot / overshoot (Fig.3) | reproduced ✅ |

**M2 — CR-200 → CR-210, 100 kHz pulse train:**
| metric | BLR OFF (JU1 short) | BLR ON (CR-210) | note |
|---|---|---|---|
| steady-state baseline | −17.3 mV (−25.7 % of peak) | −0.4 mV (−0.6 %) | **98 % droop removed** ✅ |
| per-pulse peak (early→late) | 67 → 51 mV (sinks) | 67 → 68 mV (held) | ✅ |
- The −25.7 % no-BLR droop matches the CR-200 datasheet formula S/H = R·τ·2.5e-6 = 25 % at
  100 kHz / 1 µs — independent cross-validation.

**Behavioral cross-check:** idealised CR-RC^4 vs Cremat model → **FWHM agreement 4.1 %**
(controlling metric); peaking time offset 19 % is expected (idealised equal-pole assumption).

## Engine + exact invocation
- **LTspice 24.1.9 batch** (headless ngspice unavailable). `LTspice.exe -netlist <model>.asc`
  → `make_subckts.py` → `.subckt`; `LTspice.exe -b -Run decks/<deck>.cir` → `.raw`; parsed by
  `scripts/ltspice_raw.py` (numpy) + matplotlib. **One-shot reproduce:** `bash scripts/run_all.sh`.

## Deliverables (what & where) — all under `chips-board/shaper-cr200-cr210/sim/`
- **Cremat official models** (downloaded 2026-06-25): `cremat-models/CR-200/CR-200-1us-R2.1.asc|.asy`,
  `cremat-models/CR-210/CR-210-R0.asc|.asy`; app guides `cremat-models/app-guides/CR-200-R2.1.pdf`,
  `CR-210-R0.pdf` (+ `.txt` extracts). Stimulus ref: `cremat-models/csp-ref-for-stimulus/CR-112-R2.1.pdf`.
- **Decks:** `decks/m1_cr200.cir`, `decks/m2_blr.cir`; portable subckts `decks/cr200_1us.sub`,
  `decks/cr210.sub`, `decks/models.inc`.
- **Scripts:** `scripts/{make_subckts,ltspice_raw,analyze_m1,analyze_m2,behavioral_crosscheck}.py`,
  `scripts/run_all.sh`.
- **Plots:** `plots/m1_cr200_gaussian.png`, `plots/m1_polezero_effect.png`,
  `plots/m2_baseline_restoration.png`, `plots/m2_pulse_detail.png`, `plots/crosscheck_behavioral.png`.
- **FOM data:** `data/m1_fom.json`, `data/m2_fom.json`, `data/crosscheck.json`.

## Interface I expose / consume
- **Verifies-by** (for `../INTERFACE.md`): CR-200-1µs shaper produces a Gaussian, FWHM 2.50 µs
  (spec 2.40), gain ≈ 10.2 V/V, undershoot <1 % with P/Z = **51 kΩ** (= Rf·Cf/Cin). With CR-210
  the baseline is restored to ground (≤0.6 % of peak) at 100 kHz; JU1 short = bypass (droops).
- **Topology assumed** (from `reference/cremat-CR-160-R7`): RP/Z across CR-200 pins 1↔2; CR-200
  out → {JU1 short = OUT} XOR {CR-210 → OUT}; CR-210 pin2 = GND. ±12 V supplies.
- **Consume:** A2 `csp-sim` CR-112 output waveform (stimulus) — see Open issues.

## How to use my output
The CR-200(+CR-210) sub-component meets its shaping/BLR specs in simulation with **P/Z = 51 kΩ**
and ±12 V; A4 design can adopt that P/Z value and the JU1 populate-XOR; B2 can chain my decks.

## Open issues / asks
- **A2 dependency (non-blocking):** I drove the shaper with a **representative** CR-112 CSP
  output (datasheet-exact: 6.5 mV step for 0.5 pC, decay τ = 51 µs). A2 has not yet published
  its CR-112 model output. Hand me A2's waveform in Round 2 and I will re-run; expected
  "no change" (both derive from the same CR-112 datasheet).
- **No CR-112 LTspice model on cremat.com** (only CR-110/111/113 published) — flag for A2/A3.
- **A6 real-parts gate:** only the **P/Z resistor (51 k)** is value-sensitive to my FOM; supply
  decoupling values are DC-irrelevant to the transient FOM → will note "no change."
- No login-gated models needed; all Cremat models fetched successfully.
