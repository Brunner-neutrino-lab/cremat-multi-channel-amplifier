# Fabrication and Assembly Guide

How to generate fab outputs, order the board, and assemble it — including the
**optional-population (DNP) variants** that are the defining feature of this design.

This board is a **single PCB** (12 channels on one board), unlike the multi-board
reference systems. Quantities below are per board.

---

## Generating fabrication files

Use the KiCad pipeline established by `ets-breakout` (KiCad 9/10 CLI + bundled Python):

1. **Open** `hardware/multi-channel-cremat-amplifier.kicad_pro` (once the hardware track
   has created it).
2. **DRC gate:** `kicad-cli pcb drc <pcb>` → must be **0 errors** (clearance, creepage,
   etc. — see [../hardware/pcb-design-rules.md](../hardware/pcb-design-rules.md)).
3. **Fill zones** as a *separate* pass on the saved file (headless in-memory zone fill
   segfaults — a documented gotcha in both reference projects).
4. **Export** gerbers + Excellon drill + placement CSV, and generate the BOM CSV:
   ```
   kicad-cli pcb export gerbers <pcb> -o pcbfab/gerber/
   kicad-cli pcb export drill   <pcb> -o pcbfab/drill/
   kicad-cli pcb export pos     <pcb> -o assembly/positions.csv --format csv --units mm
   #  + project BOM export (with MPN/VPN and DNP column)
   ```
5. A KiCad **job set** (`fab-files.kicad_jobset`) is the recommended way to automate 2–4,
   as the reference projects do.

> `pcbfab/`, `assembly/`, and `**/fab/` are git-ignored — **regenerate from source before
> every order**.

---

## PCB specifications (request from fab)

| Parameter | Value |
|---|---|
| Layers | 4 (preferred; 2 acceptable with a ground plane) |
| Material | FR4 (1 oz outer copper) |
| Thickness | 1.6 mm |
| Min track / clearance | per net class; **HV bias clearance set by bias voltage** |
| Surface finish | ENIG (recommended for fine-pitch + low-leakage front-end) |
| Solder mask / silk | both sides |
| Controlled impedance | only if `OUT` is run as 50 Ω — then declare it |

For low-current / low-noise front-ends, the reference docs suggest a low-absorption
substrate; FR4 with ENIG is the practical default here.

---

## Assembly — choose the build variant first

Decide the configuration **before** assembly; it sets the DNP list
([../hardware/bom.md](../hardware/bom.md)):

| Build | Bias filter | CR-210 |
|---|---|---|
| Full | fitted | fitted |
| No-BLR | fitted | bypassed |
| External-bias | bypassed | either |
| Reference-equivalent | bypassed | bypassed |

### The one assembly invariant
For each optional block, populate **either** the block **or** its 0R bypass — **never
both**:

- Bias filter: `Rf1`,`Rf2`,`Cf` **xor** `JP_Rf1`,`JP_Rf2`
- CR-210: `U_BLR` **xor** `JP_BLR`

Populating both shorts out / parallels the block. Check this per channel after placement.

### Order of assembly
1. **SMD first** (reflow / stencil): 0805 R/C, 0R jumpers, op-amps. Apply the DNP list so
   the wrong path isn't placed.
2. **Trimpots, then Cremat SIP-8 modules** (CR-11X, CR-200-X, and CR-210 if fitted) —
   through-hole, hand-soldered; observe **pin-1** (white dot on Cremat modules).
3. **Coax jacks and connectors** last (align to board edge).

### HV / SiPM cautions during bring-up
- The `BIAS_IN`, filter, front-end, and `SIPM` nets reach the **full bias voltage**.
  Ramp bias from 0 V; never hot-plug detectors.
- `Cc` (and `Cf`) must be the **voltage-rated** parts from the BOM — verify before
  powering.

---

## Post-assembly checks

1. **Continuity / isolation:** `+VDC`–`GND`, `-VDC`–`GND`, and `BIAS_IN`–`GND` not shorted.
2. **Jumper audit:** confirm exactly one path populated for every optional block, all 12
   channels.
3. **Power-only bring-up:** apply ±Vs (no bias, no detector); confirm module quiescent
   currents are sane and outputs sit near baseline.
4. **Bias bring-up:** with a detector or a test pulse, ramp `BIAS_IN`; verify the
   front-end node biases and a pulse appears at `OUT`.
5. **Per-channel functional test:** inject charge (test-pulse cap into the CSP input) and
   confirm shaped pulses on all 12 `OUT` jacks; trim P/Z and gain per channel.

---

## Storage / handling

- SiPMs and the analog front-end are ESD-sensitive — grounded strap + mat.
- Store assembled boards in anti-static bags; keep away from the HV supply when not in
  controlled use.
