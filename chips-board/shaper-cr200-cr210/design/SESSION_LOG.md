# Session Log — A4 `shaper-design`

> Ground truth, append-only. One dated entry per working session.

Track: `A4 shaper-design` · Sub-component: `shaper-cr200-cr210` · Aspect: `design`
Reads (inputs): `reference/cremat-CR-160-R7` (CR-200 P/Z + per-rail decoupling + CR-210/JU1
bypass), `reference/cremat-x6-board`, `hardware/gen_sch.py`/`gen_pcb.py`/`fill_zones.py`/
`export_dsn.py`/`import_ses.py`, `docs/FREEROUTING.md`, `docs/KICAD_WITH_CLAUDE_CODE.md`,
`hardware/lib/cremat.kicad_sym` (CR-200/CR-210 SIP-8 generic symbols).
Success criteria (mirror of report): per-milestone ERC 0 / DRC 0/0; P/Z + per-rail
decoupling per CR-160-R7; M2 populate-XOR (CR-210 ⊕ JP_BLR 0R) matching CR-160-R7 JU1.

---

## 2026-06-25 — session 1 — setup + reference decode

**Goal this session:** read the charter/conventions/brief + prior art, decode the CR-160-R7
topology around the CR-200/CR-210, set up the design subdir, and build the M1 schematic.

**Did:**
- Read `00-CHARTER.md`, `01-CONVENTIONS.md`, the A-shaper brief, and the toolchain scripts
  (`gen_sch.py`, `gen_pcb.py`, `fill_zones.py`, `export_dsn.py`, `import_ses.py`,
  `scripts/erc.sh`, `scripts/drc.sh`), `docs/FREEROUTING.md`, the symbol lib.
- Decoded `reference/cremat-CR-160-R7/CR-160-R7.net` (the authoritative connectivity).
- Created `chips-board/shaper-cr200-cr210/design/` and copied the gen scripts + `lib/`
  (cremat.kicad_sym + cremat.pretty) + lib tables + SESSION templates.

**Results (CR-160-R7 decode — the design basis):**
- CR-200 = U4: pin1 input ← net9 (R7-Pad2, input node); pin2 P/Z ← net3 (R7-Pad1);
  pins 3/6/7 = GND; pin4 = −11V; pin5 = +11V; pin8 output → net4 (JU1-Pad1 = CR-210 in).
- **Pole-zero network** = R7, a **200k trimpot** wired across CR-200 input (pin1) ↔ P/Z
  (pin2), wiper to the input node. This is the CR-200 P/Z cancellation trim.
- **Per-rail decoupling** (per the EL5163 stages + modules): series 4.7 Ω (R10–R16 region)
  + 10 µF bulk (C-series, 1206) + 0.1 µF HF (C11/C12 0805) per rail. I adopt
  4.7 Ω + 10 µF + 0.1 µF per supply pin at each module.
- CR-210 = U5: pin1 input ← net4 (CR-200 out / JU1-Pad1); pins 2/3/6/7 = GND; pin4 = −11V;
  pin5 = +11V; pin8 output → net19 (JU1-Pad2). **JU1 bridges pin1(CR-200 out) ↔ pin2
  (CR-210 out)** — i.e. closing JU1 shorts across the CR-210 = bypass. Populate-XOR:
  fit CR-210 (JU1 open/DNP) **or** fit JU1 0R (CR-210 DNP).
- Net classes/DRC severities from `hardware/multi-channel-cremat-amplifier.kicad_pro`:
  Default 0.2 clr, signal 0.33 trk, power 0.5 trk; creepage/clearance/unconnected = error.

**Decisions & why:**
- Build a purpose-written `gen_sch.py` for a **standalone single-instance** shaper board
  (the reuse target is the *method*, not the 12× root). Milestone-parameterised: `M="M1"`
  emits CR-200 + P/Z + decoupling + MCX I/O + screw terminal; `M="M2"` adds CR-210 + its
  decoupling + JP_BLR 0R bypass with the populate-XOR DNP.
- Keep MCX `CONMCX013`, 3-pos screw terminal, 4-layer (GND In1 + −VDC In2) to match the
  final board I/O/stackup (charter locked decision).
- Generic parts now (200k, 100? no — 200k P/Z; 4.7 Ω; 10 µF; 0.1 µF; 49.9 Ω out series);
  A6 swaps to real parts in Round 2.

**Dead-ends / surprises:** `pdftoppm` not available, so the CR-160-R7 schematic PDF can't be
rasterised — used the `.net` netlist (authoritative) instead.

**State vs criteria:** criteria stated in report; none met yet (about to generate M1 sch).

**Next:** write `gen_sch.py` (M1), run ERC; then `gen_pcb.py` placement → FreeRouting → DRC.

---

## 2026-06-25 — session 2 — M1 build (CR-200) + M2 build (+CR-210), both ERC/DRC 0

**Goal this session:** generate M1 then M2 schematics + 4-layer routed boards, gate each at
ERC 0 / DRC 0/0/0.

**Did (exact pipeline, run with KiCad 10 bundled python + kicad-cli + tools/freerouting):**
- Wrote purpose-built `gen_sch.py` (standalone single-instance, milestone param SHAPER_MS)
  and `gen_pcb.py` (explicit per-role placement, 4-layer, GND/−VDC planes). Created
  `shaper.kicad_pro` from the hardware net classes; pointed export/import/fill scripts at
  `shaper.*`.
- M1: `SHAPER_MS=M1 python gen_sch.py` → `kicad-cli sch erc` → **0/0**.
  `SHAPER_MS=M1 python gen_pcb.py` → placement DRC (after moving J_PWR clear of H3
  courtyard) → 0 err. `export_dsn.py` → `java -jar freerouting-2.2.4.jar -de shaper.dsn
  -do shaper.ses` (22 nets, 0.81 s) → `import_ses.py` → `fill_zones.py` (4 zones) →
  `kicad-cli pcb drc` → **0 err / 0 warn / 0 unconnected**.
- M2: `SHAPER_MS=M2 python gen_sch.py` (20 symbols) → ERC **0/0**. `gen_pcb.py` → placement
  0 err → DSN → freerouting (37 nets, 1.19 s) → SES → fill → DRC **0/0/0**. Routed board =
  115 tracks+vias, 4 layers. Rendered `plots/shaper_M2_top.png`.

**Results (figures):**
- M1 ERC 0/0; M1 DRC 0/0/0. M2 ERC 0/0; M2 DRC 0/0/0.
- M1 connectivity (verified): SH_IN = J1.1+U1.1+RV1.1; PZ = U1.2+RV1.2+RV1.3 (200k across
  in↔P/Z, wiper to input = CR-160-R7 R7); SHVP/SHVN = U1.5/U1.4 + 4.7Ω+10µF+0.1µF each;
  SH_OUT→49.9Ω→OUT→J2.
- M2 connectivity (verified): SH_OUT = U1.8 + U2.1(CR-210 in) + R5.1(JP_BLR); BLR_OUT =
  U2.8 + R5.2 + R6.1; CR-210 decoupling BLVP/BLVN identical scheme. DNP: U2=False (fitted),
  R5=True (bypass not fitted) — populate-XOR holds on schematic AND routed PCB.

**Decisions & why:**
- Module +Vs/−Vs (power_in pins) sit on filtered rail nodes (post-4.7Ω). ERC can't see a
  rail driven through a passive R, so I add a PWR_FLAG on each filtered node (SHVP/SHVN,
  +BLVP/BLVN in M2). Electrically the RC filter is unchanged; the flag only declares the net
  driven. This cleared the 2 "Input Power pin not driven" ERC errors → 0/0.
- 200k P/Z trimpot mirrors CR-160-R7 R7 (200k) — the authoritative CR-200 P/Z network.
- 4.7Ω + 10µF + 0.1µF per rail per module mirrors CR-160-R7's series-R + bulk + HF bypass.
- JP_BLR DNP=True by default (CR-210 active variant shipped); the bypass variant flips the
  two DNP flags. Bypass topology = CR-160-R7 JU1 (bridges CR-200 out ↔ CR-210 out).
- Board outline 168×80 mm standalone eval size; Phase-C reuses the *topology*, not the size.

**Dead-ends / surprises:**
- KiCad 10 sexpr netlist export uses multi-line `(ref "X")` form the original gen_pcb.py
  regex didn't match → sidestepped by building the PCB directly from the gen_sch spec
  (import gen_sch), which is cleaner and needs no netlist file.
- First M1 placement had a J_PWR↔H3 (mounting hole) courtyard overlap; moved J_PWR to
  (30,70) → clean.

**State vs criteria:** ALL M1 + M2 criteria met. Sub-component design done pending the A6
real-parts swap (Round 2) — generics listed in ../INTERFACE.md.

**Next:** await A6 models-bom report → swap generics→MPNs in gen_sch values → re-run
ERC/DRC → confirm design BOM == models BOM. Hand INTERFACE.md to Phase-B / A5.

---

## 2026-06-25 — session 3 — Round-2 A6 real-parts swap + re-verify (both milestones)

**Goal this session:** swap every generic to A6's chosen real part (Value+MPN+Footprint),
reconcile refs/scope with A6, re-run ERC+DRC for M1+M2 (each 0/0/0), and confirm design
BOM == A6 BOM incl. the DNP table.

**Did (reproducible — edited gen_sch.py / gen_pcb.py, then regenerated):**
- Added a `PARTS` metadata table in `gen_sch.py` keyed by spec role → (Value, MPN, Manufacturer,
  Distributor PN) straight from A6's `models-bom/shaper-bom.csv`. `build_spec` now pulls the
  Value from it; `sym_instance` emits hidden `MPN`/`Manufacturer`/`Distributor PN` props per part.
- Footprint change: **10 µF caps 1206 → 0805** (A6's Samsung CL21A106KAYNNNE is 0805). Dropped
  the `FP_C1206` constant; 10 µF + 0.1 µF + the new bulk all use stock 0805 / CP_Elec_6.3x7.7.
- Scope reconcile — added the two A6 fitted lines the generic board lacked:
  (1) **100k P/Z fixed R** (A6 `R_PZ2` → design `R1`), wired P/Z-node → GND as the trim companion;
  (2) **two 100 µF rail-bulk electrolytics** (A6 `Cbulk_p/n` → `C9/C10`, `Device:C_Polarized`,
  correct polarity: +rail cap +on +VDC; −rail cap +on GND / −on −VDC). Added matching PLACE
  entries in `gen_pcb.py` (R_PZ2, C_BULKP, C_BULKN).
- Fixed a self-inflicted ERC break: I'd briefly moved J_PWR to y=100, but the rail PWR_FLAGs are
  keyed to J_PWR @ (30,95) — reverted J_PWR to (30,95); the bulk caps live at (130/145,60) instead.
- Pipeline per milestone: `SHAPER_MS=M{1,2} gen_sch.py` → `kicad-cli sch erc` → `gen_pcb.py` →
  placement DRC → `export_dsn.py` → freerouting-2.2.4 (`-de/-do`, JDK-25) → `import_ses.py` →
  `fill_zones.py` → `kicad-cli pcb drc`. Exported BOMs with `kicad-cli sch export bom`.

**Results (figures):**
- ERC M1 0/0; ERC M2 0/0. DRC M1 0/0/0/0; DRC M2 0/0/0/0 (error/warn/unconnected/parity).
- FreeRouting: M1 28 nets routed 0 unrouted; M2 43 nets, completed 0 unrouted (final score 995.4).
- Footprints placed 0 missing both milestones (15 in M1, 23 in M2) → CP_Elec + 0805-10µF load fine.
- BOM M1 = 15 parts, M2 = 23 parts (22 fitted + JP_BLR DNP). **All 12 distinct A6 MPNs present,
  byte-identical.** DNP: U2 (CR-210-R0) fitted ⊕ R6 (0R) DNP — verified on schematic AND routed
  PCB (`IsDNP()`). Matches A6 DNP table.

**Decisions & why:**
- Bind to A6 by **Value+MPN** (the stated contract) and add A6's extra fitted lines rather than
  argue scope. Noted in SESSION_REPORT the A6 CSV's R_PZ2/CR-160-R7-R9 citation is slightly off
  (R9 is in the excluded buffer section), but fitted the 100k anyway for BOM parity.
- Polarized symbol for the electrolytics with rail-correct polarity (ERC-clean, real part is polar).

**Dead-ends / surprises:** adding R_PZ2 to the R counter renumbered refs — JP_BLR moved R5→R6,
OUT series R6→R7. Updated INTERFACE.md refs + DNP table to the new numbering.

**State vs criteria:** ALL M1 + M2 criteria still met, now with real parts. Real-parts gate closed.

**Next:** hand off to Phase-B / A5 (INTERFACE.md updated). Coordinator commits.

---

## 2026-06-25 — session 4 — coordinator reconciliation: remove the 100k P/Z fixed R

**Goal this session:** act on the coordinator finding that the 100k "P/Z fixed R" (`R_PZ2`,
fitted as design `R1`) does **not** belong on the shaper board. Remove it from design + BOM,
regenerate + re-route both milestones, re-gate ERC/DRC, confirm design BOM == A6 BOM.

**Finding (verified against `reference/cremat-CR-160-R7/CR-160-R7.net`):**
- The 100k cited CR-160-R7 `R9`. But `R9` (100k) is on **net code 10 `Net-(R9-Pad2)` → `U7`
  pin6 (MAX4649 mux) + `SW1` pin1 (gain/polarity DIP)** (pin1 → +11V rail) — i.e. the
  **buffer/mux/DIP section this sub-component excludes**, not the CR-200 P/Z.
- The CR-200 pole-zero is the **200k trimpot `R7` alone**: net code 3 (`R7-Pad1` → `U4` pin2 =
  CR-200 P/Z) + net code 9 (`R7-Pad2` → `U4` pin1 = CR-200 input). `U4` = CR-200. So the 100k
  must NOT be on the shaper board → removed.

**Did (reproducible — edited gen scripts, regenerated + re-routed both milestones):**
- `gen_sch.py`: dropped the `R_PZ2` entry from the `PARTS` table and from `build_spec` (it had
  been a `PZ`→`GND` shunt). Replaced with a comment documenting why the 200k trimpot is the
  sole P/Z element + the CR-160-R7 net-code-10 evidence.
- `gen_pcb.py`: removed the `R_PZ2` PLACE entry.
- Removing R_PZ2 from the R counter **reverts the A4 renumber**: P/Z trim is `RV1`, 4.7Ω
  decoupling now `R1`–`R4` (M2) / `R1`–`R2` (M1), JP_BLR `R5` (was R6), OUT series `R6` (was R7).
- Pipeline per milestone: `SHAPER_MS=M{1,2}` → `gen_sch.py` → `kicad-cli sch erc` → `gen_pcb.py`
  → `export_dsn.py` → freerouting-2.2.4 (JDK-25, `-de/-do`) → `import_ses.py` → `fill_zones.py`
  → `kicad-cli pcb drc`. Re-exported `reports/bom_M{1,2}.csv` + re-rendered `plots/shaper_M2_top.png`.

**Results (figures):**
- **ERC M1 0/0; ERC M2 0/0. DRC M1 0/0/0/0; DRC M2 0/0/0/0** (error/warn/unconnected/parity) —
  `reports/erc_M{1,2}.json`, `drc_M{1,2}.json` all empty arrays.
- FreeRouting: M1 26 unrouted → 0 (score 995.06); M2 41 unrouted → 0 (score 995.30).
- Footprints placed 0 missing: M1 14, M2 22. BOM lines: M1 = 14 fitted; M2 = 21 fitted + 1 DNP
  (R5 JP_BLR). No 100k anywhere in netlist or schematic (grep = 0).
- **P/Z verified:** net `/PZ` = `RV1` pin2 + pin3 + `U1` pin2 (CR-200 P/Z); `/SH_IN` = `J1`.1 +
  `RV1`.1 + `U1`.1. Trimpot across input↔P/Z, wiper to input = CR-160-R7 R7. Nothing floating.
- DNP XOR still holds: U2 (CR-210-R0) fitted ⊕ R5 (0R) DNP — schematic + routed PCB.

**Decisions & why:** kept the reverted (no-100k) ref numbering since it's the natural output of
the generator with R_PZ2 gone, and updated INTERFACE.md + BOM to match — internally consistent.

**State vs criteria:** ALL M1 + M2 criteria still met. 100k gone from design AND A6 BOM; P/Z is
the 200k trim only; design BOM == A6 BOM for M1 and M2 incl. the DNP table.

**Next:** none pending — reconciliation closed. Coordinator commits.
