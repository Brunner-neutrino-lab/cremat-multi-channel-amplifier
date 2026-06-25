# Session Log — A1 `csp-design`

> Ground truth, append-only. One dated entry per working session.

Track: `A1 csp-design` · Sub-component: `csp-cr112` · Aspect: `design`
Reads (inputs): brief `docs/agent-project/briefs/A-csp-cr112.md`; `00-CHARTER.md`,
`01-CONVENTIONS.md`; prior art `reference/cremat-CR-150-R5/CR-150-R5.net` (support circuit),
`hardware/gen_sch.py` / `gen_pcb.py` / `fill_zones.py` / `export_dsn.py` / `import_ses.py`,
`docs/KICAD_WITH_CLAUDE_CODE.md`, `docs/FREEROUTING.md`, `hardware/lib/cremat.kicad_sym`.
Success criteria: ERC 0, DRC 0 on a 4-layer board; per-rail decoupling per CR-150-R5;
bias front-end with working 0R-bypass DNP; `INTERFACE.md` current.

---

## 2026-06-25 — session 1 — generic-parts CR-112 CSP board, ERC 0 / DRC 0/0/0

**Goal this session:** design the standalone CR-112 CSP eval board (bias front-end +
CR-112 + module decoupling + test input, MCX I/O, screw terminal, 4-layer), generic parts,
ERC+DRC to 0/0, route with FreeRouting, publish INTERFACE.md.

**Did:**
- Read all required docs + prior art. Studied `CR-150-R5.net` for the CR-11X support
  circuit: per-rail decoupling = **4.7 Ω series (R7/R8) + 10 µF (C5/C6)** at each Vs pin,
  and the test injection = **47 Ω (R3) + 1 pF (C2)** into the CSP input. Adopted that.
- Scaffolded `chips-board/csp-cr112/design/`: copied `lib/cremat.kicad_sym`,
  `lib/cremat.pretty`, and `fill_zones.py`/`export_dsn.py`/`import_ses.py` (paths adapted to
  `csp-cr112.*`). Wrote `sym-lib-table`, `fp-lib-table`, and `csp-cr112.kicad_pro` (cloned
  net-class + DRC-severity settings from the hardware project).
- Wrote `gen_sch.py` (adapted from `hardware/gen_sch.py`, net-label-at-pin method). Spec:
  J1 BIAS_IN(MCX)→Rf1(10k)/JP_Rf1(0R,DNP)→Cf(100nF/100V)→Rf2(10k)/JP_Rf2(0R,DNP)→FE;
  J2 SIPM(MCX) on FE; Cc(0.22µF/100V) FE→CSP_IN; J3 TEST_IN(MCX)→R_test(47)→C_test(1pF)→
  CSP_IN; U1 CR-112 (cremat:CR-11X); per-rail R6/R7(4.7)+C4/C6(10µF)+C5/C7(0.1µF) on
  +VS_F/-VS_F; bulk C8/C9(10µF); J5 3-pos screw terminal.
- `gen_sch.py` → `csp-cr112.kicad_sch`. ERC first run = **2 errors** `power_pin_not_driven`
  on U1 pin 5/6: the CR-112 +Vs/-Vs sit behind the 4.7 Ω series Rs on +VS_F/-VS_F, and ERC
  can't trace power-drive through a passive R. Fix: added a `PWR_FLAG` + net label on
  `+VS_F` and `-VS_F`. Re-run ERC = **0 errors / 0 warnings.**
- Exported netlist `csp-cr112.net`, verified every net node-by-node against the block
  diagram (BIAS_IN, N_filt, FE, CSP_IN, TEST_IN/N, CSP_OUT, ±VDC, ±VS_F, GND) — matches.
  22 components, unique refdes, all footprints resolve.
- Wrote `gen_pcb.py` (explicit hand-laid placement; signal flows left→right; MCX jacks on
  edges; CR-112 SIP-8 vertical; decoupling clustered at the module). 4 copper layers,
  In1=GND plane, In2=−VDC plane, GND pour added on F/B too by fill_zones.
- First DRC: 2 `courtyards_overlap` (screw terminal J5 16.1×10.9 mm overlapped bulk caps
  C8/C9) + 2 `silk_edge_clearance` (mounting-hole refs clipped by edge) + 4
  `silk_over_copper`. Fixes: enlarged board 80×70→90×72, relaid power region (J5 to bottom-
  left, C8/C9 clear to its right), inset mounting holes to 5.5 mm and hid their silk ref.
  DRC after replacement (pre-route) = **0/0** (+42 unconnected ratsnest, expected).
- `export_dsn.py` → `csp-cr112.dsn`. FreeRouting v2.2.4 on Java 25
  (`tools/jdk-25.0.3+9-jre/bin/java.exe -jar tools/freerouting-2.2.4.jar -de … -do …`):
  39 unrouted nets → completed in **0.91 s**, score 996.48, all routed.
- `import_ses.py` (routed tracks back), `fill_zones.py` (4 zones filled). Final DRC =
  **0 errors / 0 warnings / 0 unconnected.**
- Rendered evidence: `reports/csp-cr112.svg` (schematic), `reports/pcb-top.png` (3D top),
  `reports/bom.csv`. Visual check of the render: chain + decoupling + DNP jumpers correct.
- Wrote `../INTERFACE.md` (ports/ranges/handle/DNP/generic-substitution list) and this
  report set.

**Results:**
- ERC: **0 errors, 0 warnings** (`reports/erc.json`).
- DRC: **0 errors, 0 warnings, 0 unconnected** (`reports/drc.json`).
- Board: 4-layer, 90×72 mm, 22 comps + 4 M3 holes; 70 F.Cu tracks, 18 vias; planes GND(In1),
  −VDC(In2), GND pour F/B.
- BOM 12 distinct values; R2/R4 (0R bypass) correctly flagged DNP.

**Decisions & why:**
- Per-rail decoupling 4.7 Ω + 10 µF + 0.1 µF: the CR-150-R5 reference uses 4.7 Ω + 10 µF on
  each rail at the module; added a 0.1 µF HF bypass alongside the 10 µF (standard CSP
  practice; this is exactly the support the earlier rapid build omitted). Series R on each
  rail isolates the module supply → satisfies the brief's "per-module decoupling per
  CR-150-R5."
- Test injection 47 Ω + 1 pF: copied verbatim from CR-150-R5 (R3=47, C2=1pF). 1 pF gives a
  clean Q = C·ΔV charge step for bench/sim calibration.
- Bias front-end RC+R with 0R bypass: followed the brief's block diagram (the CR-150-R5's
  own bias network is a high-megohm scheme for a different detector, so I used the brief's
  filter topology, which is the authoritative spec for this build).
- `+VS_F/−VS_F` PWR_FLAG: required because a series R blocks ERC power-drive tracing; the
  flag asserts the rail is driven (it physically is, through R6/R7 from the screw terminal).
- 4-layer with GND + −VDC planes: charter-locked stackup and the verified FreeRouting recipe
  (outer layers free → routes cleanly). It did, in <1 s.

**Dead-ends / surprises:**
- `kicad-cli sch export netlist` prints a cosmetic "schematic has annotation errors"
  warning even with ERC 0/0 (CLI doesn't re-annotate); harmless — refdes are unique.
- Phoenix screw-terminal courtyard is large (16.1 mm); first placement crowded the bulk
  caps — fixed by widening the board and spacing the power region.

**State vs criteria:** ALL generic-parts criteria met — ERC 0, DRC 0/0/0, 4-layer,
per-rail CR-150-R5 decoupling present, 0R-bypass DNP working, INTERFACE.md published.
Open: real-parts swap (Round 2, after A3).

**Next:** await A3 models-bom report → swap generic values to real MPNs/footprints →
re-run ERC + DRC → update INTERFACE.md + BOM. (Coordinator resumes me at the A3 gate.)

---

## 2026-06-25 — session 2 — REAL-PARTS swap (A3 gate), ERC 0/0 · DRC 0/0/0

**Goal this session:** Round-2 real-parts gate. Swap every generic value to A3's chosen real
MPN (Value + MPN + Footprint), re-verify ERC+DRC to 0, confirm design BOM == A3 BOM, verify
CR-112 lead spec, update INTERFACE.md + reports.

**Read:** my session-1 work (`gen_sch.py`/`gen_pcb.py`/sch/pcb/reports), `INTERFACE.md`
generic-substitution list, A3 `models-bom/PARTS_REPORT.md` + `csp-cr112-bom.csv` (the
generic→real 1:1 map), `docs/FREEROUTING.md`.

**Did:**
- **gen_sch.py:** extended the `CH` spec to carry real `value, mpn, mfr` per row; `sym_instance`
  now emits `MPN` + `MFN` symbol fields. Set A3's MPNs: Rf 10k=RC0805FR-0710KL, 0R bypass=
  RC0805JR-070RL, Rdec 4.7=RC0805JR-074R7L, Cf 100nF/100V=CL21B104KCC5PNC, Cc 0.22µF/100V=
  GRM21AR72A224KAC5K, Ctest 1pF=CC0805CRNPO9BN1R0, Cdec10 10µF=CL21A106KAYNNNE, Cdec01 0.1µF=
  CL21B104KBCNNNC, MCX=CONMCX013, PWR=Phoenix 1715035, CR-112=CR-112-R2.1.
- **Footprint changes (only two):** (a) rail bulk 10 µF C4/C6 1206→**0805** per A3's 0805
  policy; (b) rail-entry bulk C8/C9 generic 10 µF/1206 → A3's **100 µF/25 V radial
  electrolytic** (`Device:C_Polarized` + `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm`, Nichicon
  UVR1E101MED). Added `Device:C_Polarized` to SYMSRC. Note: A3's report said `Device:CP` but
  the real KiCad-10 symbol is **`Device:C_Polarized`** (same pin geometry).
- **gen_pcb.py:** re-spaced C8/C9 (now D6.3 mm radial THT, ~6.8 mm courtyard, pads at x=0 &
  x=2.5) → C8(33,61) C9(44,61), clear of J5 and each other.
- **Pipeline re-run:** gen_sch → **ERC 0/0**; netlist export; gen_pcb → 22/22 placed, 0 missing,
  **pre-route DRC 0/0/42** (clean placement); export_dsn (OK); FreeRouting 2.2.4 on Java 25
  (`-de/-do`): 36 unrouted nets → **0 unrouted in 1.07 s**, score 996.77; import_ses;
  fill_zones (4 zones) → **final DRC 0 errors / 0 warnings / 0 unconnected.**
- Regenerated `reports/bom.csv` (now Value+MPN+Manufacturer+Footprint+DNP), schematic SVG,
  3D top render (radial caps render as proper THT cylinders next to J5 — visually confirmed).
- **BOM compare (script, by MPN):** all **12 A3 MPNs present in the design**; the design has
  **one extra** — R5 47 Ω `RC0805JR-0747RL` — because **A3's BOM omitted the test-path series
  resistor** (it lists only Ctest 1 pF). Per-rail decoupling count == A3 default (no 1 µF
  mid-cap added). Resolution: kept the design's verified 47 Ω+1 pF test path, used a real
  Yageo RC0805 part, flagged the one row for A3 to add.
- **CR-112 lead spec verified:** Cremat's own CR-150-R5 PCB lays the CR-11X (`8pinSIP`) as 8
  inline THT pads at **2.54 mm pitch** (x = 0…17.78), drill 0.762 mm → generic
  `PinHeader_1x08_P2.54mm_Vertical` (2.54 mm) is correct; **no footprint change for U1.**
- Updated `../INTERFACE.md` (dropped the substitution list; added real-parts BOM table + CR-112
  lead verdict + A3 reconciliation note + CONMCX013.step 3D note) and SESSION_REPORT.md.

**Results:**
- ERC: **0 errors, 0 warnings** (`reports/erc.json`).
- DRC: **0 errors, 0 warnings, 0 unconnected** (`reports/drc.json`).
- Footprints changed: 2 lines (C4/C6 1206→0805; C8/C9 1206 10 µF → radial 100 µF THT).
  **Re-route was needed** (THT footprint change) — done via the staged FreeRouting toolchain,
  routed clean.
- Design BOM == A3 BOM: **YES for all 12 A3 lines; +1 line (47 Ω R5) the design needs and A3
  must add.**

**Dead-ends / surprises:**
- A3's PARTS_REPORT cited `Device:CP` for the electrolytic but KiCad 10's Device lib has no
  `CP` — the symbol is `C_Polarized`. Used that; identical pin coords so labels resolve.
- A3's BOM is missing the 47 Ω test resistor (only Ctest listed). Flagged for the row add.

**State vs criteria:** ALL real-parts criteria met — ERC 0/0, DRC 0/0/0, every part real
(Value+MPN+MFN+FP), design BOM matches A3 1:1 except the one row A3 must add, CR-112 lead spec
confirmed, INTERFACE.md updated. **Track A1 COMPLETE.**

**Next:** none for A1. Coordinator: have A3 add the R5 (47 Ω RC0805JR-0747RL) row so
Models-BOM == Design BOM is byte-exact; (non-blocking) drop `CONMCX013.step` into
`lib/cremat.pretty/` to restore the MCX 3D model.
