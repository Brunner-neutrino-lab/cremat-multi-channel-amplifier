# Brief — Sub-component `shaper-cr200-cr210` (Phase A)

Standalone eval board for the **Cremat CR-200-1µs Gaussian shaper**, then **sequentially
integrate the CR-210 baseline restorer**. Tracks: **A4 design**, **A5 sim**, **A6
models-bom**. Two milestones in every track: **M1 = CR-200 only**, **M2 = + CR-210**. Read
[00-CHARTER.md](../00-CHARTER.md) + [01-CONVENTIONS.md](../01-CONVENTIONS.md) first. Work in
`chips-board/shaper-cr200-cr210/<aspect>/`.

## Sub-component definition

```
 M1:  IN(MCX) ──► CR-200 (1µs) ──► OUT(MCX)        + P/Z network, per-rail decoupling
 M2:  IN(MCX) ──► CR-200 ──┬─► CR-210 (BLR) ─┬─► OUT(MCX)
                           └──── JP_BLR 0R ───┘   (populate-XOR bypass, per CR-160-R7 JU1)
```

- **`IN` is the CSP output** (a charge-amp step/tail), **not** raw charge — this board has
  no CSP. The Sim track drives it with the CR-112 model's output for a 0.5 pC event.
- **Follow Cremat's CR-160-R7 reference** (`reference/cremat-CR-160-R7`) for the support
  circuit: the **pole-zero network** around the CR-200 (datasheet R/C, e.g. the eval board's
  R7 200k / R25 100k region), **per-rail supply decoupling** (4.7 Ω + 10 µF + 0.1 µF +
  bulk), and the **CR-210 + bypass-jumper** wiring (the eval board's `U5` + `JU1`).
- **CR-210 pinout** (confirmed): `1=in 2=GND 3=GND 4=-Vs 5=+Vs 6=GND 7=GND 8=out` (= CR-200
  except pin 2). Symbols in `hardware/lib/cremat.kicad_sym`.
- **I/O / stackup:** MCX `CONMCX013`, 3-pos screw terminal ±12 V/GND, **4-layer**.

## INTERFACE exposed (`shaper-cr200-cr210/INTERFACE.md`)
- `IN`: voltage (accepts a CR-112-style step). `OUT`: shaped Gaussian pulse (post-BLR or
  post-bypass). `+12V/-12V/GND`. Schematic handle: `shaper_channel` sheet.

---

## A4 — Design
**M1:** schematic (generic parts) of CR-200 + its P/Z network + per-rail decoupling →
4-layer layout → ERC/DRC 0. **M2:** insert CR-210 with the `JP_BLR` 0R bypass between shaper
output and `OUT`; re-run ERC/DRC 0; update `INTERFACE.md`. Real-parts gate from A6.
**Success (per milestone):** ERC 0 / DRC 0; P/Z network + decoupling present per CR-160-R7;
M2 shows correct populate-XOR (module XOR 0R). **Failure:** missing P/Z or decoupling;
both module and its bypass populated; clearance/short.

## A5 — Simulation
**Do:** **download Cremat's CR-200 (and, for M2, CR-210) LTspice models + app guides** from
cremat.com (§5 of conventions); store under `sim/cremat-models/`. Stimulus = the **CR-112
model output for a 0.5 pC event** (coordinate the waveform with A2, or regenerate it from
the CR-112 model). **M1:** show the shaped Gaussian at `OUT` — report **peaking time ≈
shaping time (1 µs region per datasheet)**, peak amplitude, undershoot. **M2:** show the
CR-210 effect — baseline restoration vs. the un-restored case (e.g. a pulse train showing
baseline droop removed). Plots saved in `sim/`.
**Success:** M1 Gaussian peaking time/gain match the CR-200 datasheet within model tol; M2
demonstrably restores baseline; figures of merit tabulated + judged. **Failure:** wrong
peaking time/shape; no demonstrable BLR effect; ignoring Cremat's model.

## A6 — Models-BOM
**Do:** real, in-stock, economical Digi-Key parts for P/Z network R/C, decoupling, MCX,
screw terminal, the **CR-200-1µs** module, and (M2) the **CR-210** module; collect
symbol/footprint/3D; BOM with value/MPN/mfr/DK-PN/cost/stock/package/links. M1 then M2 adds
CR-210 parts. **Success:** all sourced/in-stock; BOM == design; economical justified.
**Failure:** unsourced/obsolete; BOM ≠ design.

## Sub-component COMPLETE when
**M2** is reached in all three tracks and they're consistent (Coordinator gate in
[02-TRACKS.md](../02-TRACKS.md)). The CR-200-only M1 is an internal milestone, not the end.
