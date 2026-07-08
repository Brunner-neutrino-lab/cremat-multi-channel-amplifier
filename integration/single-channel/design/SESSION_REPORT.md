# Session Report — B1 chan-design

> **The summary other tracks read instead of my log.** Keep current (overwrite). A
> consumer must be able to integrate from this + `INTERFACE.md` alone.

Track: `B1 chan-design` · Aspect: `design` · Status: `SCHEMATIC UPDATED (2026-07 rework)` — ERC 0/0; PCB rebuild pending
Last updated: `2026-07-08`

## Objective
Merge the two COMPLETE Phase-A sub-components (CSP `csp-cr112` + shaper `shaper-cr200-cr210`)
into one single-channel board and add the CFA, 50 Ω back-terminated output buffer. Produce
the reusable `channel` cell for Phase C and publish `INTERFACE.md`.

## Success / failure criteria
- ✅ ERC **0 errors / 0 warnings** (`kicad-cli sch erc channel.kicad_sch`, re-run after the rework).
- ⚠ **DRC / autoroute STALE** — `channel.kicad_pcb` predates the 2026-07 rework (buffer bypass,
  rail protection, dropped HF caps, reworked test input). Rebuild + re-DRC pending (deferred
  until schematic/BOM/docs wrapped).
- ✅ Active Phase-A modules (CR-112/CR-200/CR-210) reused AS-IS — pin maps/values verbatim.
- ✅ Output buffer = real TI THS3491 (Av=+2, Rf=Rg=976 Ω, 49.9 Ω back-term), now a
  **populate-or-bypass** block, DNP by default (`JP_BUF` 0 Ω fitted; XOR).
- ✅ Rail **reverse-polarity protection** per rail (PTC + series Schottky). No over-voltage
  clamp — not passively achievable at ±12 V nominal vs the ±13 V Cremat abs-max (documented).
- ✅ design BOM ↔ `single-channel-bom.csv`: **45 refs / 20 MPNs**.
- ✅ CR-210 polarity (B2 finding) resolved + documented in INTERFACE.
- ✅ `INTERFACE.md` reconciled to the reworked design (2026-07).

## Current state
**2026-07 rework applied + verified (schematic).** On top of the Round-2 THS3491 channel:
(1) the output buffer is now **DNP-by-default** with a `JP_BUF` 0 Ω bypass (XOR) — default
build = CR-210 drives the 49.9 Ω back-term directly (OUT_50 = ½·SHAPER_OUT into 50 Ω);
(2) **rail reverse-polarity protection** per rail (screw terminal → PTC `F1/F2` → series
Schottky `D1/D2` → rail; no over-voltage clamp); (3) test input reworked to a coax-terminated
injector (`R5` = 47 Ω shunt to GND, `C3` = 1 pF into `CSP_IN`; net `TEST_N` gone);
(4) 0.1 µF HF decoupling dropped board-wide (per-rail = 4.7 Ω + 10 µF); (5) `channel.kicad_sch`
redrawn as a human-review **WIRED** layout; (6) 2026-07 sourcing folded in (Cf →
CL21B104KCFNNNE, Digi-Key PN fixes). **Schematic ERC 0/0; PCB not yet rebuilt against the new
netlist.**

## Deliverables (what & where)
- `design/channel.kicad_sch` — the **`channel`** schematic (**45 symbols**; wired review layout).
- `design/channel.pdf` — current schematic render.
- `design/channel.kicad_pcb` — routed 4-layer board **(STALE — predates the 2026-07 rework)**.
- `design/lib/cremat.kicad_sym` — project lib (`THS3491xDDA` symbol).
- `design/gen_sch.py`, `gen_pcb.py`, `export_dsn.py`, `import_ses.py`, `fill_zones.py` — pipeline.
- `design/channel.kicad_pro` — net classes (hv_bias/power/signal/Default) + DRC severities.
- `design/reports/*` — **ERC current; DRC/parity/routed-top are STALE** (pre-rework).
- `../INTERFACE.md` — the contract (reconciled 2026-07).

## Interface I expose / consume
- **Expose:** see `../INTERFACE.md`. Ports `BIAS_IN`(≤60 V MCX), `SIPM`(MCX, HV), `TEST_IN`(MCX),
  `OUT_50`(MCX, **Zout 50 Ω**; buffer-populated ≈ +67.1 mV/0.5 pC, default bypass ≈ +33.5 mV),
  `+12V/GND/−12V`(screw, reverse-polarity protected). Schematic handle = `channel` sheet.
  **Detector charge-sign constraint** for CR-210 polarity (see below).
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
- **PCB rebuild pending (blocking for fab, not for design).** `channel.kicad_pcb` must be
  regenerated against the new netlist (`F1/F2/D1/D2`, `+VDC_F/−VDC_F`, `JP_BUF`, dropped
  0.1 µF caps) then re-DRC'd. Deferred by request until schematic/BOM/docs are wrapped.
- **Over-voltage protection is not passively achievable** at ±12 V nominal vs the ±13 V Cremat
  supply abs-max — the rail protection is reverse-polarity + fault-interrupt only. Keep the
  bench supply set correctly. (Verified vs datasheets; in INTERFACE + gen_sch docstring.)
- **Sourcing:** 10 µF 25 V bulk (CL21A106KAYNNNE) is Active but 0-stock (16-wk lead) — Taiyo
  Yuden `TMK212BBJ106KG-T` is the in-stock equal-spec alt; decide keep-and-reorder vs sub.
- 3D-only: `CONMCX013.step` absent from `lib/cremat.pretty` — layout-unaffected.
- Buffer gain change → update Rf/Rg (one PARTS line in gen_sch.py) + re-sim (B2).
- Default build has **no active line driver** (buffer DNP): the CR-210 drives the 50 Ω
  back-term directly and OUT_50 is halved. Populate the THS3491 block for the ×1 line-driver.
