# INTERFACE — `csp-cr112` (CR-112 CSP eval board + SiPM bias front-end)

> Owned by **A1 csp-design**. The contract downstream tracks integrate against without
> reading internals. Phase B (single-channel) consumes `CSP_OUT` as the shaper input.
> Status: **REAL-PARTS board (A3 gate passed), ERC 0/0 · DRC 0/0/0, fully autorouted.**
> Every value/footprint = A3's chosen Digi-Key/Cremat part (see "Real parts (BOM)" below).

## What this board is
A single-channel charge-sensitive-preamplifier eval board: a SiPM bias front-end feeds a
Cremat **CR-112** CSP whose output is exposed for the downstream shaper, plus a charge-
injection test input for bench/sim. Signal chain:

```
BIAS_IN(MCX,<=60V) --Rf1--+--Rf2--*FE --- SIPM (MCX, DC to detector)
                          |               |
                         Cf(HV)          Cc(HV) --> CR-112 in --> CR-112 --> CSP_OUT (MCX)
                          |        (0R bypass on Rf1 and Rf2)
                         GND
TEST_IN(MCX) --Rtest--Ctest--^   (charge-injection)        +-12V via 4.7R+10uF+0.1uF/rail
```

## Electrical I/O

| Port | Dir | Connector | Signal | Range / notes |
|------|-----|-----------|--------|---------------|
| `BIAS_IN` | in | MCX (J1) | SiPM bias DC | **≤ 60 V** (HV net; `hv_bias` class, 0.6 mm clear). Through RC+R filter to `FE`. |
| `SIPM`    | i/o | MCX (J2) | detector bias + charge | DC-coupled to filtered bias node `FE`; carries HV. Detector connects here. |
| `TEST_IN` | in | MCX (J3) | test pulse | Charge inject via 47 Ω + 1 pF → CSP input. A V step of `Vt` injects `Q = 1 pF × Vt`. |
| `CSP_OUT` | out | MCX (J4) | voltage step | **≈ Q_in × 13 mV/pC** + CR-112 decay tail (τ ≈ 50–100 µs, CR-112 datasheet). This is the **shaper input** in Phase B. Low-Z (CR-112 output). |
| `+12V` / `GND` / `-12V` | pwr | 3-pos screw terminal (J5) | supply | ±12 V nominal (CR-11X range ±6…±15 V). On-board per-rail decoupling. |

Net names (for netlist-level integration): `BIAS_IN`, `FE`, `SIPM` shield→`GND`,
`TEST_IN`, `CSP_IN` (internal), `CSP_OUT`, `+VDC`, `-VDC`, `GND`, plus the filtered module
rails `+VS_F` / `-VS_F` (after the 4.7 Ω series R; internal).

## Schematic handle
- Schematic: `design/csp-cr112.kicad_sch` (flat, single sheet — not yet a hierarchical
  sub-sheet). The instantiable block for Phase B is the **whole sheet**; the symbol that
  matters at the boundary is **U1 = `cremat:CR-11X` (value CR-112)**, SIP-8:
  - pin 1 = input (`CSP_IN`), pins 2/4/7 = GND, pin 3 = NC, pin 5 = −Vs, pin 6 = +Vs,
    pin 8 = output (`CSP_OUT`).
- For Phase-B merge: take the front-end + CR-112 + decoupling sub-circuit; drop the
  standalone power entry (J5) and the standalone output jack (J4) since the channel merges
  CSP_OUT directly into the shaper input on one board.

## Mechanical / stackup
- **4-layer:** F.Cu / In1=GND plane / In2=PWR plane (−VDC) / B.Cu. Matches the final board.
- Board outline 90 × 72 mm, 4× M3 mounting holes.
- I/O: 4× MCX `CONMCX013` edge jacks (`lib/cremat.pretty`), 1× Phoenix MKDS 3-pos screw
  terminal. (MCX `Edge.Cuts` cutouts are parked on `Dwgs.User` for routing; restore them on
  `Edge.Cuts` when the jacks are placed at the true board edge in the GUI.)
- Net classes: `hv_bias` (0.6 mm clearance, 0.4 mm track) on `BIAS_IN`/`SIPM`/`FE`;
  `power` (0.5 mm) on rails; `signal` (0.33 mm) on CSP nets; `Default` 0.2 mm.

## DNP / optional blocks (populate-or-bypass)
- **Bias filter Rf1 (R1) / Rf2 (R3)** populated by default; **0R bypass JP_Rf1 (R2) / JP_Rf2 (R4)
  are DNP**. To bypass the filter: fit the 0R, remove the corresponding filter R. Exactly one
  path of each pair is populated. (BOM `DNP` column is the single source of truth.)

## Part list pointer
- **Real-parts BOM:** `design/reports/bom.csv` (this board, real MPN + Manufacturer per ref).
- Sourcing / Digi-Key PNs / prices / alternates: A3 report `../models-bom/PARTS_REPORT.md`
  + `../models-bom/csp-cr112-bom.csv`.

## Verified-by
- ERC `design/reports/erc.json` = **0/0**; DRC `design/reports/drc.json` = **0/0/0**
  (errors/warnings/unconnected), fully autorouted (FreeRouting 2.2.4, score 996.77).
- Function (gain/rise/decay): see A2 sim report `../sim/SESSION_REPORT.md`.
  Expected `CSP_OUT` step for 0.5 pC ≈ 6.5 mV (0.5 pC × 13 mV/pC).

## Real parts (BOM) — A3 gate resolved
All values/footprints below are A3's chosen real parts (swapped in 1:1, ERC+DRC re-run clean).
Footprints are **identical to the generic board** (0805 / SIP-8 / MCX / Phoenix) **except** the
two rail-entry bulk caps, which moved from generic 10 µF/1206 to A3's **100 µF/25 V radial
electrolytic** (`Capacitor_THT:CP_Radial_D6.3mm_P2.50mm`); the board was re-placed + re-routed
for those THT parts. The 10 µF rail-bulk caps (C4/C6) also moved 1206→0805 per A3's 0805 policy.

| Ref | Value | MPN | Mfr | Footprint | DNP |
|---|---|---|---|---|---|
| Cf (C1) | 100 nF 100 V X7R | CL21B104KCC5PNC | Samsung | C_0805 | — |
| Cc (C2) | 0.22 µF 100 V X7R | GRM21AR72A224KAC5K | Murata | C_0805 | — |
| C_test (C3) | 1 pF C0G | CC0805CRNPO9BN1R0 | Yageo | C_0805 | — |
| Cp1/Cn1 (C4/C6) | 10 µF 25 V | CL21A106KAYNNNE | Samsung | C_0805 | — |
| Cp2/Cn2 (C5/C7) | 0.1 µF 50 V | CL21B104KBCNNNC | Samsung | C_0805 | — |
| Cb_p/Cb_n (C8/C9) | 100 µF 25 V | UVR1E101MED | Nichicon | CP_Radial_D6.3mm_P2.50mm | — |
| J1–J4 (MCX) | MCX edge 50 Ω | CONMCX013 | TE/Linx | cremat:MCX_CONMCX013_EdgeMount | — |
| J5 (PWR) | screw term 3-pos | 1715035 (MKDS 1,5/3) | Phoenix | TerminalBlock_Phoenix_MKDS-1,5-3 | — |
| Rf1/Rf2 (R1/R3) | 10 kΩ 1% | RC0805FR-0710KL | Yageo | R_0805 | — |
| JP_Rf1/JP_Rf2 (R2/R4) | 0 Ω | RC0805JR-070RL | Yageo | R_0805 | **DNP** |
| R_test (R5) | 47 Ω 5% | RC0805JR-0747RL | Yageo | R_0805 | — |
| R_dvp/R_dvn (R6/R7) | 4.7 Ω 5% | RC0805JR-074R7L | Yageo | R_0805 | — |
| U1 (CR-112) | CR-112 | CR-112-R2.1 | Cremat | SIP-8 PinHeader_1x08_P2.54mm | — |

**CR-112 lead spec confirmed:** Cremat's own CR-150-R5 board lays the CR-11X module
(`8pinSIP`) as 8 inline THT pads at **2.54 mm pitch** (x = 0…17.78), drill 0.762 mm — so the
generic `PinHeader_1x08_P2.54mm_Vertical` (2.54 mm pitch) is the correct real footprint.

**One BOM reconciliation for A3/coordinator:** the design's test-injection path is **47 Ω +
1 pF** (R5 + C3, per CR-150-R5). A3's BOM lists `Ctest` (1 pF) but **omits the 47 Ω series
resistor**. A1 used a real part from A3's own Yageo RC0805 family — **R5 = Yageo
RC0805JR-0747RL (47 Ω 0805)** — so the design BOM is fully real. A3 should add this one row so
Models-BOM == Design BOM. All other 12 A3 MPNs match the design 1:1.

**3D note (non-blocking):** `CONMCX013.step` is missing from `lib/cremat.pretty/`; the MCX
footprint's pads/courtyard are complete so layout/DRC is unaffected (3D viewer shows a
placeholder). Restore by dropping the TE/Linx STEP into the pretty lib.
