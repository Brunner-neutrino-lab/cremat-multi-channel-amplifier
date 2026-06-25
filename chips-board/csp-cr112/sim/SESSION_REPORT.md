# Session Report — A2 csp-sim

> **The summary other tracks read instead of my log.** Keep current (overwrite). A
> consumer must be able to integrate from this + `INTERFACE.md` alone.

Track: `A2 csp-sim` · Aspect: `sim` · Status: `criteria-met`
Last updated: `2026-06-25`

## Objective
Simulate the Cremat **CR-112 CSP** for an ideal **0.5 pC** charge impulse and verify the
`CSP_OUT` figures of merit against the datasheet (gain ≈ 13 mV/pC → ~6.5 mV step, ~3 ns
rise, ~50 µs decay). Produce a reusable `CSP_OUT` waveform = the **shaper track's stimulus**.

## Success / failure criteria (stated before work)
- ✅ `CSP_OUT` step ≈ 6.5 mV (0.5 pC × 13 mV/pC) within ~20 % → **measured 6.66 mV (+2.5 %)**.
- ✅ Rise time 10–90 % ≈ 3 ns (datasheet, zero added input cap) → **3.36 ns**.
- ✅ Decay single-exponential τ ≈ 50 µs (Rf·Cf = 680k·75p = 51 µs) → **51.0 µs (exact)**.
- ✅ Model stable, no oscillation; polarity inverting (CSP) → **negative step, clean decay**.
- ✅ Primary source = Cremat's official model (not a hand model); behavioral cross-check
  agrees → **SPICE vs behavioral peak agree to 0.01 %**.
- ✅ Topology faithfulness validated: same netlist with CR-110 values reproduces CR-110's
  own datasheet → **gain 1.42 V/pC vs ds 1.4; τ 140.5 µs vs ds 140**.

## Current state
**ALL CRITERIA MET (Phase A, round 1).** CR-112 simulated; FoM match datasheet within model
tolerance; behavioral cross-check confirms; CR-110 validation confirms topology fidelity.

### Figures of merit (CR-112, 0.5 pC ideal impulse)
| metric | simulated | datasheet | delta |
|---|---|---|---|
| charge gain | 13.33 mV/pC | 13 mV/pC | +2.5 % |
| peak amplitude | −6.66 mV | ~6.5 mV | +2.5 % |
| rise time (10–90 %) | 3.36 ns | ~3 ns | within tol |
| decay τ | 51.0 µs | ~50 µs | exact (Rf·Cf) |
| output impedance | 50 Ω (by R3) | 50 Ω | match |
| polarity | inverting (−) | inverting | match |

## Model provenance & engine
- **No native CR-112 LTspice model exists** on cremat.com — Cremat ships LTspice models only
  for CR-110/111/113. The four CR-11X parts share **one internal topology**; they differ
  only in Cf/Rf/Cin/GBW. I re-expressed Cremat's official **CR-110-R2** model as a portable
  SPICE netlist and retargeted the feedback to the **CR-112 datasheet (Cf=75 pF, Rf=680 kΩ)**.
  Downloaded models + datasheets: `cremat-models/CR-{110,111,112,113}/` (source: cremat.com,
  retrieved 2026-06-25; URLs in `SESSION_LOG.md`).
- **Engine: LTspice 24.1.9 batch** (headless ngspice is unavailable on this box).
  Exact invocation: `LTspice.exe -b -Run <deck>.net` → `.raw`, parsed with numpy
  (`analyze.py`). NOTE: LTspice batch silently fails to write outputs into the OneDrive
  working path (spaces) — `run_ltspice.ps1` stages the deck in `C:\Temp` and copies the
  `.raw` back. Reproduce: `powershell -File run_ltspice.ps1 cr11x_csp; python analyze.py cr11x_csp`.

## Deliverables (what & where, all under `chips-board/csp-cr112/sim/`)
- `cr11x_csp.cir` — CR-112 deck (the result-of-record). `cr110_validate.cir` — validation deck.
- `analyze.py` — .raw reader + FoM + plots. `behavioral_crosscheck.py` — independent model.
- `run_ltspice.ps1` — batch runner (handles the OneDrive-path quirk).
- Plots: `plots/cr11x_csp_csp_out.png` (rise + decay), `plots/cr11x_csp_input_charge.png`
  (0.5 pC verification), `plots/behavioral_overlay.png` (SPICE vs analytic).
- **Reusable waveform → shaper stimulus:** `data/cr11x_csp_csp_out.csv`
  (CSV, 2 cols: `time_s,csp_out_V`, ~5.9k pts, 0–300 µs). FoM: `data/cr11x_csp_fom.csv`.
- Cremat models/datasheets + extracted text: `cremat-models/`.

## Interface I expose / consume
- **Expose:** the CR-112 `CSP_OUT` transient for 0.5 pC: negative step −6.66 mV, ~3.4 ns
  rise, τ=51 µs decay. Waveform file `data/cr11x_csp_csp_out.csv`. (Per the sub-component
  INTERFACE, `CSP_OUT` is voltage; step ≈ Q×13 mV/pC + CR-112 decay tail; Zout 50 Ω.)
- **Consume:** A1 design topology (input/coupling network — only its added input capacitance
  Cin would move the rise time, at 0.13 ns/pF); A3 real parts (the CR-112 internal feedback
  is fixed inside the module, so the FoM are not expected to move).

## How to use my output
**Shaper sim (Phase B / A5):** feed `data/cr11x_csp_csp_out.csv` as the shaper input
stimulus (it is the CR-112 model output for 0.5 pC) — `time_s,csp_out_V`, a PWL-ready table.

## Open issues / asks
- Native CR-112 LTspice model does not exist (CR-110/111/113 only). If you want the literal
  unmodified Cremat model exercised, the CR-110 `.asc` is at
  `cremat-models/CR-110/extracted/CR-110-R2.asc` (openable in LTspice GUI); `cr110_validate.cir`
  reproduces its published specs. No download was blocked/login-gated — all fetched OK.
- Real-parts gate: expect **"no change"** to the FoM (CR-112 feedback is internal/fixed).
  Only an A1 input network adding significant Cin would slow the rise time (0.13 ns/pF).
