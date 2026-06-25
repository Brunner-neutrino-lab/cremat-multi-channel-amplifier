# Session Report — A4 `shaper-design`

> The summary other tracks read instead of my log. Keep current (overwrite).
> A consumer integrates from this + `../INTERFACE.md` alone.

Track: `A4 shaper-design` · Aspect: `design` · Status: `criteria-met (M2 reached; real parts fitted, A6 swap done)`
Last updated: `2026-06-25`

## Objective
Standalone eval board for the **Cremat CR-200-1µs Gaussian shaper** (M1), then sequentially
integrate the **CR-210 baseline restorer** with a **0R-bypass DNP** (M2). 4-layer board,
MCX I/O, 3-pos screw-terminal ±12 V/GND. Deliver schematic + layout, ERC/DRC 0/0 per
milestone, and own `../INTERFACE.md`.

## Success / failure criteria (stated before work)
**M1 — CR-200 only**
- ✅ ERC 0 errors on the M1 schematic. (`reports/erc_M1.json`: 0 err / 0 warn.)
- ✅ DRC 0 errors / 0 unconnected on the M1 routed 4-layer board. (`reports/drc_M1.json`:
  0 err / 0 warn / 0 unconnected.)
- ✅ Pole-zero network present around the CR-200 (200k P/Z trim RV1, per CR-160-R7 R7).
- ✅ Per-rail decoupling present (4.7 Ω series + 10 µF bulk + 0.1 µF HF on +Vs and −Vs),
  per CR-160-R7 (R12/R13 4.7 Ω, C4/C5 10 µF + 0.1 µF bypass).
- ✅ I/O = MCX `CONMCX013` (J1/J2); power = 3-pos screw terminal (J3); 4-layer (In1=GND,
  In2=−VDC planes).

**M2 — CR-200 + CR-210**
- ✅ CR-210 (U2) inserted between CR-200 output and OUT, with its own per-rail decoupling.
- ✅ `JP_BLR` (R5) 0R bypass across the CR-210 (in↔out), **populate-XOR**: U2 CR-210 fitted
  (DNP=False) ⊕ R5 bypass DNP=True. Verified on schematic + routed PCB: exactly one path.
- ✅ Bypass scheme matches CR-160-R7 `JU1` (pin1 = SH_OUT = CR-200 out / CR-210 in;
  pin2 = BLR_OUT = CR-210 out).
- ✅ ERC 0 / DRC 0/0 on M2. (`reports/erc_M2.json` 0/0; `reports/drc_M2.json` 0/0/0.)

**Failure modes avoided:** P/Z + decoupling present; only one of {CR-210, bypass} populated;
no clearance/short.

## Current state
**M2 reached, real parts fitted — both milestones at criteria (ERC 0/0, DRC 0/0/0/0).**
Round-2 A6 real-parts swap **done**: every line now carries A6's chosen MPN + Manufacturer +
Distributor PN + real footprint (CR-200-1us-R2.1, CR-210-R0, Bourns 3296W-1-204LF, Yageo RC0805
1%/5%, Samsung CL21 MLCC, Nichicon UWT, TE/Linx CONMCX013, Phoenix 1715734). Design BOM ==
A6 `models-bom/shaper-bom.csv` for M1 and M2 incl. the DNP table.

**Reconciliation with A6 (refs + scope):** A6 sourced **two 100 µF rail-bulk electrolytics**
(A6 `Cbulk_p/n`, = design `C9/C10`) the generic board lacked; added so the design BOM equals
A6's. The **10 µF caps moved 1206→0805** (A6's Samsung CL21A106 is an 0805 part) — the only
footprint change; it re-placed + re-routed cleanly (no DRC impact). All other footprints
unchanged.

**2026-06-25 coordinator reconciliation — 100k P/Z fixed R REMOVED:** the 100k (A6 `R_PZ2`,
briefly fitted as design `R1`) has been **removed** from design + A6 BOM. Its CR-160-R7 `R9`
citation was wrong: in the reference netlist `R9` (100k) is on **net code 10 → `U7` pin6
(MAX4649 mux) + `SW1` pin1 (gain/polarity DIP)** — the buffer/mux section this sub-component
excludes — not the CR-200 P/Z. The **CR-200 pole-zero is the 200k trimpot `RV1` alone** (= ref
`R7`: net codes 3/9 → CR-200 pins 2/1). Removing it reverted the renumber: 4.7Ω decoupling is
`R1`–`R4`, JP_BLR is `R5`, OUT series `R6`. Both milestones re-gated **ERC 0/0, DRC 0/0/0/0**;
`/PZ` net verified = RV1.2+RV1.3+U1.2 only (nothing floating). Design BOM == A6 BOM (M1, M2,
incl. DNP). See design `SESSION_LOG.md` session 4 + `models-bom/BOM-REPORT.md` reconcile note.

## Deliverables (what & where)
- `design/shaper.kicad_sch` — schematic, milestone-parameterised by `SHAPER_MS` env
  (default M2). Regenerate: `SHAPER_MS=M1|M2 python gen_sch.py`.
- `design/shaper.kicad_pcb` — routed 4-layer board (currently M2). Pipeline:
  `gen_pcb.py` → `export_dsn.py` → freerouting jar → `import_ses.py` → `fill_zones.py`.
- `design/shaper.kicad_pro` — net classes (Default/power/signal) + DRC severities.
- `design/gen_sch.py`, `gen_pcb.py`, `export_dsn.py`, `import_ses.py`, `fill_zones.py` — scripts.
- `design/reports/erc_M1.json`, `erc_M2.json`, `drc_M1.json`, `drc_M2.json` — gate outputs.
- `design/reports/bom_M1.csv`, `bom_M2.csv` — design BOM (real MPNs) per milestone.
- `design/plots/shaper_M2_top.png` — routed M2 board render.
- `../INTERFACE.md` — the contract (ports, ranges, schematic handle, CR-210 0R-bypass DNP).

## Interface I expose / consume
- Expose: see `../INTERFACE.md` (IN = CSP-style step; OUT = shaped Gaussian; ±12 V/GND;
  schematic handle `shaper_channel`; CR-210 0R-bypass DNP options).
- Consume: A6 models-bom parts report (Round-2 generic→real swap); A2/A5 for the CR-112
  output waveform that drives my IN (sim only — does not affect the design topology).

## How to use my output
Phase-B `single-channel` instantiates the `shaper_channel` block: drive IN from the CSP
output, take OUT into the CFA output buffer; choose CR-210-populated or 0R-bypass variant.

## Open issues / asks
- **RESOLVED 2026-06-25 (coordinator reconciliation):** the 100k `R_PZ2` mis-citation has been
  acted on — the part is **removed** from design + A6 BOM (it belonged to CR-160-R7's excluded
  MAX4649-mux/gain-DIP section via net code 10, not the CR-200 P/Z). The CR-200 P/Z is the 200k
  trim `RV1` alone. Both milestones re-verified ERC 0/0, DRC 0/0/0/0; design BOM == A6 BOM.
- Real-parts gate **closed** — board carries A6's MPNs; nothing else pending from A6.
