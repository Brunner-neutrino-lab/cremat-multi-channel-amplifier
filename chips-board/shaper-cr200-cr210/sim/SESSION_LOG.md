# Session Log — A5 `shaper-sim`

> **Ground truth, append-only.** One dated entry per working session: what you did, exact
> commands/tools, results (numbers, ERC/DRC counts, sim figures of merit), decisions **and
> why**, dead-ends, next steps. Never rewrite earlier entries.

Track: `A5` · Sub-component: `shaper-cr200-cr210` · Aspect: `sim`
Reads (inputs): brief `docs/agent-project/briefs/A-shaper-cr200-cr210.md`; conventions §5;
`reference/cremat-CR-160-R7` (topology); A2 `csp-sim` report (CSP-output waveform — stimulus dependency).
Success criteria (mirror of report):
- **M1 (CR-200):** shaped Gaussian at OUT; peaking time ≈ shaping time (1 µs region, FWHM ≈ 2.4 µs per datasheet) within model tol; peak amplitude & undershoot reported; Cremat official LTspice model used + behavioral cross-check.
- **M2 (+CR-210):** demonstrable baseline restoration — pulse train shows baseline droop (no-BLR) removed (with-BLR); FOM tabulated + judged. Populate-XOR bypass (JU1) modeled.

---

## 2026-06-25 — session 1 — setup, model download, topology study

**Goal this session:** read briefs/conventions/prior art; download Cremat official LTspice
models + app guides (§5 path); understand CR-160-R7 shaper topology; scaffold `sim/`.

**Did:**
- Read `00-CHARTER.md`, `01-CONVENTIONS.md` (§5), brief `A-shaper-cr200-cr210.md`,
  `reference/cremat-CR-160-R7/{README.txt, CR-160-R7.net}`, `hardware/lib/cremat.kicad_sym`.
- Confirmed environment: **no `ngspice.exe`** (only `ngspice.dll`; `kicad-cli` has no `sim`
  subcommand). **LTspice present** at `C:\Users\darro\AppData\Local\Programs\ADI\LTspice\LTspice.exe`.
- Scaffolded `chips-board/shaper-cr200-cr210/sim/` with `cremat-models/{CR-200,CR-210,app-guides}`,
  `decks/ data/ plots/ scripts/`, and copied SESSION_LOG/REPORT templates.
- **Downloaded Cremat official models + guides** via PowerShell `Invoke-WebRequest`:
  - `https://www.cremat.com/CR-200-1us-R2.1-LTSPICE.zip`  → `cremat-models/CR-200/` (1519 B; → `.asc`+`.asy`)
  - `https://www.cremat.com/CR-210-R0-LTSPICE.zip`        → `cremat-models/CR-210/` (1168 B; → `.asc`+`.asy`)
  - `https://www.cremat.com/CR-200-R2.1.pdf`              → `cremat-models/app-guides/` (404 KB)
  - `https://www.cremat.com/CR-210-R0.pdf`                → `cremat-models/app-guides/` (245 KB)
  - **Retrieval date: 2026-06-25.** Source hub: https://www.cremat.com/specification-sheets/
    Model links discovered via WebFetch of that hub + the CR-200 product page.
  - Extracted PDF text → `cremat-models/app-guides/CR-200-R2.1.txt`, `CR-210-R0.txt` (pymupdf).

**Results — datasheet figures of merit (targets):**
- **CR-200-1µs:** shaping time τ = 1 µs; **FWHM = 2.4·τ = 2.4 µs**; Cin = 1000 pF; Rin region
  1.0 kΩ; output offset ±40 mV; out swing Vs−0.5 V; Zout <5 Ω; max out current 20 mA;
  non-inverting; "produces a Gaussian (bell) output from a step-like input."
- **P/Z rule (datasheet):** RP/Z = Rf·Cf / Cin, connected pin1(input)↔pin2(P/Z); cancels the
  CSP decay pole. Cin(CR-200-1µs) = 1000 pF.
- **Baseline shift w/o BLR:** S/H = R·τ·2.5e-6 (R = count rate /s, τ in µs) → e.g. 2.5 % at 10 kcps.
- **CR-210-R0:** signal gain = 1; Zin = 10 k; Zout = 50 Ω; restores baseline to GND; works on
  **positive pulses only**; correction time const 200 µs (rising rate) / 20 ms (falling);
  holds baseline up to ~120 kHz (1µs shaping). Model: R1=10k in, two G=+1 buffers, C1=0.22µF
  (BLR cap), 2N5484 JFET switch (closed when Vo<0), LT1016 comparator, R4=47 Ω out series.

**Topology study — CR-160-R7 (`.net`) shaper region (authoritative wiring):**
- **CR-200 (U4):** pin1=input(=R7 wiper), pin2=P/Z(=R7 other end), pins3/6/7=GND, pin4=−Vs,
  pin5=+Vs, pin8=output. **R7 = 200 k pot** across pins 1↔2 = the **pole-zero network**.
- **CR-210 (U5):** pin1=input(=CR-200 out = JU1 pad1), pin8=output(→R20 1k → JU1 pad2),
  pins2/3/6/7=GND, pin4=−Vs, pin5=+Vs.
- **JU1 bypass jumper (populate-XOR):** pad1 = CR-200 out (= CR-210 in), pad2 = CR-210 out.
  Short JU1 ⇒ bypass CR-210 (M1 / BLR-off); open JU1 ⇒ signal routed through CR-210 (M2 BLR-on).
- Per-rail decoupling on the eval board: 4.7 Ω series + 10 µF + 0.1 µF per rail (C9/C10 10µF,
  C11/C12 0.1µF, R21/R22 4.7 Ω). Pure DC for sim → decoupling not value-sensitive to FOM.

**Cremat model internals (read from `.asc`):**
- **CR-200-1µs:** AC-couple Cin=1000pF, then 3× UniversalOpamp2 (Avol=1Meg, GBW=80Meg,
  Slew=200Meg) Sallen-Key integrator/diff stages: R2/R4/R6/R14 = 4.25 k, C2/C3/C6 = 100 pF,
  C4 = 260 pF, feedback/series R1/R3/R5/R8/R11 = 1 k, R12 = 100, R13 = 1.25 k. Ports (`.asy`
  SpiceOrder): 1=input, 2=output, 3=pole-zero, 4=−Vsupply, 5=+Vsupply.
  NOTE: the model `.asc` carries internal V1/V2 = 0.5 — verify whether they self-power the
  block or are leftover test sources (resolved in session 2).
- **CR-210-R0:** ports (SpiceOrder): 1=input, 2=output, 3=−Vsupply, 4=+Vsupply. Internal V1/V2
  =5, V3=2.5 references; uses ±5 internal regulation off the supply pins.

**Decisions & why:**
- **Engine = LTspice batch** (`-b -Run <deck>.asc` → `.raw`), parsed in Python (numpy) +
  matplotlib. Justification: Cremat models are native LTspice BLOCK symbols (`.asy`+`.asc`),
  no portable `.subckt`; headless ngspice unavailable. Sanctioned by conventions §5 path 2.
- Drive the shaper with the CR-200's own P/Z network present (RP/Z) per the datasheet, since
  RP/Z is part of *this* sub-component (it lives around U4 on the eval board).
- **Stimulus = representative CR-112-style CSP output step** (fast rise + long decay tail) until
  A2 publishes its actual CR-112 model output. A2 `csp-sim` currently has only template files
  → its waveform is not yet available. Dependency flagged; Round-2 swap if A2 changes a FOM.

**Dead-ends / surprises:**
- `pdftoppm` (poppler) not available → could not Read the PDFs as images; used system-Python
  `pymupdf` to extract text instead (KiCad's bundled py lacks pypdf/pymupdf; Anaconda py has both).

**State vs criteria:** models + datasheet FOM acquired; topology understood. No sim run yet.

**Next:** build LTspice test decks: (1) bare CR-200 char (step → measure gain, peaking
time, FWHM, undershoot); (2) CR-200 + RP/Z with CSP-step stimulus (M1); (3) CR-200→CR-210 pulse
train, BLR-on vs JU1-bypass (M2). Run batch, parse `.raw`, plot, tabulate FOM vs datasheet.

## 2026-06-25 — session 2 — pipeline working; stimulus + P/Z fixed from datasheets

**Did:**
- Wrote `scripts/make_subckts.py`: `LTspice.exe -netlist <model>.asc` → flat `.net`, then
  wrapped each as a portable `.subckt` (`decks/cr200_1us.sub`, `decks/cr210.sub`) with clean
  ASCII (renamed LTspice's `X§U*`→`XXU*`, `µ`→`u`) and a shared `decks/models.inc`
  (`.lib UniversalOpAmp2.lib`, `standard.jft`, `LTC.lib`). The genuine Cremat device lines are
  preserved verbatim inside the subckt.
- **Confirmed LTspice batch runs the model:** `LTspice.exe -b -Run smoke_fixed.cir` → `.raw`,
  exit 0. Wrote `scripts/ltspice_raw.py` (UTF-16 header + binary float64-time/float32-vals
  reader). Smoke result: 10 mV ideal step → CR-200 out peak **+103 mV ⇒ model gain ≈ 10.3**.

**Dead-end / key fix:** LTspice X-instance syntax = `Xname n1 n2 ... SUBCKTNAME` (**subckt name
LAST**). I first wrote `XU CR200_1US IN OUT ...` (name first) → "sub-circuit name is not
defined" pointing at the last token. Corrected to `XU IN OUT PZ VN VP CR200_1US`. Verified by
bisection (a 5-port dummy subckt reproduced + fixed it).

**Stimulus locked from CR-112 datasheet** (`cremat-models/csp-ref-for-stimulus/CR-112-R2.1.pdf`,
retrieved 2026-06-25 from https://www.cremat.com/CR-112-R2.1.pdf):
- CR-112 **gain = 13 mV/pC**, **Rf = 680 kΩ**, **Cf = 75 pF**, decay **τ_csp = Rf·Cf ≈ 51 µs**
  (datasheet "≈50 µs"), rise ≈ 3 ns.
- **0.5 pC event ⇒ CSP step = 13 mV/pC × 0.5 pC = 6.5 mV** (matches brief "≈6.5 mV").
  Representative CSP-output stimulus = 6.5 mV step, 3 ns rise, exp decay τ=51 µs.
- NOTE: **Cremat publishes NO CR-112 LTspice model** (only CR-110/111/113). So A2 must build
  the CR-112 output behaviorally / by scaling CR-110; I use the datasheet-exact representative
  step above and will swap in A2's actual waveform in Round 2 if it moves a FOM.
- **P/Z resistor (datasheet rule RP/Z = Rf·Cf/Cin):** Cin(CR-200-1µs)=1000pF ⇒
  **RP/Z = 51µs / 1nF = 51 kΩ** (eval board realizes this with the R7 200k trimpot). This is
  the generic P/Z value for M1/M2.

## 2026-06-25 — session 3 — M1 + M2 simulated, FOM measured, cross-check done

**Goal:** run M1 (CR-200) + M2 (+CR-210) on the genuine Cremat models; measure FOM vs datasheet.

**Engine + exact invocation (reproducible):**
- `LTspice.exe -netlist <model>.asc` → `.net` → `scripts/make_subckts.py` wraps as `.subckt`.
- `LTspice.exe -b -Run decks/<deck>.cir` → `.raw`; parsed by `scripts/ltspice_raw.py`
  (UTF-16 header + binary float64-time/float32-value reader). One-shot: `bash scripts/run_all.sh`.
- **Key LTspice gotchas solved:** X-instance = `Xname n1..nk SUBCKTNAME` (name LAST); `.include`
  (full word, not `.inc`) so the opamp `.lib` loads before the subckt parse; ASCII-only subckt
  (renamed `X§`→`XX`, `µ`→`u`); charge stimulus must be **timestep-resolvable** — a 1 ns impulse
  at 20 ns max-step lost ~70 % of its charge, so the CSP train is an **analytic pile-up
  superposition B-source** (exact, step-independent), cross-checked against the RC charge-
  injection model at 1 ns step (identical 6.73 mV step, 51 µs decay).

**M1 — CR-200-1µs single 0.5 pC event** (`decks/m1_cr200.cir`, `analyze_m1.py`):
- CSP stimulus 6.49 mV step (target 6.5), τ=51 µs tail. Supplies ±12 V.
- **as-built (P/Z 51 k): peak 66.3 mV (gain 10.19), peaking 2.50 µs, FWHM 2.50 µs, undershoot −0.22 %.**
- Datasheet FWHM spec = 2.40 µs (=2.4·τ) → **+4.2 %**, within model tol. ✓
- **Pole-zero validation (reproduces datasheet Fig.3):** P/Z 51 k → −0.2 % (clean);
  NO P/Z → −4.9 % undershoot; P/Z 10 k (too low) → +13.5 % overshoot.
- Plots: `plots/m1_cr200_gaussian.png` (CSP in vs Gaussian out), `plots/m1_polezero_effect.png`.

**M2 — CR-200 → CR-210 BLR, 100 kHz pulse train** (`decks/m2_blr.cir`, `analyze_m2.py`):
- CSP pile-up steady-state peak = 37.44 mV (analytic 6.667/(1−e^(−10/51)) = 37.44 — exact match).
- SHOUT per-event ≈ 68 mV (gain consistent with M1). AC coupling Cc=100 n into 10 k (τ=1 ms).
- Two paths model the CR-160-R7 **JU1 populate-XOR**: JU1 short → AC-coupled, no BLR (droops);
  JU1 open → through CR-210 (restored).
- **BLR OFF steady-state baseline = −17.3 mV = −25.7 % of peak.** This MATCHES the CR-200
  datasheet formula S/H = R·τ·2.5e-6 = 1e5·1·2.5e-6 = **25 %** — strong cross-validation.
- **BLR ON steady-state baseline = −0.4 mV = −0.6 % of peak → CR-210 removes 98 % of the droop.**
- Pulse peaks: BLR off sinks 67→51 mV; BLR on holds 67→68 mV.
- Plots: `plots/m2_baseline_restoration.png` (peak + baseline envelopes),
  `plots/m2_pulse_detail.png` (5-pulse zoom: early vs late vs restored).

**Behavioral cross-check** (`scripts/behavioral_crosscheck.py`, `plots/crosscheck_behavioral.png`):
- Idealised CR-RC^4 (datasheet: input CR + two Sallen-Key = 4 integration poles), τ_s fit to
  FWHM 2.40 µs. **FWHM agreement with the Cremat model = 4.1 %** (controlling shaping-time metric).
- Peaking time differs 19 % (behavioral 2.02 µs vs model 2.50 µs) — **expected**: the idealised
  formula assumes n IDENTICAL poles + pure DC-zero CR, whereas the real CR-200 uses unequal SK
  RC (R=4.25 k, C=100 p/260 p). Shapes overlay well; verdict = CONSISTENT on FWHM.

**Decisions & why:**
- Use analytic CSP superposition (not charge integration) for M2 to remove timestep sensitivity
  while remaining datasheet-faithful (step height = 0.5 pC/75 pF, decay = Rf·Cf). Verified equal.
- Judge M1 against **FWHM** (the datasheet's stated shaping-time metric), not peaking time, since
  the datasheet defines τ via FWHM = 2.4·τ.

**State vs criteria:** **M1 met** (Gaussian; FWHM within 4.2 % of spec; P/Z verified; official
model + behavioral cross-check). **M2 met** (BLR demonstrably restores baseline, 98 % droop
removed; −25.7 % no-BLR droop matches datasheet 25 % formula; JU1 XOR modeled; FOM tabulated).

**Open / dependencies:**
- Stimulus = **representative** CR-112 CSP step (datasheet-exact: 6.5 mV, τ=51 µs). A2 `csp-sim`
  has not yet published its CR-112 model output (only template files present). Round-2 swap if
  A2's waveform moves a FOM — expected "no change" since both are CR-112-datasheet-derived.
- No CR-112 LTspice model exists on cremat.com (only CR-110/111/113) — A2/A3 should note this.
- A6 real-parts gate: P/Z resistor value (51 k generic) is the only value-sensitive FOM input;
  decoupling (4.7 Ω/10 µF/0.1 µF) is DC-irrelevant to these transient FOM (note "no change").
