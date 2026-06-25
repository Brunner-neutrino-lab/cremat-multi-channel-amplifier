# Brief — `single-channel` integration (Phase B)

Combine the two proven sub-components into **one complete channel** and add the **output
buffer**. Tracks: **B1 design**, **B2 sim**, **B3 models-bom**. **Gate:** both
`csp-cr112` and `shaper-cr200-cr210` must be **COMPLETE** before starting. Read
[00-CHARTER.md](../00-CHARTER.md) + [01-CONVENTIONS.md](../01-CONVENTIONS.md) and **both
sub-component `INTERFACE.md` + reports** first. Work in `integration/single-channel/<aspect>/`.

## What this phase is

Mostly **merge + prove the merger still works**, then append the buffer:

```
 BIAS_IN/SIPM ─► [csp-cr112] ─CSP_OUT─► [shaper-cr200-cr210] ─OUT─► [BUFFER] ─► OUT_50 (MCX)
   (from A interfaces, unchanged)                                   CFA, 50Ω back-terminated
```

- **Reuse the sub-component sheets/interfaces as-is** — connect `csp-cr112.CSP_OUT` →
  `shaper-cr200-cr210.IN`. Don't redesign the proven blocks; integrate them.
- **Output buffer (locked):** current-feedback amp, **EL5167-class**, **50 Ω
  back-terminated** output (`OUT_50`). Drives a 50 Ω DAQ/scope. Take its application circuit
  from the x6-board reference and the op-amp datasheet (gain, feedback, decoupling).
- **I/O / stackup:** MCX `CONMCX013`, ±12 V screw terminal, **4-layer**. This board is the
  **single-channel cell that Phase C instantiates ×12**, so keep the sheet cleanly
  hierarchical.

## INTERFACE exposed (`single-channel/INTERFACE.md`)
- `OUT_50`: shaped pulse, **Zout = 50 Ω**, into a 50 Ω load. Plus `BIAS_IN`, `SIPM`,
  `+12V/-12V/GND`. Schematic handle: the `channel` hierarchical sheet (the Phase-C unit).

---

## B1 — Design
**Do:** instantiate the CSP and shaper/CR-210 sheets, wire `CSP_OUT→IN`; add the CFA output
buffer stage (gain + 49.9 Ω series for 50 Ω Zout + its decoupling); single-channel 4-layer
board; ERC + DRC **0/0**. Publish `INTERFACE.md` + the reusable `channel` sheet.
**Success:** ERC 0 / DRC 0; buffer presents 50 Ω back-terminated output; the two sub-blocks
are unchanged from their COMPLETE state; `channel` sheet is clean for ×12 reuse.
**Failure:** redesigning/altering the proven blocks; Zout ≠ 50 Ω; clearance/short.

## B2 — Simulation
**Do:** chain the **Cremat CR-112 + CR-200 + CR-210 models** + the **buffer op-amp SPICE
model** (from the op-amp vendor); inject **0.5 pC** at the CSP input; load `OUT_50` with
50 Ω. Plot the response at **every stage** (CSP, shaper, BLR, buffer/`OUT_50`).
**Success:** end-to-end response is sane and consistent with the sub-component sims (gains
compound correctly; peaking time preserved; `OUT_50` amplitude into 50 Ω as expected; no
instability); plots + figures-of-merit table in the report; explicitly state the expected
`OUT_50` peak for 0.5 pC and confirm it. **Failure:** the merged response contradicts the
standalone sims without explanation; output can't drive 50 Ω; oscillation.

## B3 — Models-BOM
**Do:** **merge** the two sub-component BOMs (dedupe shared jellybeans) and **add the buffer
parts** (the CFA op-amp + feedback/gain R's + 49.9 Ω + decoupling), all real/in-stock/
economical Digi-Key with the full fields. Collect the op-amp symbol/footprint/3D.
**Success:** one consolidated single-channel BOM, every line sourced/in-stock, == B1
design; buffer op-amp chosen with justification (CFA, adequate bandwidth/drive for 50 Ω).
**Failure:** unsourced parts; BOM ≠ design; buffer op-amp inadequate for 50 Ω drive.

## COMPLETE when
B1+B2+B3 meet criteria and are consistent; the `channel` sheet + `INTERFACE.md` are ready
for Phase C. Coordinator marks `single-channel` COMPLETE in [02-TRACKS.md](../02-TRACKS.md).
