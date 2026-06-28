# Session Log — B2 chan-sim

> **Ground truth, append-only.** One dated entry per working session.

Track: `B2 chan-sim` · Sub-component: `single-channel` · Aspect: `sim`
Reads (inputs): A2 `chips-board/csp-cr112/sim/SESSION_REPORT.md` + `cr11x_csp.cir`;
A5 `chips-board/shaper-cr200-cr210/sim/SESSION_REPORT.md` + `decks/{cr200_1us.sub,
cr210.sub,m1_cr200.cir,m2_blr.cir}`; `reference/cremat-CR-160-R7` (EL5167 app circuit);
Renesas/Intersil FN7365 (EL5166/67 datasheet); 00-CHARTER, 01-CONVENTIONS §5, B brief.
Success criteria (mirror of report): end-to-end response consistent with the A2/A5
standalone sims (gains compound, peaking time preserved, no instability); state the
expected OUT_50 peak for 0.5 pC into 50 Ω and confirm it; per-stage plots + FoM table.

---

## 2026-06-25 — session 1 — full chain CR-112→CR-200→CR-210→EL5167, end-to-end

**Goal this session:** chain the proven Phase-A models + add the EL5167 CFA buffer;
inject 0.5 pC at the CSP, load OUT_50 with 50 Ω; plot every stage; confirm the
expected OUT_50 peak.

**Did:**
- Read A2 + A5 reports/decks; confirmed both Phase-A sub-components COMPLETE/criteria-met.
- Built `integration/single-channel/sim/` tree (decks/ scripts/ data/ plots/ models/).
- Re-used Phase-A artifacts (copied read-only into decks/): `cr200_1us.sub`, `cr210.sub`,
  `models.inc` (Cremat official CR-200-1µs + CR-210-R0 LTspice models, via A5); the LTspice
  `.raw` reader `scripts/ltspice_raw.py` and the OneDrive-path-safe batch runner.
- Wrapped A2's CR-112 internal model as a subckt: `decks/cr112_csp.sub` (Cf=75p, Rf=680k,
  Cin=15p, G2=1 → 13.3 mV/pC, τ=51 µs, ~3 ns rise; same topology as A2 `cr11x_csp.cir`).
- **EL5167 buffer model:** searched renesas.com — the EL5167 product page exposes ONLY the
  datasheet; no public SPICE/PSpice (any SPICE is behind the login-gated EDA portal). Per
  §5 fallback, built a datasheet-anchored CFA behavioral macromodel `decks/el5167_cfa.sub`
  from FN7365 Rev 6.00: ROL(transimpedance)=1.1 MΩ, Rin(+)=130k, Cin=1.5p, SR=6000 V/µs,
  Iout=±160 mA typ, Vos=−0.5 mV, recommended Rf=392 (AV=1)/250 (AV=2), BW 1.4 GHz(G1)/
  800 MHz(G2). Got the EL5167 application circuit from Cremat's own `reference/cremat-CR-160-R7`
  netlist (U2=EL5167: R5=390 fb, R6=43 gain → AV≈10; output 49.9 Ω back-term in the x6 board).
  Chose **buffer default AV=+2 (Rf=250, Rg=250)** pending B1; one .param line to change.
- Wrote `decks/chain_single_event.cir` (0.5 pC impulse → full chain → 49.9 Ω → 50 Ω load),
  `analyze_chain.py` (FoM + 4 plots), and ran via `scripts/run_ltspice.ps1` (stages whole
  decks/ to C:\Temp, copies .raw back — OneDrive space-path quirk).

**Results (FoM, 0.5 pC single event, polarity-corrected canonical deck):**
| stage | peak | peaking | FWHM | vs standalone |
|---|---|---|---|---|
| CSP_OUT | −6.445 mV | — | — | A2 −6.66 mV (−3%, P/Z loads the CSP out) |
| SHOUT (CR-200) | −67.16 mV (×10.42) | 2.44 µs | 2.53 µs | A5 −66.3 mV ×10.19, 2.50 µs ✓ |
| BLR_OUT (CR-210) | +67.03 mV (×0.998) | 2.47 µs | 2.53 µs | restorer passband ≈ unity ✓ |
| BUF_OUT (EL5167) | +133.98 mV (×1.999) | 2.47 µs | 2.53 µs | AV=2 exact ✓ |
| **OUT_50 (50 Ω)** | **+67.06 mV** (×0.501) | 2.47 µs | 2.53 µs | 50/50 back-term = 0.5 ✓ |
- Injected charge integrated = 0.5000 pC (target). charge→OUT_50 = 134 mV/pC.
- **Expected OUT_50 = 0.5pC×13.3mV/pC ×10.2 ×1.0 ×2 ×0.5 = 67.9 mV; simulated 67.1 mV (−1.2%). CONFIRMED.**

**Decisions & why:**
- **No `uic`** in the decks: with `uic` the level2 op-amp macromodels in the Cremat models
  ring for ~1 µs at start-up (SHOUT jumped to +346 mV at t=10 ns and was still +52 mV at the
  t=1 µs event), contaminating the response. Solving the DC operating point first (Gmin
  stepping succeeds) makes every node start settled at 0. A5's decks likewise avoid uic.
- **maxstep 2 ns + `.options plotwinsize=0`** (no waveform compression) to resolve the 3 ns
  CSP rise and the 2.5 µs shaper peak; the first coarse run gave only 182 points.

**Dead-ends / surprises:**
- **CR-210 polarity (the integration finding).** The real CR-112 is INVERTING → the shaped
  pulse reaching the CR-210 is NEGATIVE. The Cremat CR-210 is a *unipolar* baseline restorer
  validated (A5 M2) for a POSITIVE pulse; fed the negative pulse it MIS-restores — in the
  100 kHz train the baseline climbed to +69.5 mV (≈100% of peak) instead of being held at 0.
  Verified by regenerating A5's M2 raw: A5 fed the CR-210 +68 mV and got a +1.46 mV restored
  baseline. Resolution = the channel must present the CR-210 the polarity it restores
  (positive), as the CR-160-R7 reference does. Modeled with a unity inverter (POL=−1) between
  shaper and AC-coupling cap → `chain_pulse_train_pol.cir` and applied to the canonical
  single-event deck. With POL=−1: 100 kHz train holds OUT_50 peak 68.4→67.5 mV (1.4% droop)
  and baseline −0.8 mV (−1.2% of peak) — matches A5 M2 (−0.43 mV). **Flag to B1 design.**
- The project's `ltspice_raw.py` is transient-only (real data); it does not parse complex
  `.ac` raw → judged buffer stability from a fast transient step instead (see below).

**State vs criteria:** ALL MET. Gains compound (×10.42 ×0.998 ×1.999 ×0.501), peaking time
preserved (2.44→2.47 µs), no instability (buffer step: 0% overshoot, 0 ringing sign changes;
single-event tail 0 sign changes; 30-pulse train smooth). Expected OUT_50 stated + confirmed.

**Next:** Round 2 — if B3 picks a different real buffer op-amp or B1 sets a different gain,
re-run with the new AV/Rf (single .param line) and re-check FoM. Else "no change."

**Stability check:** `decks/buffer_ac.cir` (fast 1 ns step into the AV=2 buffer) → BUF_OUT
settles 0.1989 V (=2×0.1−2×Vos), OUT_50 0.0995 V (÷2 back-term), 0.00% overshoot, 0 ringing.

**Pulse-train BLR proof:** `chain_pulse_train_pol.cir` (corrected) baseline −0.8 mV/−1.2%;
`chain_pulse_train.cir` (raw polarity) baseline +69.5 mV/+99.8% — `analyze_train.py`,
plot `plots/chain_train_baseline.png`, FoM `data/chain_train_fom.json`.

---

## 2026-06-28 — session 2 — round-2 buffer swap to TI THS3491

**Goal this session:** coordinator decision — output buffer = **TI THS3491** (HV CFA, ±12 V
direct, 900 MHz, 8000 V/µs, ~520 mA), replacing the EL5167 behavioral model. (1) update the
buffer to THS3491; (2) make the corrected-polarity chain the deck of record, drop the
mis-polarity case to a note; (3) re-run and confirm OUT_50 ≈ 67 mV, per-stage FoM preserved,
no instability.

**Did:**
- Fetched the THS3491 datasheet (TI SBOS875C): 900 MHz SSBW, 320 MHz LSBW, SR 8000 V/µs, ZOL
  8 MΩ, Iout 520 mA (linear 420 mA), Zout 0.17 Ω DC / 1 Ω @ 50 MHz, supply ±15 V test,
  Cin 1.5 pF, recommended Rf = **976 Ω for G=2** (RGT). Saved `models/THS3491/THS3491_datasheet.pdf`+`.txt`.
- **TI publishes the SPICE model with NO login** — downloaded SBOMBP9 (PSpice), SBOMAI5A
  (TINA DDA), SBOMAN4 (TINA RGT) from ti.com/lit/zip. Used `THS3491RGT.lib` (SBOMAN4) →
  copied to `decks/ths3491_rgt.lib`. Ports: `INP INN FB OUT PD_not VCC VEE GND` (FB tied to
  OUT by a 1 µΩ internal trace; external Rf goes FB→INN; PD_not held high to enable).
- Verified the TI model runs in LTspice with `decks/ths3491_test.cir` (gain +2, 50 Ω back-term):
  OUTX 102.9 mV / OUT_50 51.5 mV for a 50 mV step → AV≈2, 0% overshoot. One benign warning
  (`d_in_clmp N=0.02 too small`). So I use TI's REAL model in the chain, not a behavioral one.
- Swapped the buffer in `chain_single_event.cir` (deck of record), `chain_pulse_train_pol.cir`
  (corrected, deck of record), `chain_pulse_train.cir` (now headed "DOCUMENTED NOTE ONLY"),
  and `buffer_ac.cir` to the THS3491 (Rf=Rg=976, PD_not=high, GND pin → 0). Relabeled the
  analyze script + run_all step "EL5167"→"THS3491". Re-ran `scripts\run_all.ps1` (all exit 0).

**Results (THS3491, 0.5 pC single event, deck of record):**
| stage | peak | peaking | FWHM | round-1 (EL5167) |
|---|---|---|---|---|
| CSP_OUT | −6.445 mV | — | — | −6.445 (same path) |
| SHOUT | −67.16 mV (×10.42) | 2.44 µs | 2.53 µs | −67.16 (same) |
| BLR_OUT | +66.99 mV (×0.997) | 2.47 µs | 2.53 µs | +67.03 |
| BUF_OUT | +133.86 mV (×1.998) | 2.47 µs | 2.53 µs | +133.98 |
| **OUT_50** | **+67.00 mV** (×0.501) | 2.47 µs | 2.53 µs | +67.06 |
- charge→OUT_50 = 134.0 mV/pC. **Expected 67.9 mV (0.5pC×13.3×10.2×1×2×0.5); simulated 67.00 mV (−1.3%). CONFIRMED.**
- THS3491 swap moved OUT_50 by 0.1% vs EL5167 → **no FoM change** (buffer far in-band, as predicted).
- Train (corrected = deck of record): peak 68.4→67.5 mV (1.4% droop), baseline −0.65 mV (−0.96% of peak) — matches A5 M2.
- Train (uncorrected, note): baseline +69.6 mV (mis-restore) — reproduces the polarity finding.
- Stability (`buffer_ac.cir`, THS3491): BUF_OUT 136.9 mV / OUT_50 68.5 mV for a 67 mV/100 ns step, 0% overshoot, 0 sustained ringing → STABLE.

**Decisions & why:**
- Used TI's **official** THS3491RGT SPICE model (runs in LTspice) instead of a behavioral
  model — better fidelity, vendor-sourced, no login needed.
- Rf = 976 Ω (TI's datasheet G=2 recommended value) for AV=+2; Rg=976.
- A small DC offset appears at BUF_OUT (+3 mV) from the THS3491 input bias current × 976 Ω fb;
  harmless for the pulse FoM (the CR-210 / AC path handles DC; peaks are baseline-referenced).

**Dead-ends / surprises:** none — the TI model converged first try. Noted TI's model header
caveat (validated at ±15 V; we run ±12 V) — in-band FoM unaffected, only swing headroom scales.

**State vs criteria:** ALL MET (round 2). FoM unchanged from round 1 within 0.1%; OUT_50 67 mV
confirmed; peaking time preserved; stable; deck-of-record = corrected polarity.

**Next:** Phase-B integration consistency with B1/B3. If B1 changes buffer gain, one .param re-run.
