# Session Log — B1 chan-design

> **Ground truth, append-only.** One dated entry per working session: what you did, exact
> commands/tools, results (numbers, ERC/DRC counts, sim figures of merit), decisions **and
> why**, dead-ends, next steps. Never rewrite earlier entries.

Track: `B1 chan-design` · Sub-component: `single-channel` (Phase B) · Aspect: `design`
Reads (inputs): `chips-board/csp-cr112/INTERFACE.md` + `design/`, `chips-board/shaper-cr200-cr210/INTERFACE.md` + `design/`, `reference/cremat-x6-board/channel.kicad_sch` (buffer app circuit), EL5167 symbol in `hardware/lib/cremat.kicad_sym`, EL5166/EL5167 datasheet (Renesas FN7365).
Success criteria (mirror of report):
- ERC 0 errors / 0 warnings.
- DRC 0 errors / 0 warnings / 0 unconnected.
- The two Phase-A blocks (CSP front-end+CR-112, shaper CR-200+CR-210) reused AS-IS — same nets/values/topology/DNP.
- Buffer = CFA, non-inverting, 49.9 Ω series → 50 Ω back-terminated `OUT_50`; Zout(OUT_50)=50 Ω confirmed.
- One clean, flat `channel` cell that Phase C can instantiate ×12 (gen-script driven, like the Phase-A boards).
- `INTERFACE.md` published.

---

## 2026-06-25 — session 1 — merge CSP+shaper, add CFA buffer, ERC/DRC to 0/0/0

**Goal this session:** Build the merged single-channel board: front-end → CR-112 → CR-200 →
CR-210 → 49.9 Ω → CFA output buffer → 49.9 Ω → OUT_50 (MCX). ERC + DRC clean. Publish
INTERFACE.

**Inputs read & key facts pulled:**
- `csp-cr112/INTERFACE.md`: front-end nets `BIAS_IN, N_filt, FE, CSP_IN, CSP_OUT`,
  rails `+VDC/-VDC/GND` + filtered `+VS_F/-VS_F`. CR-112 (cremat:CR-11X) pin map
  1=in 2/4/7=GND 3=NC 5=-VS_F 6=+VS_F 8=out. Real BOM frozen (Samsung/Yageo/Murata/Nichicon).
  Gain ≈ 13 mV/pC → CSP_OUT ≈ 6.5 mV for 0.5 pC. HV net class `hv_bias` 0.6 mm.
- `shaper-cr200-cr210/INTERFACE.md`: shaper `IN` = CSP step; CR-200 1=in 2=P/Z 3/6/7=GND
  4=-Vs 5=+Vs 8=out; P/Z = 200k trimpot alone; CR-210 BLR with JP_BLR 0R bypass
  (populate-XOR, U_BLR fitted / JP_BLR DNP by default); 49.9 Ω at OUT. Real BOM frozen.
- EL5167 symbol pins (hardware/lib/cremat.kicad_sym): **1=OUT, 2=V-, 3=+IN, 4=-IN, 5=V+**
  (SOT-23-5). Description says "EL5167 or LM7321".
- Reference x6 buffer: EL5163/EL5167IWZ (DNP variant) + **LM7321** alternate, **49.9 Ω**
  (R32) series at the buffer output → MCX. 0603 passives in the reference.

**CRITICAL datasheet finding (flagged for B3):**
- EL5167 **absolute-max supply VS+ to VS- = 12.6 V** (Renesas FN7365). The channel runs
  **±12 V (= 24 V span)** → a true EL5167 would be destroyed. The symbol/reference therefore
  pair it with **LM7321** (CFA-class, ±15 V / 32 V abs-max) which survives ±12 V.
- **Decision:** design the buffer as an **LM7321-class CFA** on the channel ±12 V rails
  (pin-compatible with the EL5167 symbol & SOT-23-5 footprint). Keeps the "EL5167-class CFA,
  50 Ω back-terminated" locked decision while being rail-safe. B3 picks the real op-amp:
  either LM7321 (±12 V direct) OR a true EL5167 fed from local ±5–6 V regulation. Listed
  as a buffer generic needing substitution in INTERFACE.md.

**Buffer topology (generic values; B3 refines):**
- Non-inverting CFA: shaper `OUT` → buffer **+IN (pin3)**.
- Feedback: **Rf = 510 Ω** from OUT(pin1) → -IN(pin4); **Rg = 510 Ω** from -IN(pin4) → GND.
  Gain `Av = 1 + Rf/Rg = +2`. (510 Ω is a safe mid-range CFA Rf for this family; B3 sets the
  datasheet-optimum Rf for the chosen part. For a CFA, Rf is the dominant stability element.)
- Output: OUT(pin1) → **Rser = 49.9 Ω** → `OUT_50` (MCX). With Av=+2 and the 49.9 Ω series
  resistor matching the 50 Ω cable/load, the back-terminated divider gives ≈ ×1 to the 50 Ω
  load (×2 amp, then 50/(49.9+50) ≈ 0.5 divider). **Zout looking into OUT_50 = Rser = 49.9 Ω**
  (op-amp output ≈ 0 Ω in series with 49.9 Ω) → **50 Ω back-termination**. Standard 50 Ω
  line-driver topology; matches the x6 reference's 49.9 Ω.
- Buffer decoupling: 4.7 Ω series + 10 µF + 0.1 µF on each rail at the buffer (same per-rail
  filter pattern as the CR-modules), nets `BVP`/`BVN`.

**Merge wiring:** the shaper `IN` net = `CSP_OUT` so CSP output drives the CR-200 input
directly on one board (no MCX between them). Each block keeps its own nets; the only joins
are CSP_OUT ≡ shaper IN, and shaper OUT → buffer +IN. The standalone CSP `CSP_OUT` MCX jack
(J_OUT) and the standalone shaper `IN` MCX jack are dropped in the merge; the shaper OUT MCX
is replaced by the buffer path; new MCX jacks: BIAS_IN, SIPM, TEST_IN, OUT_50.

**Did:**
- Set up `integration/single-channel/design/`: copied templates, `hardware/lib/cremat.kicad_sym`
  (has all 4 symbols: CR-11X, CR-200, CR-210, EL5167) + `cremat.pretty` (MCX), wrote
  `sym-lib-table`, `fp-lib-table`, `channel.kicad_pro` (net classes incl. hv_bias 0.6 mm + the
  new buffer rail nets).
- Wrote `gen_sch.py` (based on the shaper's clean generator): one flat `channel` sheet
  composing CSP block (csp-cr112) + shaper block (shaper-cr200-cr210) + buffer, with the merge
  join (`CSP_OUT` = CR-112 out = CR-200 in) and `SHAPER_OUT → buffer +IN`. All CSP/shaper
  values/footprints/DNP copied verbatim from the two COMPLETE INTERFACEs (real parts). Buffer
  = generic (U4 EL5167-class, R_FB/R_GAIN 510, R_BSER 49.9 real, per-rail decoupling).
  Ran it → 51 symbols.
- `kicad-cli sch erc` → **0 violations (0/0)** first pass.
- Exported netlist; audited nets: CSP_OUT joins U1.8+U2.1+RV1.1 (merge ✓), SHAPER_OUT =
  R13.2+U4.3 (shaper→buffer ✓), buffer Rf/Rg/Rser wired (Av=+2, 49.9 back-term ✓), 3 DNP
  (R2/R4/R12) ✓. CR-112 NC pin (pin3) = proper no-connect.
- Wrote `gen_pcb.py` (from netlist, like Phase A): 4-layer, explicit DRC-clean placement
  (left→right signal row; 3 SIP-8 modules flat rot90; SOT-23-5 buffer; MCX at edges;
  decoupling above/below; bottom power strip), net classes, GND(In1)+−VDC(In2) planes.
- First placement DRC: **6 violations** (C19↔C12/C13 courtyard overlap from the SHVN
  decoupling row landing on the bulk strip; J5↔H3 courtyard + NPTH-in-courtyard). Fixed by
  moving the SHVN row to flank the trim, relocating C18/C19 under the CR-210, and shifting J5
  right of the mounting hole. Re-ran → **0 placement violations**.
- Routing: export DSN (OK = clean placement) → FreeRouting 2.2.4 (Java 25). First route left
  **1 unrouted: +VDC C8→J5** (+VDC has no inner plane; bottom strip congested). Tried nudging
  C8 (worse: 2 unrouted). **Root fix:** added a **+VDC pour on B.Cu** (gen_pcb, priority 1) so
  every +VDC pad ties to copper without pad-to-pad +VDC tracks; updated fill_zones to F.Cu GND
  fill (priority 2) + keep the B.Cu +VDC pour. Re-route → **all 89 nets routed, score 996.10,
  0 unrouted.**
- `import_ses.py` → `fill_zones.py` (4 zones: GND In1 + F.Cu fill, −VDC In2, +VDC B.Cu) →
  `kicad-cli pcb drc` → **0 errors / 0 warnings / 0 unconnected.** ERC re-run **0/0**.
  Board: 204 tracks, 49 vias, 4 copper layers, 51 footprints.
- Rendered `reports/routed-top.png` (clean left→right layout, all parts placed/routed).
- Compared `--schematic-parity`: 106 items (footprint↔symbol UUID/field link + 4 mounting
  holes). Verified the COMPLETE Phase-A CSP board has the **same class** (50 items) → this is
  the accepted gen-script-pipeline artifact, not in the gate; resolved by GUI "Update PCB from
  Schematic". Wrote `INTERFACE.md`.

**Results:**
- **ERC 0/0 · DRC 0/0/0** (errors/warnings/unconnected), fully autorouted (FreeRouting 2.2.4,
  score 996.10). Files: `channel.kicad_sch/.kicad_pcb/.kicad_pro`, gen scripts, reports/.
- Two Phase-A blocks reproduced verbatim (netlist-audited); only joins = merge + buffer.
- Buffer: CFA Av=+2, 49.9 Ω series → Zout(OUT_50)=49.9 Ω ≈ 50 Ω back-term (standard line driver).

**Decisions & why:**
- **Buffer rail safety (key):** EL5167 abs-max VS+−VS− = 12.6 V (Renesas FN7365) < the ±12 V
  (24 V) channel rails → designed as **LM7321-class CFA** (±15 V, SOT-23-5, pin-compatible with
  the EL5167 symbol), keeping the "EL5167-class CFA, 50 Ω back-terminated" locked decision while
  being rail-safe. Flagged as the primary B3 substitution.
- **+VDC B.Cu pour:** the only clean way to route +VDC 100% on this power-dense board (GND/−VDC
  already take both inner planes); also lowers +VDC rail impedance. Symmetric to the existing
  −VDC plane.
- **49.9 Ω at OUT_50 = back-termination:** op-amp Zout≈0 + 49.9 Ω series → 49.9 Ω source into a
  50 Ω line; matches the x6-reference R32=49.9. Confirmed OUT_50 node carries only R16 + the MCX.
- **Kept the shaper's own 49.9 Ω (R13) at SHAPER_OUT** unchanged (it's part of the COMPLETE
  shaper topology); the buffer's high-Z +IN means no load divider there.

**Dead-ends / surprises:**
- Nudging/rotating C8 to fix the +VDC route made it worse (2 unrouted). The architectural fix
  (+VDC pour) was correct, not placement micro-tuning.
- `--schematic-parity` "106 issues" looks alarming but is the same cosmetic UUID/field-link
  class the COMPLETE Phase-A boards have; the real gate (`pcb drc`) is 0/0/0.

**State vs criteria:** ALL met — ERC 0/0; DRC 0/0/0; Phase-A blocks unchanged (audited);
buffer 50 Ω back-terminated; clean `channel` cell for ×12; INTERFACE.md published. Only the
**buffer parts are generic** (by design — B3 sources them at the Round-2 real-parts gate).

**Next:** await B3 PARTS report → swap U4/R14/R15 generics → real, re-run ERC/DRC, reconcile
BOM == B3. Phase C reuses the `channel` sheet/topology ×12.

---

## 2026-06-28 — session 2 — Round-2: real THS3491 buffer + CR-210 polarity + BOM==B3

**Goal this session:** Coordinator tasks: (1) swap the buffer to TI **THS3491** (THS3491IDDAT,
SOIC-8-1EP), Av=+2 with Rf=Rg=1.21k, keep 49.9 Ω back-term; re-place/re-route; ERC+DRC 0/0/0.
(2) Fix CR-210 polarity (B2 finding). (3) Update INTERFACE + confirm design BOM == B3 BOM.

**Inputs read:** B3 `models-bom/single-channel-bom.csv` + `BOM-REPORT.md`; B2
`sim/SESSION_LOG.md` (polarity finding); THS3491 datasheet (TI FN/SLOS pinout via web);
CR-160-R7 reference (`.cmp` shows EL5163 op-amp stages + MAX4649 for polarity/gain);
Cremat CR-11X polarity spec (output sign set by detector current direction).

**Did — buffer swap:**
- Pulled the KiCad stock **`THS3491xDDA`** symbol from `Amplifier_Operational.kicad_sym` and
  appended it to `design/lib/cremat.kicad_sym`. Verified its pin map = THS3491 datasheet:
  **1=REF 2=−IN 3=+IN 4=V− 5=NC 6=OUT 7=V+ 8=PD 9=EP**. (SOIC-8-1EP FP has pads 1–8 + pad 9.)
- gen_sch.py: SYMSRC EL5167→THS3491xDDA; FP_SOT235→FP_SOIC8EP
  (`Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm`). Rewrote U_BUF pin map:
  1→GND (REF, split-supply), 2→BUF_FB, 3→SHAPER_OUT, 4→BVN, 5→NC, 6→BUF_OUT, 7→BVP,
  8→BVP (PD tied high = enabled, TI advises not floating), 9→BVN (EP→V−, coordinator).
  Rf/Rg 510→**1.21k** (RC0805FR-071K21L); R_BSER kept 49.9.
- Aligned every PARTS Value string + MPN to B3's CSV exactly (e.g. "0.1uF 50V X7R",
  "10uF 25V X5R", "100uF 35V", "CR-200-1us", "MCX edge jack 50R", terminal "1715734").

**Did — B3 dedups (to make BOM==B3, and they're electrically correct in the merged channel):**
- Removed the CSP standalone **radial entry-bulk Cb_p/Cb_n** (UVR1E101MED) — channel keeps
  ONE 100 µF rail-bulk pair = the shaper SMD electrolytics (UWT1V101MCL1GS, both rails).
- Removed the shaper **board-edge 49.9 Ω R_OUT**: CR-210 out (`SHAPER_OUT`) now drives the
  buffer's high-Z +IN directly; the single channel 49.9 Ω back-term is at OUT_50 (R15).
  JP_BLR bypass pin2 retargeted SH_OUT↔SHAPER_OUT. (Merge-dedup, not a shaper-function change.)
- Power terminal MPN 1715035→**1715734** (5.08 mm, B3-reconciled).
- Net symbol count 51→**48** (= B3's 48 ref lines).

**Did — CR-210 polarity (item 2):**
- B2: real CR-112 is INVERTING, CR-200 passband non-inverting → CR-210 sees the CR-112 sign;
  CR-210 restores only a POSITIVE pulse (negative → baseline runs to ~100% of peak at rate).
  CR-160-R7 reference uses op-amp stages to set polarity; B2 modeled a unity inverter between
  CR-200 and CR-210.
- **Resolution (no added parts):** Cremat CR-11X output polarity is set by the **detector
  current direction** ("positive when current flows from the CSP input"; CR-110/CR-112 work
  with either polarity). So the channel presents the CR-210 a positive pulse by the
  **detector charge-sign / coupling orientation** — a documented constraint, no hardware
  inverter, proven blocks + the non-inverting THS3491 unchanged. Documented in INTERFACE.md
  (Polarity section + the explicit detector-sign constraint box).

**Did — verify + reconcile:**
- gen_pcb.py: rewrote PLACE for the new ref map (caps/Rs renumbered after the 3 deletions;
  U4 SOIC-8 not SOT-23). First route left 1 unrouted +VDC (C8→J5) — same class as Round 1,
  the +VDC B.Cu pour already present handles it after a clean re-place. Board-edge clearance
  errors near J4 (OUT_50) at the right edge → widened board 160→**164 mm**, inset J4/R15,
  bumped fill_zones outer-fill margin 0.3→0.6 mm (≥ the 0.5 mm edge-clearance rule).
- Pipeline: gen_sch → ERC **0/0**; gen_pcb (48 fp, 0 missing, 0 placement DRC) → export_dsn →
  FreeRouting (91 nets, score 996.0, **0 unrouted**) → import_ses → fill_zones (4 zones) →
  **DRC 0/0/0**. Bonus: **`--schematic-parity` now 0 issues** (clean THS3491xDDA stock symbol
  + aligned fields → no UUID/field-link items this round).
- BOM reconcile (`reports/bom_reconcile.txt`): design vs B3 on (Value,MPN,Footprint,qty) →
  **48 lines, 19 MPNs, 0 mismatches → DESIGN == B3 : YES.**
- DNP refs (sch & PCB) = {R2,R4,R12} (JP_Rf1/JP_Rf2/JP_BLR). Re-rendered routed-top.png.

**Results:**
- **ERC 0/0 · DRC 0/0/0 · schematic-parity 0**, fully autorouted (score 996.0). 207 tracks,
  52 vias, 4 layers, 48 footprints. **design BOM == B3 BOM (0 mismatches).**
- Buffer = TI THS3491 (HV CFA, ±12 V direct), Av=+2 (Rf=Rg=1.21k), 49.9 Ω → Zout(OUT_50)=50 Ω.
- B2 OUT_50 = +67.1 mV for 0.5 pC into 50 Ω (matches the compounded-gain expectation).

**Decisions & why:**
- **THS3491 over B3's THS3091 primary:** coordinator instruction; both TI HV-CFAs, same
  SOIC-8 PowerPAD, same Rf=Rg=1.21k, THS3491 is the in-stock part (695 stk). B3's CSV `U_BUF`
  line already reads THS3491/THS3491IDDAT, so design==B3 is exact.
- **PD→V+ and REF→GND** per TI datasheet (enabled, split-supply thresholds); **EP→V−** per
  coordinator (thermal pad sinks to −VDC plane).
- **Polarity = detector-sign constraint, not a hardware inverter:** the CR-11X is
  polarity-agnostic (sign = detector current direction), so the positive-into-CR-210
  requirement is met by detector coupling — keeps the proven blocks + non-inverting buffer
  intact and adds no BOM line. Matches B2's intent and the CR-160-R7 reference's purpose.
- **Board 160→164 mm:** to give OUT_50's GND routing ≥0.5 mm board-edge clearance (the only
  DRC errors after the first Round-2 route were edge-clearance at the right edge).

**Dead-ends / surprises:**
- Heredoc backslash mangling in bash → moved the symbol-extraction script to a file.
- First J4 reposition (154→151) collided J4 with R15 (MCX is 9.9 mm wide) → widened the board
  instead and kept J4 at 152, R15 at 143.

**State vs criteria:** ALL met — ERC 0/0; DRC 0/0/0 (and parity 0); buffer = real THS3491,
50 Ω back-terminated; Phase-A active blocks unchanged (only merge joins + B3 dedups);
polarity resolved + documented; design BOM == B3 BOM; `channel` cell clean for ×12.

**Next:** Phase C instantiates the `channel` sheet/topology ×12. If anyone changes the buffer
gain, update Rf/Rg (one PARTS line) + re-sim (B2).

---

## 2026-06-28 — session 3 — Round-2b: buffer Rf=Rg 1.21k -> 976R (THS3491 datasheet value)

**Goal:** Coordinator close-out: for the CFA the feedback resistor governs loop stability, so
use the TI THS3491 datasheet G=+2 recommended **976 Ω** (B2 validated vs TI's official SPICE
model), not 1.21 kΩ. Value-only swap (same 0805 footprint). Re-run ERC/DRC; confirm BOM==B3.

**Did:**
- gen_sch.py PARTS: R_FB/R_GAIN "1.21k"/RC0805FR-071K21L → **"976"/RC0805FR-07976RL**
  (DK 311-976CRCT-ND). Value+MPN only; footprint R_0805 unchanged. Av = 1+976/976 = +2.
- gen_sch → ERC **0/0**; re-exported netlist.
- Value-only, so I updated R13/R14 values **in-place on the routed `channel.kicad_pcb`**
  (pcbnew SetValue) — confirmed R13 on BUF_OUT↔BUF_FB, R14 on BUF_FB↔GND (the CFA Rf/Rg) —
  preserving the routing. DRC **0/0/0**, schematic-parity **0**.
- Also ran a full clean reproducible pipeline (gen_pcb → DSN → FreeRouting score 996.01, 0
  unrouted → import → fill) to confirm a fresh rebuild reproduces 0/0/0 with 976R. Updated
  gen_pcb.py comments to 976R. Board: 208 tracks, 52 vias, 4 layers, R13=R14=976.
- BOM reconcile (`reports/bom_reconcile.txt`): **DESIGN == B3 : YES** (48 lines, 19 MPNs, 0
  mismatches). B3 had already switched its CSV to 976 / RC0805FR-07976RL in parallel.
- Updated INTERFACE.md (topology, buffer real-parts table, ASCII diagram, a 976-Ω note).

**Results:** ERC 0/0 · DRC 0/0/0 · parity 0; design BOM == B3 BOM (incl. 976 Ω). No
placement/route change (value-only). Av unchanged at +2.

**Decisions & why:** datasheet/sim-pinned CFA feedback (976 Ω, THS3491 Table G=+2) over the
earlier 1.21 kΩ generic-class value — for a CFA Rf sets the loop, so the datasheet value
governs; B2 validated it against TI's official SPICE model.

**State vs criteria:** ALL met; Phase-B design gate closed. `channel` cell ready for Phase C ×12.

---

## 2026-07-08 — session 4 — 2026-07 rework recap + rail reverse-polarity protection + doc reconcile

**Context:** a prior 2026-07 session reworked the channel but did not log here; this entry
records that rework (reconstructed from the design files + the `gen_sch.py` DESIGN NOTES
docstring) plus the rail-protection work and doc reconciliation done this session.

**2026-07 design rework (prior session, folded in here):**
- Output buffer → **populate-or-bypass, DNP by default.** New `JP_BUF` (R18, 0 Ω,
  `SHAPER_OUT→BUF_OUT`) fitted by default XORs the whole THS3491 block. Default build: CR-210
  drives the 49.9 Ω back-term directly (OUT_50 = ½·SHAPER_OUT into 50 Ω).
- Test input reworked: `R5` = 47 Ω shunt termination to GND, `C3` = 1 pF series into `CSP_IN`;
  net `TEST_N` removed.
- Per-rail decoupling reduced to 4.7 Ω + 10 µF (all eight 0.1 µF HF caps dropped).
- `channel.kicad_sch` redrawn as a human-review **WIRED** layout (`gen_sch.py` rewritten).
- Sourcing folded in (2026-07-07 sweep): Cf NRND → CL21B104KCFNNNE; Digi-Key PN fixes; 10 µF
  25 V bulk flagged Active-but-0-stock (16-wk lead).

**This session — rail protection (the TBD the rework left "pending review"):**
- Researched supply abs-max of every rail part, adversarially verified vs primary datasheets:
  **weakest = ±13 V** (Cremat CR-200 explicit abs-max; CR-112/CR-210 spec-table "maximum");
  THS3491 = ±16.5 V. Rails are ±12 V nominal → **~1 V headroom, effectively closed: no passive
  shunt Zener/TVS can both idle off at 12 V and clamp below 13 V** → over-voltage clamping of
  the modules is infeasible; over-voltage becomes an operational limit.
- Chose (with user) **reverse-polarity block + fault interrupt**; dropped the drawn shunt-Zener.
- Implemented per rail: `+VDC_IN → F_P (PTC) → +VDC_F → D_RP (Schottky, cathode→+VDC) → +VDC`
  (mirror on −rail, anode→−VDC). Parts: onsemi **SS14** (40 V/1 A, `Diode_SMD:D_SMA`) +
  Littelfuse **1206L010/60WR** PTC (0.1 A hold / 0.25 A trip / 60 V, `Fuse:Fuse_1206_3216Metric`)
  — both Active/in-stock, native KiCad footprints. Added `Device:D_Schottky` +
  `Device:Polyfuse_Small` to SYMSRC; new nets `+VDC_IN/+VDC_F/−VDC_IN/−VDC_F`; refs `F1/F2`
  (PTC), `D1/D2` (Schottky). Removed the TBD `R_ZP/D_ZP/R_ZN/D_ZN` placeholders.
- Netlist-audited the series chain + Schottky polarity; regenerated; **ERC 0/0**. Added the 4
  parts to `single-channel-bom.csv` (now 45 rows / 20 MPNs); refreshed `channel.pdf`.

**Docs reconciled:** `INTERFACE.md` + `SESSION_REPORT.md` updated to the reworked topology
(buffer optional, rail protection, test-inject, decoupling, 45-ref/20-MPN counts, PCB-stale
flag, OUT_50 default-vs-populated amplitudes); BOM `R_test` row description fixed (said
"series R"; now shunt termination to GND).

**Results:** schematic **ERC 0/0**; design BOM ↔ CSV = **45 refs / 20 MPNs**. **PCB
`channel.kicad_pcb` is STALE** (predates the rework) — layout rebuild deferred by request.

**Decisions & why:** reverse-block + fuse over shunt-Zener because the ±13 V module abs-max vs
±12 V nominal closes the over-voltage window; reverse polarity (swapped leads) is the real,
achievable bench-error protection. Series Schottky (SS14) blocks reverse; PTC interrupts
sustained faults; ~0.4 V drop leaves the rails ≈ ±11.6 V (> the modules' ±6 V and the THS3491's
±7 V minimums).

**State vs criteria:** schematic + BOM + docs updated & mutually consistent (ERC 0/0). Open
item: rebuild `channel.kicad_pcb` against the new netlist.

---

## 2026-07-08 — session 5 — PCB rebuild: thin, tile-able CHANNEL-ROW cell (autonomous)

**Objective (user):** lay out the PCB. Requirements: bias+output on one grouping, test+input on
the other; edge-mount **MCX female** receptacles; keep the channel **as thin as possible** for
multiple channels; keep **common circuitry at one end**, anticipating a multi-channel board.

**Floorplan chosen (confirmed with user):** each channel is a horizontal **ROW** — signal
flows left→right (front-end → CR-112 → CR-200 → CR-210 → THS3491) — with the four MCX at the
two **short ends** (left edge = `SIPM`(IN)+`TEST_IN`; right edge = `OUT_50`+`BIAS_IN`) and a
shared **COM row** across the top (J5 screw terminal + F1/F2 PTC + D1/D2 Schottky + C10/C11
bulk, power in at the rear). Channels stack vertically below the COM row.

**Work:**
- Measured footprints (pcbnew): MCX courtyard ~10×11.5 (2 stacked/end ⇒ the ~24 mm channel
  height), SIP-8 module 21.4×3.6 @ rot 90, screw terminal 16×11, CP_Elec bulk 9.4×7.2.
- Rewrote `gen_pcb.py` `PLACE`/`W`/`H`/`DNP_BY_REF` for the new floorplan and the 2026-07 refs:
  `U1..U4`, `J1..J5`, `F1/F2` (PTC), `D1/D2` (SS14), `R18`=JP_BUF(fit); DNP set = the buffer
  block {U4,R13,R14,R16,R17,C12,C13} + bias/BLR jumpers {R2,R4,R12}. Added net-class patterns
  for `*VDC_IN*`/`*VDC_F*` (power). 2 M3 holes in the COM row. Hid J1–J4/R2/R4/R13 silk refs to
  clear F.Silk DRC. Board = **138 × 52 mm**.
- Placement DRC clean (0 violations). Installed a **Java 25** runtime (Temurin 25.0.3 JRE,
  downloaded from Adoptium to `%LOCALAPPDATA%\temurin25` — FreeRouting 2.2.4 needs class 69;
  Java 21 was too old). Ran the pipeline: `export_dsn.py` → FreeRouting (`-de channel.dsn -do
  channel.ses -mp 200`) → `import_ses.py` → `fill_zones.py` → `kicad-cli pcb drc`.
- First route left `+VDC_IN` (J5.1→F1.1) unrouted — mounting hole H1 sat in that path; moved
  J5 to x=24 and H1 back to the top-left corner. Re-route = **100 % routed**.

**Results:** `channel.kicad_pcb` — **DRC 0 errors / 0 warnings / 0 unconnected**, 4-layer
(F.Cu / In1=GND / In2=−VDC / B.Cu=+VDC pour), fully autorouted (FreeRouting 2.2.4 score 996.4),
**171 tracks, 41 vias**. Matches the reworked netlist.

**Decisions & why:** channel-row + shared COM row per the user's tiling sketch — connectors on
the short ends stay on the array perimeter when channels stack; MCX-pair height (~24 mm) sets
the thin dimension. BIAS_IN enters at the right edge (grouped with OUT) and runs the board
length as `hv_bias` to the front-end/SIPM at the left — a deliberate consequence of the
connector grouping. MCX `Edge.Cuts` cutouts parked on `Dwgs.User` (restore at the true edge in
the GUI), same convention as the prior board.

**State vs criteria:** ALL met — schematic ERC 0/0, PCB DRC 0/0/0, docs reconciled. GUI
finishing left: restore MCX edge cutouts; optional per-connector silk labels. Single channel
is fab-ready as a cell; the multi-channel board tiles this row under the shared COM row.

**Schematic-parity note (benign):** `kicad-cli pcb drc --schematic-parity` reports ~92
*metadata* items — footprint↔symbol library-link mismatches (the `.kicad_pcb` footprints carry
the bare footprint name, not `lib:name`), footprints not carrying the symbols' BOM fields
(`MPN`/`Manufacturer`/`Distributor PN`), and the 2 mounting holes not in the schematic. **None
are electrical** (DRC copper/clearance/connectivity = 0/0/0; netlist matches). A KiCad GUI
*Update PCB from Schematic* reconciles the links/fields cleanly. Doing it headlessly via
`fp.SetFPID(lib:name)` fixes the link-parity but then re-triggers a `lib_footprint_mismatch`
DRC on the 4 intentionally-modified MCX (Edge.Cuts parked on Dwgs.User), so the parity cleanup
is left for the GUI pass rather than trading benign parity for a real DRC hit.

---

## 2026-07-08 — session 6 — push + 10 µF bulk swapped to an in-stock part

- **Pushed** to `github.com/Brunner-neutrino-lab/cremat-multi-channel-amplifier` (`main` → origin/main;
  Git Credential Manager auth).
- **10 µF 25 V X5R bulk fitted part swapped** off the 0-stock Samsung CL21A106KAYNNNE to the
  in-stock **KEMET C0805C106K3PACTU** (DK 399-11939-1-ND). Re-verified live on Digi-Key:
  ~255 k in stock, Active, $0.23 q1 / $0.083 q100 — beat Taiyo Yuden (in stock but ~600 pcs),
  TDK (stocked but NRND), Murata/Yageo (0-stock). Samsung retained as documented alternate
  (same-mfr fallback CL21A106KACLRNC, ~71 k). Value-only swap in `gen_sch.py` (8 caps) + the 8
  CSV rows; **0805 footprint and PCB unchanged** (schematic ERC re-run 0/0). Docs updated
  (INTERFACE, SESSION_REPORT, SOURCING-VERIFICATION).

---

## 2026-07-08 — session 7 — fix: 'Update PCB from Schematic' re-spawned all components

**Symptom (user):** clicking *Update PCB from Schematic* in the GUI added a fresh copy of
every footprint instead of updating the existing ones.

**Cause:** `gen_pcb.py` built the board by loading bare footprints and assigning nets by name,
but never wrote each footprint's **schematic-symbol UUID** into its `(path ...)`. KiCad's
Update-from-Schematic matches symbols→footprints **by UUID**; with no UUIDs it treated every
symbol as new and re-added the whole board. (Same root gap behind the "annotation errors"
netlist warning and the footprint↔symbol parity items.)

**Fix:**
- `gen_pcb.py` now parses each component's UUID from the netlist `(tstamps ...)` and calls
  `fp.SetPath(KIID_PATH("/" + uuid))`; mounting holes get `SetBoardOnly(True)` so Update
  ignores them (were flagged `extra_footprint`).
- Applied the same **in place** to the committed routed board (a small pcbnew pass) so its 45
  footprints carry their UUIDs **without re-routing** — DRC stays **0/0/0**, routes intact.
  Remaining parity (footprint library-link + MPN-field, 90) is benign and does NOT cause the
  re-spawn; it's the FPID/field metadata left for a GUI reconcile (see the session-5 note —
  forcing the FPID headlessly re-triggers `lib_footprint_mismatch` on the modified MCX).

**To apply on an already-open project:** either (a) close the board without saving, `git pull`,
reopen; or (b) in the open session, undo the spawn and re-run *Update PCB from Schematic* with
**"Re-link footprints to schematic symbols based on their reference designators"** checked —
that matches by refdes and writes the UUIDs. Do one or the other, not both.

---

## 2026-07-11 — session 8 — edge-mount MCX (user's own footprint) + connector orientation

Three user-reported connector issues on the routed board; all fixed, board re-routed,
**DRC 0 errors / 0 unconnected** (4 benign `lib_footprint_mismatch` from the intentional
Edge.Cuts → Dwgs.User demotion).

**1. MCX edge cutout pointed the wrong way (Plan A).** Fixed `gen_pcb.py`: J1–J4 place by
footprint **ORIGIN** at rot 90 (right edge) / 270 (left edge); the **board outline cuts the
notch itself** (reads each notch back from the placed footprint, then demotes the footprint's
Edge.Cuts → Dwgs.User); FPID keeps the `cremat:` prefix (`SetFPID`); `write_dru()` emits
`channel.kicad_dru` waiving `edge_clearance` for the MCX shield tabs. Re-autorouted with
FreeRouting — see `docs/FREEROUTING.md` for the Java-25 + **dead-proxy** headless recipe
(reinstall Java 25 + freerouting jar on the new machine).

**2. Power connector J5 faced inward.** Screw-terminal wire funnels faced the board interior →
`gen_pcb.py` J5 rot `0` → **`180`** so the funnels face the top edge (outward). Render-verified.

**3. Swapped in the user's downloaded MCX footprint.** Replaced project SnapEDA
`cremat:MCX_CONMCX013_EdgeMount` with the user's Linx `CONMCX013-T` package
(`~/Downloads/CONMCX013_T (1).zip`). Installed as **`cremat:MCX_CONMCX013-T`**
(`lib/cremat.pretty/MCX_CONMCX013-T.kicad_mod` + `CONMCX013-T.step`) with two required edits:
shield pads `G1`/`G2` → **`2`** (GND connects via `Conn_Coaxial` pin 2), and trimmed the
connector-tiling ±6 mm Edge.Cuts extension segments so the outline logic reads the true notch.
`gen_sch.py` `FP_MCX` + the `.kicad_dru` condition updated. ERC 0; netlist-membership
**IDENTICAL** to baseline (footprint field only, circuit unchanged).

**4. MCX 3D model faced up ("facing the wrong way").** Raw STEP points the coax barrel +Z
(vertical); an edge-launch jack must lie flat with the coax face OFF the edge. Fix =
**`(rotate (xyz 270 0 0))`** on the model block in `MCX_CONMCX013-T.kicad_mod` (rot90 → mating
face inboard; rot270 → coax socket off-edge = correct; `offset 0` seats it — the jack straddles
the board edge). **3D-cosmetic only** → patched the 4 model blocks in the routed
`channel.kicad_pcb` directly, **no reroute**, DRC unchanged. Datasheet: CONMCX013 = 50 Ω MCX
jack, board-edge cutout, SMT, snap-on; `-T` = tape-&-reel of the SAME part (BOM PN unchanged).

**Gotcha (cost hours):** `${KIPRJMOD}`-relative 3D model paths do NOT resolve when you render a
board **copy from another directory** (e.g. scratchpad) — that model silently doesn't render,
while stock `${KICAD10_3DMODEL_DIR}` models still show. Run test renders from the real design
dir. Use `kicad-cli pcb render --quality high` (not `basic`) to judge fine 3D.

Old `MCX_CONMCX013_EdgeMount.kicad_mod` left in the lib (now unused) pending the user's call on
deleting it.

