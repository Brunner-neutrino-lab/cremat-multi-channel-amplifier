# Session Log — C3 board-sim (twelve-channel, Simulation / system check)

> **Ground truth, append-only.** One dated entry per working session.

Track: `C3 board-sim` · Sub-component: `twelve-channel` (Phase C) · Aspect: `sim`
Reads (inputs): `docs/agent-project/{00-CHARTER,01-CONVENTIONS,02-TRACKS}.md`,
brief `briefs/C-twelve-channel.md`; `integration/single-channel/INTERFACE.md` +
`integration/single-channel/sim/SESSION_REPORT.md` (Phase-B FoM, decks, models);
datasheets `chips-board/*/sim/cremat-models/` (CR-112/CR-200/CR-210) +
`integration/single-channel/sim/models/THS3491/THS3491_datasheet.txt`.
Success criteria (mirror of report):
1. one-channel OUT_50 unchanged in the x12 context vs Phase B (67.0 mV/0.5 pC);
2. 12-channel total +-12 V supply current computed + rail/decoupling/bulk adequate;
3. channel-to-channel (shared-rail) crosstalk bounded + negligible.

---

## 2026-06-28 — session 1 — system-level confidence pass for the 12-ch board

**Goal this session:** confirm the proven single channel survives x12, compute the
shared-rail load and judge decoupling/bulk adequacy, and bound channel-to-channel
crosstalk — all at a confidence level (no full EM model), per the C3 brief.

**Did:**
- Set up `final-board/twelve-channel/sim/{decks,scripts,data,plots}`; copied the proven
  Phase-B decks/models/scripts (read-only source `integration/single-channel/sim/`):
  `chain_single_event.cir`, `cr112_csp.sub`, `cr200_1us.sub`, `cr210.sub`,
  `ths3491_rgt.lib`, `models.inc`, `ltspice_raw.py`, `analyze_chain.py`. Wrote local
  `scripts/run_ltspice.ps1` (same OneDrive-space-path staging trick; temp = `C:\Temp\ltspice_12ch`).
- **Criterion 1:** re-ran `chain_single_event.cir` in this workspace via LTspice 24.x batch
  (`-b -Run`), analysed with `analyze_chain.py`.
- **Criterion 2:** pulled datasheet quiescent currents (see Results), wrote `scripts/rail_budget.py`
  computing the 12x board supply current, the 4.7 ohm per-part decoupling IR drop, the
  shared-feed plane drop, and bulk-cap adequacy. Ran it.
- **Criterion 3:** to bound shared-rail crosstalk, first tried a 2-channel deck (aggressor +
  victim on a shared RC rail node) — the DC op-point of two stacked THS3491 macromodels on a
  *soft* (RC-fed) rail is singular (`Singular matrix: xbufv:gndf`), and a single-aggressor deck
  on a soft rail stalled the transient at t~2e-11 s (timestep collapse in the macromodel when
  its rails aren't stiff). **Resolution:** split the hard nonlinear solve from the trivial
  linear rail network. Captured ONE channel's real dynamic supply current on STIFF rails
  (`chain_isupply.cir` = the proven deck + `.save I(Vp) I(Vn)`; runs in 2.2 s), then drove that
  current into the shared-rail RC network analytically (`scripts/xtalk_analyze.py`: 100 uF bulk
  +30 mohm ESR, 100 mohm feed) and applied the THS3491 PSRR for the victim bound. Cross-checked
  the ODE against the closed-form `i_peak*ESR` and the 12x-simultaneous worst case.

**Results:**
- **Criterion 1 (PASS):** injected charge 0.5000 pC. OUT_50 peak = **+66.998 mV**, peaking
  **2.473 µs**, FWHM **2.527 µs**; gain chain shaper/CSP ×10.421, BLR/shaper ×−0.997,
  buffer/BLR ×1.998, OUT_50/buffer ×0.501; charge→OUT_50 = **134.0 mV/pC**. **Bit-identical to
  Phase B** (B2 reported 67.00 mV, 134 mV/pC, 2.47/2.53 µs) — same models, same deck, so the
  per-channel response is unchanged in the x12 context (each channel's signal path is
  electrically independent; the only ×12 coupling is the shared rail → criterion 3).
- **Criterion 2 (PASS):** datasheet per-rail quiescent currents — CR-112 ~5 mA @ ±6V (use 8 mA
  @ ±12 V, conservative; no-load Pdiss 70 mW; CR-110 sibling ~9 mA @ Vs=13); CR-200 **7 mA**
  @ Vs=±13V; CR-210 **17 mA (pos) / 13 mA (neg)** @ Vs=±13V (asymmetric); THS3491 IQ **16.7 mA**
  @ ±15V (15.8 @ ±7V). Per channel: **+rail 48.7 mA, −rail 44.7 mA**. ×12 board total:
  **+12 V = 584 mA (0.58 A), −12 V = 536 mA (0.54 A)**, board power **≈13.5 W**.
  - 4.7 ohm per-part decoupling drop is PER-PART (each R carries one part's current) →
    **independent of channel count**; worst = CR-210 +rail = 4.7×17 mA = **79.9 mV**
    (THS3491 78.5 mV), local rail ≈ 11.92 V ≫ CR-11X ±6 V minimum. AMPLE.
  - Shared-feed plane drop: 12 mV (20 mΩ) / 29 mV (50 mΩ) / 58 mV (100 mΩ) — sub-100 mV.
  - Bulk: single-event dynamic charge per channel ~3.4 nC → 0.34 mV on the 10 µF local cap;
    all-12-simultaneous 40 nC → 0.40 mV on the 100 µF bulk. Bulk hugely over-spec'd for the
    signal transient. Total rail decoupling C = 100 µF bulk + 480 µF distributed local.
- **Criterion 3 (PASS):** sim quiescent on the ±12 V rails (CR-200+CR-210+THS3491) = 23.8 mA
  per rail (CR-112 on its own ±6 V op-point rail in the model). **Aggressor DYNAMIC supply
  current during a 0.5 pC event = only −1.38 mA peak (+rail), 0.025 mA (−rail)** — the buffer
  sourcing into the 50 Ω. Driving that into the shared 100 µF bulk (30 mΩ ESR) + 100 mΩ feed:
  **dynamic rail ripple = 41.6 µV worst** (= i_peak×ESR, the cap shunts the AC). Through the
  THS3491 PSRR (conservative 50 dB in-band; datasheet 78/77 dB min DC): **victim crosstalk
  ≈ 0.13 µV = 0.0002 % of the 67 mV full-scale**. 12×-simultaneous fully-correlated worst case:
  ripple ≈ 0.50 mV → victim ≈ 1.6 µV = 0.0024 % FS. Static DC droop (584/536 mA × 100 mΩ feed)
  = 58/54 mV — a fixed common offset (NOT crosstalk; signal-independent), leaves ~11.9 V headroom.

**Decisions & why:**
- Used the EXACT Phase-B deck of record for criterion 1 (no re-litigation; the C3 brief says
  "confirm it survives ×12", not re-derive). The response can't change with ×12 except via the
  shared rail, which criterion 3 quantifies.
- For criterion 3, separated the nonlinear channel solve (hard with macromodels on soft rails)
  from the linear rail network. Captured the real I(rail) demand and convolved it analytically.
  This is robust, reproducible, and the closed-form `i_peak×ESR` cross-check (41.46 µV) matches
  the ODE (41.6 µV) — high confidence without an EM model (as the brief scopes).
- Conservative numbers throughout: CR-112 8 mA (vs 5), 100 mΩ feed (pessimistic for a 4-layer
  pour), 50 dB PSRR (vs 78 dB datasheet), 12×-correlated worst case.

**Dead-ends / surprises:**
- 2-channel shared-soft-rail deck: singular matrix (two THS3491 macromodels' `gndf`) and
  t≈2e-11 transient stall. Not pursued — superseded by the captured-current method above.
  Removed the broken deck; `chain_isupply.cir` is the crosstalk-source deck of record.
- LTspice .txt extraction of the Cremat PDF spec tables is scrambled (column layout); read the
  numbers from the surrounding line context (verified against the CR-110 sibling table).
- Surprise (good): the CR-210 BLR is the heaviest single load (17 mA +rail) and is *asymmetric*
  (17/13) — the +12 V rail is ~48 mA/channel heavier than −12 V; noted for C1/C2 (rail balance).

**State vs criteria:** all three **MET**. One-channel OUT_50 = 67.0 mV (= Phase B); 12-ch
supply +584/−536 mA, decoupling/bulk adequate with margin; shared-rail crosstalk ≤0.0002 % FS.

**Next:** none for sim. Flag to C1/C2 (in report): (1) supply must source ~0.6 A/rail, 13.5 W —
size the screw-terminal/feed copper and pick a ≥1 A/rail supply; (2) +rail is ~10 % heavier
(CR-210 asymmetry) — keep the +VDC pour generous (it's the rail without a full inner plane);
(3) single 100 µF bulk is adequate but consider a 2nd bulk near the far channels for margin
(optional — the analysis says 100 µF alone is fine). No design change is *required*.

---

## 2026-07-11 — refresh on current design + AC / linearity / noise extension

**Refresh.** Re-ran `run_all.ps1` on this machine against the current (widened, 180 mm) board.
The widening is mechanical only (netlist identical), so results reproduce **bit-identically**:
OUT_50 66.998 mV/0.5 pC, 134.0 mV/pC, +584/−536 mA, crosstalk 0.0002 % FS. LTspice ~1.6 s/deck.

**Extension — 3 new analyses** (decks `chain_ac`, `chain_linearity`, `chain_noise`; analysis
`scripts/analyze_ac_lin.py`; plots+FoM under `plots/` `data/`):
- **AC transfer function** (charge→OUT_50 transimpedance): band-pass **1.59 kHz … 130 kHz**,
  peak 336 kΩ @ ~15 kHz. Upper corner (130 kHz↔1.2 µs) confirms the 1 µs shaping; lower corner
  = CSP 50 µs decay + CR-210 restore high-pass. Needed a complex-`.raw` reader (added to script).
- **Charge linearity / dynamic range**: 133.4 mV/pC, linear ~1 % to ≈30 pC, **OUT_50 hard-clip
  5.13 V** set by the **THS3491 buffer** railing at +10.25 V (shaper still linear at 60 pC →
  buffer is the limit; bypassed variant ~2× headroom). CR-112 max charge 210 pC.
- **ENC / noise**: design ENC = CR-112 datasheet **7000 e⁻ + 30 e⁻/pF @ 1 µs** (tabulated vs
  SiPM C; zero-C dynamic range ~34 000:1). `.noise` is only a cross-check — the Cremat
  macromodels are **noiseless** (no CSP FET series noise); it gives ~9.7 k e⁻ in-band, same
  order as datasheet, i.e. Rf-thermal/front-end dominated, no board noise blow-up. Honest caveat
  documented in the report + deck header.

**State:** the 3 original criteria remain MET and are now complemented by bandwidth, dynamic-
range, and ENC characterisation. No design change indicated. Report section appended to
`SESSION_REPORT.md` (## 2026-07-11).
