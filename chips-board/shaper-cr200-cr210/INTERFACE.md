# INTERFACE — `shaper-cr200-cr210`

> Owned by **A4 shaper-design**. The contract a consumer integrates against without reading
> internals. Status: **M2 reached, real parts fitted** (CR-200 + CR-210 BLR + 0R bypass).
> ERC 0/0 and DRC 0/0/0 for both milestones. All parts are A6's chosen real MPNs (no generics).

This sub-component is the **Cremat CR-200-1µs Gaussian shaper** followed by an **optional
CR-210 baseline restorer (BLR)**. It has no CSP on board — its **input is a CSP-style
step/tail** (the CR-112 output), and its **output is the shaped (and baseline-restored)
Gaussian pulse** that feeds the Phase-B output buffer.

```
 IN(MCX) ──► CR-200 (1µs) ──┬─► CR-210 (BLR) ─┬─► 49.9Ω ─► OUT(MCX)
            + P/Z trim       └──── JP_BLR 0R ──┘
            + per-rail decoup   (populate-XOR: CR-210 ⊕ JP_BLR)
```

## Electrical I/O (ports)

| Port | Dir | Connector | Signal | Expected range |
|------|-----|-----------|--------|----------------|
| `IN`  | in  | MCX `CONMCX013` (J1) | CSP output: fast step + long tail (unipolar) | ~0–0.7 V step for a 0.5 pC event through a CR-112 CSP; AC-coupled into the CR-200 internally by the module. **Confirm amplitude with A2/A5 CR-112 model output.** |
| `OUT` | out | MCX `CONMCX013` (J2) | Gaussian shaped pulse (post-BLR or post-bypass) | unipolar quasi-Gaussian; peaking time ≈ 1 µs (CR-200-1µs); amplitude = CR-200 gain × input step (≈ a few × the input). Series 49.9 Ω at OUT (not a full 50 Ω back-term — see notes). **Pin down peak/undershoot with A5 sim.** |
| `+12V` | pwr | screw terminal (J3 pin 1) | +12 V supply | +12 V (module abs-max ±15 V; runs ±12 V) |
| `GND`  | pwr | screw terminal (J3 pin 2) | ground | 0 V |
| `-12V` | pwr | screw terminal (J3 pin 3) | −12 V supply | −12 V |

Each module supply pin is fed through a **4.7 Ω series + 10 µF bulk + 0.1 µF HF** per-rail
filter (per CR-160-R7). GND and −VDC are internal plane layers (In1, In2).

## Schematic handle
- Sheet/handle to instantiate downstream: **`shaper_channel`** (this design's `shaper.kicad_sch`
  is the single-instance realisation; Phase-B re-instantiates the same topology).
- Module symbols: `cremat:CR-200`, `cremat:CR-210` (SIP-8, `hardware/lib/cremat.kicad_sym`).
- Key refs in this board (M2): `U1`=CR-200 (CR-200-1us-R2.1), `U2`=CR-210 (CR-210-R0),
  `RV1`=200k P/Z trim (Bourns 3296W-1-204LF) — **the sole CR-200 pole-zero element**,
  `R1`–`R4`=4.7 Ω per-rail decoupling, `R5`=0R BLR-bypass jumper (JP_BLR, DNP by default),
  `R6`=49.9 Ω OUT series, `C9`/`C10`=100 µF rail bulk, `J1`=IN MCX, `J2`=OUT MCX, `J3`=power.
  (M1 drops the CR-210 + its decoupling + the 0R jumper; refs renumber to 14 fitted parts.)

## CR-210 baseline-restorer option (the 0R-bypass DNP) — populate-XOR

Confirmed to match **Cremat CR-160-R7 `JU1`**: the bypass jumper bridges the **CR-200 output
node (= CR-210 input)** and the **CR-210 output node**, so closing it shorts across the BLR.

| Variant | Populate | DNP | Net behaviour |
|---------|----------|-----|---------------|
| **BLR active** (default) | `U2` CR-210 (CR-210-R0) | `R5` (JP_BLR 0R) = **DNP** | `SH_OUT → CR-210 → BLR_OUT → OUT` |
| **BLR bypassed** | `R5` (JP_BLR 0R) | `U2` CR-210 = **DNP** | `SH_OUT → 0R → BLR_OUT → OUT` (CR-210 omitted) |

- `JP_BLR` (`R5`): pin1 = `SH_OUT` (CR-200 out / CR-210 in), pin2 = `BLR_OUT` (CR-210 out).
- **Exactly one path populated** — never both (would short the CR-210 output to its input).
- As shipped in the design: `U2` fitted (DNP=False), `R5` DNP=True — verified on schematic AND
  routed PCB. Matches A6 BOM DNP table (`U_BLR` XOR `JP_BLR`); when bypassed, the CR-210's
  dedicated decoupling (CR-210 rail caps `C5`/`C7` + series `R4`) is also DNP per A6.
- M1 (CR-200 only) is the internal milestone with no CR-210/JP_BLR at all.

## Mechanical / stackup
- **4-layer**: F.Cu (signal) / In1.Cu = **GND plane** / In2.Cu = **−VDC plane** / B.Cu (signal).
- Board outline 168 × 80 mm, 4× M3 mounting holes. (Standalone eval size; Phase-C shrinks
  per-channel — the topology, not this outline, is what's reused.)
- MCX `CONMCX013` edge-mount jacks for IN/OUT; 3-pos 5.0 mm screw terminal for power.

## Real parts fitted (A6 Models-BOM, swapped 1:1 — no generics remain)
M2 ref designators (M1 drops `U2`/`R4`/`R5`/`C5`–`C8`/`R6` and renumbers). MPNs are the
binding contract; design BOM == A6 `models-bom/shaper-bom.csv` (verified per milestone).

| Ref(s) (M2) | Value | MPN | Mfr | Footprint |
|---|---|---|---|---|
| U1 | CR-200-1us | CR-200-1us-R2.1 | Cremat | PinHeader_1x08 (SIP-8) |
| U2 | CR-210 | CR-210-R0 | Cremat | PinHeader_1x08 (SIP-8) |
| RV1 | 200k trim (sole P/Z) | 3296W-1-204LF | Bourns | Potentiometer_Bourns_3296W_Vertical |
| R1,R2,R3,R4 | 4.7 Ω (rail decoup) | RC0805JR-074R7L | Yageo | R_0805_2012Metric |
| R5 | 0 Ω (BLR bypass, **DNP**) | RC0805JR-070RL | Yageo | R_0805_2012Metric |
| R6 | 49.9 Ω (OUT series) | RC0805FR-0749R9L | Yageo | R_0805_2012Metric |
| C1,C3,C5,C7 | 10 µF (local bulk) | CL21A106KAYNNNE | Samsung | **C_0805_2012Metric** |
| C2,C4,C6,C8 | 0.1 µF (HF bypass) | CL21B104KBCNNNC | Samsung | C_0805_2012Metric |
| C9,C10 | 100 µF (rail bulk) | UWT1V101MCL1GS | Nichicon | CP_Elec_6.3x7.7 |
| J1,J2 | MCX `CONMCX013` | CONMCX013 | TE/Linx | cremat:MCX_CONMCX013_EdgeMount |
| J3 | 3-pos screw term | 1715734 | Phoenix | TerminalBlock_Phoenix_MKDS-1,5-3 5.08mm |

Notes vs the prior generic board: the **10 µF caps moved 1206→0805** (Samsung CL21 is 0805)
and **two 100 µF rail-bulk electrolytics (C9/C10)** were added to match A6's fitted lines.
No other footprint changed; the swap was otherwise metadata-only.

**Reconciliation 2026-06-25:** a 100k "P/Z fixed R" briefly added during the A6 swap has been
**removed** — the CR-200 pole-zero is the **200k trimpot `RV1` alone**. The 100k's CR-160-R7
`R9` citation was wrong (`R9` is in the excluded MAX4649-mux/gain-DIP buffer section: net code
10 → `U7` pin6 + `SW1` pin1). Refs reverted to the no-`R1`-100k numbering. Both milestones
re-verified ERC 0/0, DRC 0/0/0/0; design BOM == A6 BOM incl. DNP.

## Verified by
- ERC: `design/reports/erc_M1.json`, `erc_M2.json` — 0 errors / 0 warnings each.
- DRC: `design/reports/drc_M1.json`, `drc_M2.json` — 0 errors / 0 warnings / 0 unconnected / 0 parity.
- BOM (real parts): `design/reports/bom_M1.csv`, `bom_M2.csv` — MPNs identical to A6
  `models-bom/shaper-bom.csv` for both milestones (incl. the CR-210 vs JP_BLR DNP).
- Simulation figures of merit: **A5 shaper-sim** report (peaking time ≈ 1 µs, BLR effect).

## How Phase-B consumes this
Phase-B `single-channel` (B1) instantiates the `shaper_channel` topology: drive `IN` from
the CR-112 CSP output, take `OUT` into the CFA (EL5167-class) output buffer. Pick the
CR-210-active or 0R-bypass variant via the DNP table above. Supply ±12 V/GND shared with
the rest of the channel.
