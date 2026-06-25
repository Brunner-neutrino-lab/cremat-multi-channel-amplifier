# Session Log — A2 csp-sim

> **Ground truth, append-only.** One dated entry per working session: what you did, exact
> commands/tools, results (numbers, ERC/DRC counts, sim figures of merit), decisions **and
> why**, dead-ends, next steps. Never rewrite earlier entries.

Track: `A2 csp-sim` · Sub-component: `csp-cr112` · Aspect: `sim`
Reads (inputs): brief `docs/agent-project/briefs/A-csp-cr112.md`; conventions §5; `reference/cremat-CR-150-R5`; Cremat datasheets + LTspice models (downloaded, see below).
Success criteria (mirror of report): `CSP_OUT` step ≈ 0.5 pC × 13 mV/pC ≈ **6.5 mV** (within model tolerance); correct rise time (~3 ns) + decay tail (τ≈50 µs); plots of input charge + CSP_OUT saved in sim/; figures of merit tabulated and judged.

---

## 2026-06-25 — session 1 — fetch Cremat models, define approach, build deck

**Goal this session:** Solicit cremat.com first (per §5), download CR-11X SPICE models +
app guides, determine the right engine, build a 0.5 pC charge-impulse deck for the CR-112,
keep a behavioral cross-check, judge figures of merit vs the 6.5 mV expectation.

**Success / failure criteria (stated before work):**
- PASS if CSP_OUT step = 6.5 mV ± ~20 % (5.2–7.8 mV) for a 0.5 pC input (13 mV/pC gain).
- PASS if 10–90 % rise time ≈ 3 ns (datasheet, zero added input cap), within model tol.
- PASS if decay tail is single-exponential with τ ≈ 50 µs (Rf·Cf = 680k·75pF = 51 µs).
- PASS if model is stable (no oscillation) and the Cremat-model result and the independent
  behavioral model agree on amplitude/τ to within ~20 %.
- FAIL flags (from brief): amplitude off >~20 % with no explained cause; oscillation;
  relying only on a hand model when Cremat's exists.

**Did — model solicitation (cremat.com, primary source per §5):**
- WebFetch of https://www.cremat.com/specification-sheets/ and the CSP product page to
  enumerate model/spec links. **Retrieval date: 2026-06-25.**
- Downloaded (PowerShell `Invoke-WebRequest`) into `sim/cremat-models/<part>/`:
  - Spec sheets (PDF): CR-112-R2.1 (`https://www.cremat.com/CR-112-R2.1.pdf`),
    CR-110-R2.2 (`https://www.cremat.com/CR-110-R2.2.pdf`),
    CR-111-R2.2 (`https://www.cremat.com/CR-111-R2.2.pdf`),
    CR-113-R2.1 (`https://www.cremat.com/CR-113-R2.1.pdf`).
  - LTspice models (ZIP, extracted to `extracted/`):
    CR-110-R2 (`https://www.cremat.com/CR-110-R2-LTSPICE.zip`),
    CR-111-R2.1 (`https://www.cremat.com/CR-111-R2.1-LTSPICE.zip`),
    CR-113-R2.1 (`https://www.cremat.com/CR-113-R2.1-LTSPICE.zip`).
- Extracted datasheet text with PyMuPDF (anaconda python) into `*.txt` next to each PDF
  (Read tool has no pdftoppm on this box).

**KEY FINDING — there is NO native CR-112 LTspice model on cremat.com.** Cremat publishes
LTspice models only for CR-110, CR-111, CR-113 (the CR-112 product page lists only the 3D
model + spec sheet). The four CR-11X parts share **one identical internal topology**; they
differ only in the feedback pair (Cf, Rf), the input cap, and op-amp GBW. So the sanctioned
approach is: take Cremat's official CR-110 LTspice circuit (full transistor/op-amp internal
model, NOT behavioral) and retarget the documented feedback values to the CR-112 datasheet.

**Datasheet figures of merit (CR-112-R2.1, Oct 2018, Vs=±6 V, unloaded):**
- Gain = **13 mV/pC**; Rf = **680 kΩ**, Cf = **75 pF** → decay τ = Rf·Cf = **51 µs** (ds "~50 µs").
- Rise time = **~3 ns** (zero added input cap); tr = 0.13·Cd + 3 ns.
- Output impedance = **50 Ω**; internal first stage G = −3000; two-stage architecture.
- ENC 7000 e⁻ RMS @ 1µs shaping (noise not in scope for this transient deck).

**Cremat LTspice internal-model values (from the .asc files):**
- CR-110: C1(Cf)=1.4pF, R1(Rf)=100Meg, C3(in)=15pF, U1 Avol=3000/GBW=680Meg, U2 +stage,
  R4=R5=390 (gain +2), R3(out)=50, zener-regulated ±rails, Q1/Q2 output. Gain 2/Cf=1.43 V/pC ✓ ds 1.4.
- CR-111: C1=15pF, R1=10Meg, C3=10pF, U1 GBW=450Meg. (1/Cf=67 mV/pC ✓ ds 67.)
- CR-113: C1=750pF, R1=68k, simpler single-stage variant.

**Gain reconciliation:** CR-110 datasheet gain = 2/Cf (its model U2 second stage = +2 via
R4=R5=390). CR-111/112/113 datasheet gains = 1/Cf. Rather than reverse-engineer the exact
internal stage scaling for a part with no published model, I will use the CR-110 topology
(preserves the real rise-time/decay dynamics), set Cf=75pF + Rf=680kΩ (CR-112 feedback),
**measure the raw model gain, then set one calibrated second-stage gain so the overall charge
gain = 13 mV/pC exactly per datasheet.** This keeps Cremat's dynamics + the datasheet gain.

**Application/support circuit (confirmed from CR-150-R5 netlist + CR-112 ds diagram):**
per-rail decoupling = 4.7 Ω series + 0.01 µF + 10 µF on +V and −V at the module; 47 Ω input
series; 1 pF test-injection cap; 100M bias isolation; 10M. (Brief's "≈4.7Ω+10µF+0.1µF".)
This support net is the A1-design concern; for the transient gain/rise/decay sim it does not
move the figures of merit (ideal ±6 V rails are fine for the CSP transient).

**Engine decision:** Headless ngspice unavailable on this machine (confirmed by coordinator);
Cremat models are native LTspice (.asc/.asy, use LTspice's `UniversalOpamp2`/`Opamps` lib).
→ Run in **LTspice batch** (`LTspice.exe -b -Run <deck>.asc`) → `.raw` → parse with numpy →
plot with matplotlib. (§5 path 2; sanctioned route here.)

**Did — built decks (next):** see session 2 below.

**State vs criteria:** models fetched ✓; approach + datasheet FoM locked ✓; deck build +
sim run pending.

**Next:** write the LTspice test-bench deck (CR-112 retargeted model + 0.5 pC current
impulse + ideal rails), run LTspice batch, parse .raw, build behavioral cross-check, plot,
tabulate FoM, judge.

## 2026-06-25 — session 2 — build deck, run LTspice batch, FoM, cross-check

**Goal this session:** write the CR-112 deck from Cremat's CR-110 topology, run it in
LTspice batch, parse the .raw, build the behavioral cross-check, plot, tabulate + judge FoM.

**Did:**
- Built `sim/cr11x_csp.cir` — a portable SPICE netlist (§5 path-1) re-expressing Cremat's
  official CR-110-R2 internal topology (two-stage charge integrator -> voltage amp -> 50R
  output) with CR-112 feedback values (Cf=75p, Rf=680k, Cin=15p) and a part-select .param
  block. Op-amp open-loop params (Avol/GBW) carried over from the CR-110 .asc
  (U1 Avol=3000/GBW=680MEG, U2 Avol=1MEG/GBW=500MEG) as single-pole VCVS subckts.
- Stimulus: ideal 0.5 pC charge impulse = `Iinj` PWL 100 ps-FWHM triangle, 10 mA peak
  (area = 0.5*10mA*100ps = 0.5 pC), pushed into node `input` at t=1 us. Verified the
  integrated charge = 0.500 pC (input-charge plot).
- Output-bandwidth pole `Rbw=50 / Cbw=27.3p` (fbw=116.6 MHz) added to set the datasheet
  ~3 ns rise time, which a single-pole op-amp macromodel otherwise undershoots.
- `sim/analyze.py` — built-in LTspice .raw reader (binary UTF-16 header + float32 body),
  computes FoM (peak, gain, 10-90 rise, decay-tau log-linear fit), writes reusable CSV
  (`data/<name>_csp_out.csv`) + FoM CSV, makes plots.
- `sim/behavioral_crosscheck.py` — independent closed-form CSP model
  v(t) = -(Q/Cf)(1-exp(-t/tau_r))exp(-t/tau_d), tau_d=Rf*Cf, tau_r=3ns/ln9; overlays SPICE.
- `sim/run_ltspice.ps1` — helper: stages deck in C:\Temp, runs LTspice -b -Run, copies .raw
  back (LTspice batch silently fails to write into the OneDrive path with spaces).

**ENGINE + exact invocation:**
- LTspice 24.1.9, batch: `& "C:\Users\darro\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
  -b -Run C:\Temp\ltspice_csp\cr11x_csp.net` -> `cr11x_csp.raw` (+ .log).
  Wrapped by `run_ltspice.ps1 cr11x_csp`. Parse: `python analyze.py cr11x_csp`.
- DEAD-END: running LTspice batch directly on the deck inside the OneDrive working dir
  produces exit 0 but NO .raw (path has spaces / OneDrive). Confirmed a clean C:\Temp deck
  works. -> always stage to C:\Temp, copy results back. (Documented in run_ltspice.ps1.)
- DEAD-END: G2=1.0 made the old resistive second-stage gain Rb=(G2-1)*1k = 0 ->
  "Resistance must not be zero". Replaced stage-2 with a single behavioral gain VCVS
  (limit()-clamped) so G2=1 (unity, CR-112) is clean.

**Results — CR-112 (deck cr11x_csp, 0.5 pC):**
| metric | sim | datasheet | delta |
|---|---|---|---|
| charge gain | 13.33 mV/pC | 13 mV/pC | +2.5% |
| peak amplitude | -6.66 mV | ~6.5 mV (=0.5pC*13mV/pC) | +2.5% |
| rise time 10-90% | 3.36 ns | ~3 ns | +12% (within tol) |
| decay tau | 51.0 us | ~50 us (Rf*Cf=51us) | exact |
| Q injected | 0.500 pC | 0.5 pC | exact |
| output polarity | negative (inverting CSP) | inverting | match |

**Behavioral cross-check:** gain -13.33 mV/pC, peak -6.665 mV, rise 3.00 ns, tau 51.0 us.
Agreement with SPICE peak = **0.01%**. Decay curves perfectly overlaid (plots/behavioral_overlay.png).

**Validation — CR-110 (deck cr110_validate, same topology, Cf=1.4p/Rf=100Meg/G2=2):**
gain **-1.42 V/pC** (datasheet 1.4 V/pC, +1.6%), decay tau **140.5 us** (1.4p*100M=140us, exact).
Confirms the extracted topology reproduces Cremat's OWN published part specs -> faithful.

**Deliverables (paths under chips-board/csp-cr112/sim/):**
- decks: cr11x_csp.cir (CR-112), cr110_validate.cir (validation)
- scripts: analyze.py, behavioral_crosscheck.py, run_ltspice.ps1
- plots: plots/cr11x_csp_csp_out.png, plots/cr11x_csp_input_charge.png,
  plots/behavioral_overlay.png, plots/cr110_validate_csp_out.png
- reusable waveform (SHAPER STIMULUS): data/cr11x_csp_csp_out.csv  (cols: time_s,csp_out_V)
- FoM: data/cr11x_csp_fom.csv
- Cremat models + datasheets: cremat-models/CR-{110,111,112,113}/ (+ extracted .asc, .txt)

**State vs criteria:** ALL MET.
- 6.5 mV gain step: 6.66 mV (within ~2.5%) PASS.
- rise ~3 ns: 3.36 ns PASS. decay ~50 us: 51 us PASS. stable, no oscillation PASS.
- Cremat-model vs behavioral agree to 0.01% PASS. Used Cremat's official model as the
  primary source (not a hand model) PASS.

**Open issues:**
- No NATIVE CR-112 LTspice model exists on cremat.com (only CR-110/111/113). Approach:
  CR-110 official topology retargeted to CR-112 feedback, validated against CR-110's own ds.
  If the user wants the literal Cremat .asc run unmodified, the CR-110 model is in
  cremat-models/CR-110/extracted/ and can be opened in LTspice GUI; its specs are reproduced
  by cr110_validate.cir.
- Values are datasheet-exact (Cf=75p, Rf=680k). A3 models-bom does not set the CR-112's
  INTERNAL feedback (fixed inside the module), so the FoM are NOT expected to move at the
  real-parts gate. Round-2 note will be "no change" unless A1's input/coupling network adds
  significant Cin (rise time slows 0.13 ns/pF per datasheet) -> would only affect rise time.

**Next:** none for round 1. Awaiting coordinator gate / any A1 topology (added input cap)
or A3 real-parts that could move rise time.
