# Session Report — B2 chan-sim

> **The summary other tracks read instead of my log.** Keep current (overwrite). A
> consumer must be able to integrate from this + `INTERFACE.md` alone.

Track: `B2 chan-sim` · Aspect: `sim` · Status: `criteria-met (round 2: THS3491 buffer)`
Last updated: `2026-06-28`

## Objective
Simulate the **full single channel end-to-end** — CR-112 CSP → CR-200-1µs shaper →
CR-210 BLR → **TI THS3491 CFA output buffer** — for an ideal **0.5 pC** charge impulse,
with `OUT_50` loaded by **50 Ω**. Reuse the proven Phase-A models; plot every stage;
confirm the chain is consistent with the A2/A5 standalone sims and state + confirm the
expected `OUT_50` peak.

## Round 2 (2026-06-28) — output buffer = TI THS3491
Per the coordinator the output buffer is the **TI THS3491** HV CFA (±12 V direct, 900 MHz
SSBW, 8000 V/µs, ~520 mA Iout), replacing the round-1 EL5167 behavioral model. **Used TI's
OFFICIAL SPICE model** — `THS3491RGT.lib` (SBOMAN4, downloaded from ti.com, **no login**),
which runs natively in LTspice. As predicted (the buffer is far in-band for the 2.5 µs pulse),
the FoM are unchanged vs round 1. The corrected-polarity chain is the **deck of record**; the
mis-polarity case is kept only as a documented note.

## Success / failure criteria (stated before work)
- ✅ End-to-end response consistent with the sub-component sims (gains compound; peaking
  time preserved). **CSP −6.45 mV (A2 −6.66), shaper ×10.42 (A5 ×10.19), peaking 2.44→2.47 µs
  (A5 2.50), FWHM 2.53 µs (A5 2.50).**
- ✅ `OUT_50` amplitude into 50 Ω as expected, **explicitly stated and confirmed**: expected
  **67.9 mV** (= 0.5 pC × 13.3 mV/pC × 10.2 × 1.0 × 2 × 0.5); **simulated 67.00 mV (−1.3%).**
- ✅ No instability / oscillation: THS3491 buffer step 0.00% overshoot, 0 sustained ringing;
  single-event tail smooth; 30-pulse train smooth + baseline-restored.
- ✅ Buffer drives 50 Ω: THS3491 Iout ~520 mA ≫ the ~1.4 mA needed; 49.9 Ω back-term gives
  Zout = 50 Ω and the exact 0.501 divider into the 50 Ω load.
- ✅ Per-stage plots + figures-of-merit table produced.

## Current state
**ALL CRITERIA MET (Phase B, round 2, TI THS3491 official model).** Full chain simulated;
FoM compound correctly and match A2/A5 within model tolerance; CR-210 baseline restoration
confirmed at rate (after the polarity convention — see Open issues); buffer stable into 50 Ω.

### Figures of merit — 0.5 pC single event (DECK OF RECORD, polarity-corrected, THS3491)
| stage | peak | gain vs prev | peaking time | FWHM |
|---|---|---|---|---|
| CSP_OUT (CR-112) | −6.45 mV | — (13.3 mV/pC) | — | — |
| SHOUT (CR-200) | −67.16 mV | ×10.42 | 2.44 µs | 2.53 µs |
| BLR_OUT (CR-210) | +66.99 mV | ×0.997 (passband) | 2.47 µs | 2.53 µs |
| BUF_OUT (THS3491) | +133.86 mV | ×1.998 (AV=2) | 2.47 µs | 2.53 µs |
| **OUT_50 (into 50 Ω)** | **+67.00 mV** | ×0.501 (back-term ÷2) | 2.47 µs | 2.53 µs |
- Overall chain charge→OUT_50 = **134 mV/pC** → **67.00 mV for 0.5 pC** (expected 67.9, −1.3%).
- Injected charge verified = 0.5000 pC. Polarity at OUT_50 = positive (unipolar pulse).
- Round-1 (EL5167 behavioral) gave OUT_50 67.06 mV → **THS3491 swap moved it by 0.1%** (in-band).

### Baseline restoration (100 kHz train, full chain, THS3491)
| | corrected polarity = **deck of record** | raw CR-112 polarity (documented note) |
|---|---|---|
| OUT_50 peak first→last | 68.4 → 67.5 mV (1.4% droop) | drifts (mis-restore) |
| steady baseline | **−0.65 mV (−0.96% of peak)** | +69.6 mV (+99.8%) |
→ corrected case matches A5 M2 (−0.43 mV / 98% droop removed).

## Model provenance & engine
- **Chained models (reused, read-only):** A2 CR-112 internal model (`cr112_csp.sub`, = A2's
  `cr11x_csp.cir` topology); Cremat **official** CR-200-1µs + CR-210-R0 LTspice models via A5
  (`cr200_1us.sub`, `cr210.sub`, `models.inc`).
- **Buffer = OFFICIAL TI THS3491 SPICE model** (`ths3491_rgt.lib`, = TI SBOMAN4
  `THS3491RGT.lib`, downloaded 2026-06-28 from ti.com, no login). Runs natively in LTspice
  (one benign clamp-diode emission-coefficient warning). TI model header notes it targets
  ±15 V; on the board's ±12 V the in-band gain/BW/slew used here are unaffected. Datasheet
  SBOS875C: 900 MHz SSBW, 320 MHz LSBW, 8000 V/µs, ZOL 8 MΩ, Iout 520 mA, recommended
  Rf = 976 Ω for G=2 (used). Round-1 EL5167 behavioral model (`el5167_cfa.sub`) retained as a
  superseded cross-check artifact.
- **Engine: LTspice 24.1.9 batch.** Invocation: `LTspice.exe -b -Run <deck>.net` → `.raw`,
  parsed with numpy (`scripts/ltspice_raw.py`). The runner stages the whole `decks/` dir to
  `C:\Temp` and copies the `.raw` back (LTspice batch fails on the OneDrive space-path).
  **One-shot reproduce:** `powershell -File scripts\run_all.ps1`.

## Deliverables (what & where) — all under `integration/single-channel/sim/`
- **Decks:** `decks/chain_single_event.cir` (DECK OF RECORD, per-stage FoM),
  `decks/chain_pulse_train_pol.cir` (DECK OF RECORD, BLR proof, corrected polarity),
  `decks/chain_pulse_train.cir` (documented note: raw-polarity mis-restore),
  `decks/buffer_ac.cir` (buffer stability), `decks/ths3491_test.cir` (TI-model standalone check).
  Subckts/libs: `decks/{cr112_csp,cr200_1us,cr210}.sub`, `decks/ths3491_rgt.lib`,
  `decks/el5167_cfa.sub` (superseded), `decks/models.inc`.
- **Scripts:** `scripts/{analyze_chain,analyze_train,ltspice_raw}.py`, `scripts/{run_ltspice,run_all}.ps1`.
- **Plots:** `plots/chain_per_stage.png`, `plots/chain_normalised_overlay.png`,
  `plots/chain_out50_detail.png`, `plots/chain_input_charge.png`, `plots/chain_train_baseline.png`.
- **FoM data:** `data/chain_fom.json`, `data/chain_fom.csv`, `data/chain_train_fom.json`.
- **Buffer model + datasheet:** `models/THS3491/` (TI SPICE zips SBOMAN4/SBOMAI5A/SBOMBP9 +
  extracted `.lib`, datasheet `THS3491_datasheet.pdf` + `.txt`); `models/EL5167/` (round-1 datasheet).

## Interface I expose / consume
- **Verifies-by** (for `../INTERFACE.md`): the single channel delivers **+67 mV at OUT_50 for
  0.5 pC into 50 Ω** (≈134 mV/pC charge gain), peaking time **2.47 µs**, FWHM **2.53 µs**, Zout =
  **50 Ω** (49.9 Ω back-term), stable, with the CR-210 restoring the baseline to ≤1% of peak at
  100 kHz. Per-stage gain chain ×10.42 (shaper) ×0.997 (BLR) ×1.998 (THS3491 AV=2) ×0.501.
- **Consume:** A2 CR-112 model + 0.5 pC stimulus; A5 CR-200/CR-210 models + P/Z=51 k; B3's
  buffer BOM (THS3491 + Rf/Rg) and B1's topology/polarity.

## How to use my output
**B1/Phase-C:** the proven channel transfer is ≈**134 mV/pC** to a 50 Ω load with a 2.5 µs
peaking pulse; set the buffer gain via the single `AVgain`/`Rfb` .param in the chain decks
(currently AV=+2, Rf=Rg=976 Ω per TI's G=2 table).
**B1 action item:** ensure the channel presents the CR-210 a **positive** shaped pulse (it is a
unipolar restorer); the CR-112→CR-200 path is net inverting, so a polarity convention is
needed (handled in sim by POL=−1).

## Open issues / asks
- **CR-210 polarity is an integration item for B1** (see How to use my output). Not a sim
  failure — the BLR works correctly once fed its design polarity (confirmed vs A5 M2).
- **THS3491 model validated for ±15 V** per TI's header; the board runs ±12 V. In-band FoM are
  unaffected (gain/BW/slew far exceed the signal); only the absolute output-swing headroom
  scales with the rails (ample for the ≤±0.2 V signals here).
- **Round-2 gate satisfied.** If B1 changes the buffer gain, re-run with one `.param` line
  (OUT_50 scales linearly with gain; THS3491 50 Ω drive margin is enormous, ~520 mA).
- Tooling: `ltspice_raw.py` parses transient only (not complex `.ac`) — buffer stability was
  judged from a transient step (clean, no ringing) instead of a Bode plot.
