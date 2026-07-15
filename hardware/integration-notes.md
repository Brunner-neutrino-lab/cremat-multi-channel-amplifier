# Integration Notes — golden per-channel netlist (Track 3 deliverable)

The authoritative per-channel connectivity for schematic capture (Track 5). Pinouts are
confirmed from the Cremat open-source boards; values from
[../docs/hardware/circuit-design.md](../docs/hardware/circuit-design.md).

## Hierarchy

```
multi-channel-cremat-amplifier.kicad_sch   (root)
  ├─ power: J_PWR screw terminal → +VDC / -VDC / GND distributed to all sheets
  └─ channel.kicad_sch  ×12   (each instance carries its own 4 MCX jacks)
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
CR-210 = CR-200 except pin 2: P/Z → GND.) Buffer `U_BUF` (**TI THS3491**, 8-pin
HSOIC/DDA PowerPAD): as WIRED IN THIS DESIGN (`gen_sch.py`) — 1=GND (REF), 2=VIN− (feedback),
3=VIN+ (input), 4=−VS, 5=NC, 6=VOUT, 7=+VS, 8=+VS (tied to pin 7 → PD held high = enabled).
The **thermal pad (EP, pin 9) ties to −VS** (the DDA PowerPAD is internally connected to −VS),
**not** to GND.

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
| `BLR_OUT` | `U_BLR`.8 · `JP_BLR`.2 · `JP_BUF`.1 · buffer input network (→ `U_BUF`.3 = VIN+ via Rin) |
| `BUF_OUT` | `U_BUF`.6 (VOUT) · `R_OUT`.1 · `JP_BUF`.2 · buffer feedback network (→ `U_BUF`.2 = VIN−) |
| `OUT` | `R_OUT`.2 · `J_OUT`.1 (center, the 50 Ω `OUT_50` jack) |
| `+VDC` | `U_CSP`.6 · `U_SHAPER`.5 · `U_BLR`.5 · `U_BUF`.7 (+VS) · `U_BUF`.8 (+VS, tied to pin 7) · decoupling |
| `-VDC` | `U_CSP`.5 · `U_SHAPER`.4 · `U_BLR`.4 · `U_BUF`.4 (−VS) · `U_BUF`.9 (thermal pad / EP → −VS) · decoupling |
| `GND` | `U_CSP`.{2,4,7} · `U_SHAPER`.{3,6,7} · `U_BLR`.{2,3,6,7} · `U_BUF`.1 (REF → GND) · `U_BUF`.5 (NC) · `Cf`.2 · `J_*`.2 (shields) · decoupling returns |

> Each channel has a **4th MCX, `J_TEST`** (charge-injection input), in addition to
> `J_BIAS`, `J_SIPM`, `J_OUT` (= the 50 Ω `OUT_50`) above — 4 jacks/channel, 48/board. It
> couples into the CSP input (`CSP_IN`) through a small test capacitor per the reference
> channel; its exact network is finalized at schematic capture.

## The three bypass jumpers (populate-XOR)

- **Bias filter:** `JP_Rf1` parallels `Rf1` (`BIAS_IN`↔`N_filt`); `JP_Rf2` parallels `Rf2`
  (`N_filt`↔`FE`). Fitted filter ⇒ `Rf1/Rf2/Cf` populated, `JP_Rf*` DNP. Bypassed ⇒ `JP_Rf*`
  = 0 Ω, `Rf1/Rf2/Cf` DNP ⇒ `BIAS_IN`=`FE` (straight through).
- **CR-210:** `JP_BLR` parallels the module (`SH_OUT`↔`BLR_OUT`). Fitted ⇒ `U_BLR`
  populated, `JP_BLR` DNP. Bypassed ⇒ `JP_BLR` = 0 Ω, `U_BLR` DNP ⇒ `SH_OUT`=`BLR_OUT`.
- **THS3491 buffer:** `JP_BUF` parallels the buffer (`BLR_OUT`↔`BUF_OUT`). **Default build
  is bypassed** ⇒ `JP_BUF` = 0 Ω, `U_BUF` DNP ⇒ `BLR_OUT`=`BUF_OUT` (shaper/BLR drives
  `R_OUT` directly). Buffered ⇒ `U_BUF` populated, `JP_BUF` DNP.

This mirrors the CR-160-R7 `JU1`-across-the-module pattern (now an 0805 0R).

## Notes for capture (carry from the reference channel)

- **Pole-zero network** (`U_SHAPER`.2, `RV_PZ` 200 kΩ 25-turn) follows
  `reference/cremat-x6-board/channel.kicad_sch` — reuse that sub-circuit, resizing passives
  to 0805.
- **Output buffer** is now a **TI THS3491** CFA (8-pin HSOIC/PowerPAD), **DNP by default**
  with a `JP_BUF` 0R bypass so the shaper/BLR drives `R_OUT` (49.9 Ω) directly. When fitted,
  set gain with its own `Rf`/`Rg` per the THS3491 datasheet — **there are no gain/offset
  trimpots** (the EL5163/LM7321-era `RV_GAIN`/`RV_OFS` are gone). Give it its own ±VS
  decoupling. Per the schematic: pin 8 ties to +VS (holds PD high = enabled), pin 1 (REF)
  ties to GND, and the thermal pad (EP, pin 9) ties to −VS.
- **Decoupling:** 0.1 µF / 1 µF / 10 µF per `±Vs` rail at each module, per the reference.
- **Capture technique:** internal nets can be wired by **local labels** (the names above);
  only `+VDC/-VDC/GND` need hierarchical pins. This keeps the 12× instantiation clean.
