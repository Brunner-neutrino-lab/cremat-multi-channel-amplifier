# Fielded BOM — Multi-channel Cremat Amplifier (Track 1 deliverable)

Per-channel parts ×12 + shared parts, for the **Full build variant** (bias filter fitted +
CR-210 fitted; all `JP_*` 0R bypasses DNP). Policy/rationale is in
[../../docs/hardware/bom.md](../../docs/hardware/bom.md); designed values are in
[../../docs/hardware/circuit-design.md](../../docs/hardware/circuit-design.md).

> The front-end, modules, output termination, optional jumpers, trimpots, and connectors
> below are fixed. The CR-200→buffer **support passives + per-rail decoupling** carry over
> from the reference channel (`reference/cremat-x6-board/channel.kicad_sch`) and are
> finalized when Track 5 captures the schematic and exports the authoritative netlist BOM.

## Per-channel (×12)

| Ref (per ch) | Value | Footprint (KiCad lib) | MPN / source | Qty/ch | Qty×12 | Populate (Full) |
|---|---|---|---|---|---|---|
| `U_CSP` | Cremat **CR-112** | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` (SIP-8) | Cremat CR-112 | 1 | 12 | ● |
| `U_SHAPER` | Cremat **CR-200-1µs** | same SIP-8 | Cremat CR-200-1µs | 1 | 12 | ● |
| `U_BLR` | Cremat **CR-210** | same SIP-8 | Cremat CR-210 | 1 | 12 | ● |
| `U_BUF` | **EL5167** (or LM7321) | `Package_TO_SOT_SMD:SOT-23-5` | Renesas EL5167 / TI LM7321 | 1 | 12 | ● |
| `Cc` | **0.22 µF 100 V X5R** | `Capacitor_SMD:C_0805_2012Metric` | e.g. Murata GRM21 100 V | 1 | 12 | ● |
| `Rf1`,`Rf2` | **10 kΩ** | `Resistor_SMD:R_0805_2012Metric` | any 1 % 0805 | 2 | 24 | ● |
| `Cf` | **100 nF 100 V X7R** | `Capacitor_SMD:C_0805_2012Metric` | any 100 V 0805 | 1 | 12 | ● |
| `JP_Rf1`,`JP_Rf2` | **0 Ω** (filter bypass) | `Resistor_SMD:R_0805_2012Metric` | 0R 0805 jumper | 2 | 24 | **DNP** |
| `JP_BLR` | **0 Ω** (CR-210 bypass) | `Resistor_SMD:R_0805_2012Metric` | 0R 0805 jumper | 1 | 12 | **DNP** |
| `R_OUT` | **49.9 Ω** | `Resistor_SMD:R_0805_2012Metric` | 49.9 R 1 % 0805 | 1 | 12 | ● |
| `RV_PZ` | 100 kΩ trim (pole-zero) | `Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical` | Bourns 3296W-104 | 1 | 12 | ● |
| `RV_GAIN`,`RV_OFS` | buffer gain/offset trim (per reference) | `Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical` | per reference | 2 | 24 | ● |
| `J_BIAS`,`J_SIPM`,`J_OUT` | MCX edge jack | `cremat:MCX_CONMCX013_EdgeMount` *(to create)* | TE Linx **CONMCX013** (DK 343-CONMCX013-ND) | 3 | 36 | ● |
| decoupling | 0.1 µF / 1 µF / 10 µF (per module rails) | `Capacitor_SMD:C_0805_2012Metric` | per reference | ~4 | ~48 | ● |
| buffer support R | per reference channel (feedback / bias) | `Resistor_SMD:R_0805_2012Metric` | per reference | several | — | ● |

## Shared (×1 per board)

| Ref | Value | Footprint (KiCad lib) | MPN / source | Qty |
|---|---|---|---|---|
| `J_PWR` | 3-pos screw terminal (+Vs/-Vs/GND) | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm` | Phoenix MKDS 1,5/3 | 1 |
| `C_BULK+`,`C_BULK-` | 10 µF + 100 µF electrolytic / rail | `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm` | per rail | 4 |
| `H1..H4` | M3 mounting hole | `MountingHole:MountingHole_3.2mm_M3` | — | 4 |

## Module order summary (Cremat, long lead — order early)

| Part | Qty (12-ch, Full) | Notes |
|---|---|---|
| CR-112 | 12 | charge-sensitive preamp |
| CR-200-1µs | 12 | 1 µs Gaussian shaper |
| CR-210 | 12 | baseline restorer (omit if a No-BLR build) |

## DNP by build variant

| Variant | `Rf1/Rf2/Cf` | `JP_Rf1/JP_Rf2` | `U_BLR` | `JP_BLR` |
|---|---|---|---|---|
| **Full** (first build) | ● | DNP | ● | DNP |
| No-BLR | ● | DNP | DNP | ● |
| External-bias | DNP | ● | ● | DNP |
| Reference-equiv | DNP | ● | DNP | ● |

Invariant: a `JP_*` 0R and the block it bypasses are **mutually exclusive** — never both.
