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

