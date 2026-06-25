# Brief — Sub-component `csp-cr112` (Phase A)

Standalone eval board for the **Cremat CR-112 charge-sensitive preamplifier**, **including
the per-channel SiPM bias front-end** (locked decision). Three parallel tracks work here:
**A1 design**, **A2 sim**, **A3 models-bom**. Read [00-CHARTER.md](../00-CHARTER.md) +
[01-CONVENTIONS.md](../01-CONVENTIONS.md) first. Work in `chips-board/csp-cr112/<aspect>/`.

## Sub-component definition (what this board is)

A single-channel CSP eval board: SiPM bias + amplify the detector's charge, expose the CSP
output for the downstream shaper, and allow bench/sim charge injection.

```
 BIAS_IN(MCX, ≤60V) ─[Rf1]─┬─[Rf2]─● FE ──● SIPM (MCX, DC to detector)
                           │              │
                          Cf             [Cc] ──► CR-112 input ──► CR-112 ──► CSP_OUT (MCX)
                           │   (0R-bypass on Rf1/Rf2)   ±12V rails w/ per-module decoupling
                          GND
 TEST_IN(MCX) ─[Ctest]─────────────────────^   (charge-injection test input)
```

- **Bias front-end** = RC+R filter (`Rf1`,`Cf`,`Rf2`) with 0R bypass jumpers; AC-coupling
  `Cc` (HV-rated) into the CR-112; `SIPM` is DC-coupled to the filtered bias node `FE`.
- **CR-112 support circuit must follow Cremat's CR-150-R5 reference** (`reference/cremat-
  CR-150-R5`): proper **per-rail supply decoupling** (≈ 4.7 Ω series + 10 µF + 0.1 µF on
  +12 V and −12 V at the module) and any recommended input protection. This is the part the
  earlier rapid build omitted — do not skip it.
- **I/O / stackup:** MCX `CONMCX013` for `BIAS_IN`/`SIPM`/`CSP_OUT`/`TEST_IN`; 3-pos screw
  terminal for ±12 V/GND; **4-layer** (GND plane + power plane).

## INTERFACE this sub-component exposes (Design owns `csp-cr112/INTERFACE.md`)
- `CSP_OUT`: voltage; step `≈ Q_in × 13 mV/pC` + CR-112 decay tail; this is the **shaper's
  input** in Phase B.
- `BIAS_IN` (≤60 V), `SIPM` (to detector), `TEST_IN` (charge inject), `+12V/-12V/GND`.
- Schematic handle: the `csp_channel` hierarchical sheet (pin names listed in INTERFACE.md).

---

## A1 — Design
**Do:** schematic (generic parts: "10 kΩ", "100 nF 100 V", a generic SIP-8 for the CR-112
from `hardware/lib/cremat.kicad_sym`) using the `gen_sch.py` net-label method; then 4-layer
layout (place + FreeRouting per [docs/FREEROUTING.md](../../FREEROUTING.md)); GND + power
planes; ERC + DRC to **0/0**. Publish `INTERFACE.md`. At the **real-parts gate** (A3 done),
swap generics → chosen MPNs/footprints and re-run ERC/DRC.
**Success:** ERC 0, DRC 0 on the real-parts 4-layer board; per-rail decoupling present per
CR-150-R5; bias front-end with working 0R-bypass DNP options; `INTERFACE.md` current.
**Failure flags:** any clearance/short, missing module decoupling, undriven power pins.

## A2 — Simulation
**Do:** **download Cremat's CR-11X/CR-110 SPICE (LTspice) model + application guide** from
cremat.com (see [01-CONVENTIONS.md §5](../01-CONVENTIONS.md#5-spice--simulation-rules));
store under `sim/cremat-models/`. Build a deck that injects an ideal **0.5 pC** charge
impulse at the CR-112 input and records `CSP_OUT`. Keep a behavioral cross-check.
**Success:** `CSP_OUT` step amplitude ≈ **0.5 pC × 13 mV/pC ≈ 6.5 mV** (CR-112 gain; within
model tolerance), correct rise time and decay tail per datasheet; plots of input charge +
`CSP_OUT` saved in `sim/` and shown in the report; figures of merit tabulated and judged.
**Failure flags:** amplitude off by >~20 % from datasheet gain with no explained cause;
unstable/oscillating model; using only a hand-behavioral model when Cremat's exists.

## A3 — Models-BOM
**Do:** for every part (bias filter R/C incl. HV-rated `Cc`/`Cf` ≥100 V, decoupling R/C,
the MCX `CONMCX013`, screw terminal, the **CR-112 module** itself) find a real,
**in-stock, economical** Digi-Key part; collect symbol+footprint+3D (reuse
`hardware/lib/`, SnapEDA/Ultra-Librarian, KiCad libs); assemble the BOM with **value, MPN,
mfr, Digi-Key PN, unit cost @ qty, stock, package, datasheet + model source.**
**Success:** every line sourced + in stock; economical choices justified; models/footprints
collected (or listed for human download with links); BOM matches the design's part set.
**Failure flags:** unsourced/obsolete/out-of-stock parts; missing HV rating on `Cc`/`Cf`;
BOM disagreeing with the design schematic.

## Sub-component COMPLETE when
A1+A2+A3 each meet criteria **and** are consistent (design BOM == A3 BOM; A2 simulated the
A1 topology). Coordinator checks the gate in [02-TRACKS.md](../02-TRACKS.md) and marks it.
