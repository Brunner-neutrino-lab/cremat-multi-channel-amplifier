# Integration Notes — golden per-channel netlist (Track 3 deliverable)

The authoritative per-channel connectivity for schematic capture (Track 5). Pinouts are
confirmed from the Cremat open-source boards; values from
[../docs/hardware/circuit-design.md](../docs/hardware/circuit-design.md).

## Hierarchy

```
multi-channel-cremat-amplifier.kicad_sch   (root)
  ├─ power: J_PWR screw terminal → +VDC / -VDC / GND distributed to all sheets
  └─ channel.kicad_sch  ×12   (each instance carries its own 3 MCX jacks)
```

The channel sheet has **three hierarchical pins only: `+VDC`, `-VDC`, `GND`** (the shared
analog supply). Everything else — `BIAS_IN`, `SIPM`, `OUT`, and all internal nodes — is
**local to the sheet**, so each of the 12 instances gets its own independent copy. `BIAS_IN`
is therefore per-channel (its own `J_BIAS` MCX on the sheet), not a shared rail.

## Confirmed module pinouts (SIP-8)

| Pin | CR-112 (`U_CSP`) | CR-200-1µs (`U_SHAPER`) | CR-210 (`U_BLR`) |
|---|---|---|---|
| 1 | input | input | input |
| 2 | GND | **P/Z** | **GND** |
| 3 | NC | GND | GND |
| 4 | GND | -Vs | -Vs |
| 5 | -Vs | +Vs | +Vs |
| 6 | +Vs | GND | GND |
| 7 | GND | GND | GND |
| 8 | output | output | output |

(CR-200/CR-210 from `reference/cremat-CR-160-R7`; CR-11X from `reference/cremat-CR-150-R5`.
CR-210 = CR-200 except pin 2: P/Z → GND.) Buffer `U_BUF` (EL5167/LM7321, SOT-23-5):
1=OUT, 2=V-, 3=+IN, 4=-IN, 5=V+.

## Per-channel net → pin map

Local nets (per instance): `BIAS_IN, N_filt, FE, CSP_IN, CSP_OUT, SH_OUT, PZ, BLR_OUT,
BUF_OUT, OUT`. Shared (hierarchical): `+VDC, -VDC, GND`.

| Net | Connects (pins) |
|---|---|
| `BIAS_IN` | `J_BIAS`.1 (center) · `Rf1`.1 · `JP_Rf1`.1 |
| `N_filt` | `Rf1`.2 · `Cf`.1 · `Rf2`.1 · `JP_Rf1`.2 · `JP_Rf2`.1 |
| `FE` (front-end node) | `Rf2`.2 · `JP_Rf2`.2 · `J_SIPM`.1 (center) · `Cc`.1 |
| `CSP_IN` | `Cc`.2 · `U_CSP`.1 |
| `CSP_OUT` | `U_CSP`.8 · `U_SHAPER`.1 |
| `PZ` | `U_SHAPER`.2 · `RV_PZ` (pole-zero network, see note) |
| `SH_OUT` | `U_SHAPER`.8 · `U_BLR`.1 · `JP_BLR`.1 |
| `BLR_OUT` | `U_BLR`.8 · `JP_BLR`.2 · buffer input network (→ `U_BUF`.3 via reference Rin) |
| `BUF_OUT` | `U_BUF`.1 · `R_OUT`.1 · buffer feedback network |
| `OUT` | `R_OUT`.2 · `J_OUT`.1 (center) |
| `+VDC` | `U_CSP`.6 · `U_SHAPER`.5 · `U_BLR`.5 · `U_BUF`.5 · decoupling |
| `-VDC` | `U_CSP`.5 · `U_SHAPER`.4 · `U_BLR`.4 · `U_BUF`.2 · decoupling |
| `GND` | `U_CSP`.{2,4,7} · `U_SHAPER`.{3,6,7} · `U_BLR`.{2,3,6,7} · `Cf`.2 · `J_*`.2 (shields) · decoupling returns |

## The two bypass jumpers (populate-XOR)

- **Bias filter:** `JP_Rf1` parallels `Rf1` (`BIAS_IN`↔`N_filt`); `JP_Rf2` parallels `Rf2`
  (`N_filt`↔`FE`). Fitted filter ⇒ `Rf1/Rf2/Cf` populated, `JP_Rf*` DNP. Bypassed ⇒ `JP_Rf*`
  = 0 Ω, `Rf1/Rf2/Cf` DNP ⇒ `BIAS_IN`=`FE` (straight through).
- **CR-210:** `JP_BLR` parallels the module (`SH_OUT`↔`BLR_OUT`). Fitted ⇒ `U_BLR`
  populated, `JP_BLR` DNP. Bypassed ⇒ `JP_BLR` = 0 Ω, `U_BLR` DNP ⇒ `SH_OUT`=`BLR_OUT`.

This mirrors the CR-160-R7 `JU1`-across-the-module pattern (now an 0805 0R).

## Notes for capture (carry from the reference channel)

- **Pole-zero network** (`U_SHAPER`.2) and the **output buffer** (gain/offset trims
  `RV_GAIN`/`RV_OFS`, feedback + input resistors, decoupling) follow
  `reference/cremat-x6-board/channel.kicad_sch` — reuse that sub-circuit verbatim, only
  resizing passives to 0805. The reference buffer used EL5163/LM7321 with a `49.9 Ω`
  series output; values R14/R22/R23/R24/R26/R27/… carry over.
- **Decoupling:** 0.1 µF / 1 µF / 10 µF per `±Vs` rail at each module, per the reference.
- **Capture technique:** internal nets can be wired by **local labels** (the names above);
  only `+VDC/-VDC/GND` need hierarchical pins. This keeps the 12× instantiation clean.
