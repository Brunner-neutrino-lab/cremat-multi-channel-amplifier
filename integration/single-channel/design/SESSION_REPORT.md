# Session Report — B1 chan-design

> **The summary other tracks read instead of my log.** Keep current (overwrite). A
> consumer must be able to integrate from this + `INTERFACE.md` alone.

Track: `B1 chan-design` · Aspect: `design` · Status: `COMPLETE` (real THS3491 buffer; design BOM == B3)
Last updated: `2026-06-28`

## Objective
Merge the two COMPLETE Phase-A sub-components (CSP `csp-cr112` + shaper `shaper-cr200-cr210`)
into one single-channel board and add the CFA, 50 Ω back-terminated output buffer. Produce
the reusable `channel` cell for Phase C and publish `INTERFACE.md`.

## Success / failure criteria
- ✅ ERC **0 errors / 0 warnings** (`design/reports/erc.json`).
- ✅ DRC **0 errors / 0 warnings / 0 unconnected** (`design/reports/drc.json`), fully autorouted
  (FreeRouting 2.2.4, score 996.0). **`--schematic-parity` = 0 issues** too.
- ✅ Two Phase-A **active** blocks reused AS-IS — module pin maps/values/DNP reproduced verbatim
  (netlist-audited). Merge joins + B3 dedups only (see Current state).
- ✅ Buffer presents **50 Ω back-terminated** `OUT_50` (CFA Av=+2, 49.9 Ω series, Zout≈50 Ω).
- ✅ Buffer = **real TI THS3491** (THS3491IDDAT, SOIC-8 PowerPAD), **Rf=Rg=976 Ω**
  (THS3491 datasheet G=+2 value, B2-validated vs TI SPICE model; Av=+2).
- ✅ **design BOM == B3 BOM** (48 refs / 19 MPNs / 0 mismatches; `design/reports/bom_reconcile.txt`).
- ✅ CR-210 polarity (B2 finding) resolved + documented in INTERFACE.
- ✅ One clean flat `channel` cell, gen-script driven, ready for Phase-C ×12.
- ✅ `INTERFACE.md` current.

## Current state
**Round 2 COMPLETE.** Real THS3491 buffer fitted (±12 V direct, no regulator), Av=+2. B3
dedups applied: CSP↔shaper internal jacks removed; the two board-edge 49.9 Ω → one at OUT_50;
the two 100 µF bulk pairs → one Nichicon UWT SMD pair; terminal = Phoenix 1715734. The CR-200
and CR-210 active signal function and the CSP front-end are byte-faithful to Phase A. ERC/DRC
green; design BOM identical to B3.

## Deliverables (what & where)
- `design/channel.kicad_sch` — the **`channel`** schematic (48 symbols), the Phase-C unit.
- `design/channel.kicad_pcb` — routed 4-layer board (207 tracks, 52 vias), DRC 0/0/0.
- `design/lib/cremat.kicad_sym` — project lib (+ the `THS3491xDDA` symbol added this round).
- `design/gen_sch.py`, `gen_pcb.py`, `export_dsn.py`, `import_ses.py`, `fill_zones.py` — pipeline.
- `design/channel.kicad_pro` — net classes (hv_bias/power/signal/Default) + DRC severities.
- `design/reports/erc.json` (0/0), `drc.json` (0/0/0), `drc_parity.json` (0), `routed-top.png`,
  `bom_reconcile.txt` (design == B3 proof).
- `../INTERFACE.md` — the contract (I own it).

## Interface I expose / consume
- **Expose:** see `../INTERFACE.md`. Ports `BIAS_IN`(≤60 V MCX), `SIPM`(MCX, HV), `TEST_IN`(MCX),
  `OUT_50`(MCX, **Zout 50 Ω**, +67.1 mV/0.5 pC into 50 Ω), `+12V/GND/−12V`(screw). Schematic
  handle = `channel` sheet. **Detector charge-sign constraint** for CR-210 polarity (see below).
- **Consume:** `chips-board/{csp-cr112,shaper-cr200-cr210}/INTERFACE.md` (both COMPLETE);
  B3 `models-bom/single-channel-bom.csv` (real parts); B2 `sim/` (FoM + polarity finding);
  TI THS3491 datasheet (pinout + REF/PD).

## How to use my output
**Phase C (C1):** instantiate the `channel` sheet/topology ×12 (replicate the per-channel
net-label block, suffix per-channel nets `_chN`, share the ±12 V rails) — same method as
`hardware/gen_sch.py`. Per channel: 4 MCX (BIAS/SIPM/TEST/OUT_50) + shared screw terminal.

## CR-210 polarity (resolved)
The real CR-112 is inverting → the shaped pulse at the CR-210 is the CR-112 output sign; the
CR-210 restores only a **positive** pulse. **Resolution = detector charge-sign constraint**
(CR-11X polarity is set by detector current direction; no hardware inverter, proven blocks +
non-inverting THS3491 unchanged). Wire the SiPM so the CR-112/CR-200 output is **positive**
into the CR-210. B2 verified the corrected polarity (train baseline −1.2 % of peak). Full
detail + the constraint box in `INTERFACE.md`.

## Open issues / asks
- None blocking. Phase C may shrink the per-channel outline (164×90 mm here is the standalone
  cell; the topology is what's reused).
- 3D-only: `CONMCX013.step` absent from `lib/cremat.pretty` (carried from Phase A) — layout/DRC
  unaffected; THS3491 SOIC-8 + passives use KiCad stock 3D.
- If the buffer gain is ever changed, update Rf/Rg (one PARTS line in gen_sch.py) + re-sim (B2).
