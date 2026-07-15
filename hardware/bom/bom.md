# Fielded BOM — Multi-channel Cremat Amplifier (Track 1 deliverable)

Per-channel parts ×12 + shared parts, for the **Full build variant** (bias filter fitted +
CR-210 fitted; all `JP_*` 0R bypasses DNP **except `JP_BUF`** — the THS3491 output buffer
is DNP by default and its 0R bypass is fitted). Policy/rationale is in
[../../docs/hardware/bom.md](../../docs/hardware/bom.md); designed values are in
[../../docs/hardware/circuit-design.md](../../docs/hardware/circuit-design.md).

> The front-end, modules, output termination, optional jumpers, trimpots, and connectors
> below are fixed. The CR-200→buffer **support passives + per-rail decoupling** carry over
> from the reference channel (`reference/cremat-x6-board/channel.kicad_sch`) and are
> finalized when Track 5 captures the schematic and exports the authoritative netlist BOM.

## Per-channel (×12)

| Ref (per ch) | Value | Footprint (KiCad lib) | MPN / source | Qty/ch | Qty×12 | Populate (Full) |
|---|---|---|---|---|---|---|
| `U_CSP` | Cremat **CR-112** (plugs into socket) | — plugs into the SIP-8 socket below | Cremat CR-112 *(owned)* | 1 | 12 | ● |
| `U_SHAPER` | Cremat **CR-200-1µs** (plugs in) | — plugs into the SIP-8 socket below | Cremat CR-200-1µs *(owned)* | 1 | 12 | ● |
| `U_BLR` | Cremat **CR-210** (plugs in) | — plugs into the SIP-8 socket below | Cremat CR-210 *(owned)* | 1 | 12 | ● |
| module socket (×3/ch) | **SIP-8 socket** carrying the 3 modules above (soldered; modules never soldered) | `Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical` | Samtec **SS-108-TT-2** (alt Harwin D01-9970842) | 3 | 36 | ● |
| `U_BUF` | **TI THS3491** CFA output buffer | `Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm` (SOIC-8 PowerPAD — confirm EP size vs DDA land) | TI **THS3491** (DK 296-49085-1-ND) | 1 | 12 | **DNP** |
| `JP_BUF` | **0 Ω** (buffer bypass) | `Resistor_SMD:R_0805_2012Metric` | 0R 0805 jumper | 1 | 12 | ● |
| `Cc` | **0.22 µF 100 V X7R** | `Capacitor_SMD:C_0805_2012Metric` | KEMET **C0805C224K1RACTU** (alt Murata GRM21AR72A224KAC5K) | 1 | 12 | ● |
| `Rf1`,`Rf2` | **10 kΩ** | `Resistor_SMD:R_0805_2012Metric` | any 1 % 0805 | 2 | 24 | ● |
| `Cf` | **100 nF 100 V X7R** | `Capacitor_SMD:C_0805_2012Metric` | any 100 V 0805 | 1 | 12 | ● |
| `JP_Rf1`,`JP_Rf2` | **0 Ω** (filter bypass) | `Resistor_SMD:R_0805_2012Metric` | 0R 0805 jumper | 2 | 24 | **DNP** |
| `JP_BLR` | **0 Ω** (CR-210 bypass) | `Resistor_SMD:R_0805_2012Metric` | 0R 0805 jumper | 1 | 12 | **DNP** |
| `R_OUT` | **49.9 Ω** | `Resistor_SMD:R_0805_2012Metric` | 49.9 R 1 % 0805 | 1 | 12 | ● |
| `RV_PZ` | 200 kΩ trim (pole-zero, 25-turn) | `Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical` | Bourns 3296W-204 | 1 | 12 | ● |
| `J_BIAS`,`J_SIPM`,`J_TEST`,`J_OUT` | MCX edge jack (`BIAS`/`SIPM`/`TEST`/`OUT_50`) | `cremat:MCX_CONMCX013-T` | TE Linx **CONMCX013** (DK 343-CONMCX013-ND) | 4 | 48 | ● |
| decoupling | 0.1 µF / 1 µF / 10 µF (per module rails) | `Capacitor_SMD:C_0805_2012Metric` | per reference | ~4 | ~48 | ● |
| buffer support R | THS3491 CFA gain-set (`Rf`/`Rg`) + decoupling | `Resistor_SMD:R_0805_2012Metric` | per THS3491 datasheet | several | — | fit w/ `U_BUF` |

## Shared (×1 per board)

| Ref | Value | Footprint (KiCad lib) | MPN / source | Qty |
|---|---|---|---|---|
| `J_PWR` | 3-pos 5.08 mm screw terminal — **supply in** (+Vs/−Vs/GND) | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal` | Phoenix MKDS 1,5/3-5.08 | 1 |
| `J_DAISY` | 3-pos 5.08 mm screw terminal — **raw rails out** to the next 1U box | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal` | Phoenix MKDS 1,5/3-5.08 | 1 |
| `C_BULK+`,`C_BULK-` | 10 µF + 100 µF electrolytic / rail | `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm` | per rail | 4 |
| `H1..H4` | M3 mounting hole | `MountingHole:MountingHole_3.2mm_M3` | — | 4 |

## Module summary (Cremat — already owned, socketed)

| Part | Qty (12-ch, Full) | Notes |
|---|---|---|
| CR-112 | 12 | charge-sensitive preamp |
| CR-200-1µs | 12 | 1 µs Gaussian shaper |
| CR-210 | 12 | baseline restorer (omit if a No-BLR build) |

**All three module types are already owned** (qty 12 each). They **plug into the
SS-108-TT-2 sockets** (never soldered) and are **not part of the JLCPCB fab/assembly
order**. For reference, the 2026-01 Cremat US list (qty-12 tier) is CR-112 $55 /
CR-200-1µs $55 / CR-210 $77 ⇒ ~$2,244/board.

## DNP by build variant

| Variant | `Rf1/Rf2/Cf` | `JP_Rf1/JP_Rf2` | `U_BLR` | `JP_BLR` |
|---|---|---|---|---|
| **Full** (first build) | ● | DNP | ● | DNP |
| No-BLR | ● | DNP | DNP | ● |
| External-bias | DNP | ● | ● | DNP |
| Reference-equiv | DNP | ● | DNP | ● |

Invariant: a `JP_*` 0R and the block it bypasses are **mutually exclusive** — never both.

The **THS3491 output buffer (`U_BUF`) is DNP by default in every variant above** — `JP_BUF`
= 0R is fitted so the shaper/BLR drives the 49.9 Ω back-termination directly. Populate
`U_BUF` (and its gain-set `Rf`/`Rg`) and DNP `JP_BUF` only when a buffered 50 Ω output is
required. This buffer↔`JP_BUF` pair obeys the same mutual-exclusion invariant.
