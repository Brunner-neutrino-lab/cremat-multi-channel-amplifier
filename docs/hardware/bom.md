# Bill of Materials & Population Strategy

How the BOM is organized, the 0805 passive policy, the Cremat modules, and — most
importantly — the **DNP / populate tables** that define each build variant. The
authoritative, fielded BOM lives in the KiCad project once implemented; this document is
the policy + the optional-population logic.

Carry the reference board's BOM fields forward (`MPN`, `MFN`, `VPN`, `VN`, plus a `DNP`
flag), the same convention `ets-breakout` and the reference board use.

---

## Passive size policy (Change 2)

- **Default 0805** for every R and C that allows it.
- **0R bypass jumpers** are 0805 zero-ohm links (or solder-jumper footprints for the
  tightest spots).
- **Voltage-rated exceptions stay 0805 but with HV dielectric:** the AC-coupling cap `Cc`
  and the bias-filter `Cf`/`Rf*` see the full SiPM bias. Spec `Cc` ≥ bias voltage
  (this board: `0.22 µF 100 V X7R`, KEMET **C0805C224K1RACTU**); spec `Cf` similarly. An
  0805 100 V X7R is fine;
  do not drop the rating to hit a size.
- **Never 0805** (different package): Cremat SIP-8 modules, op-amps, trimpots, coax jacks,
  power/HV connectors.

---

## Key components per channel

| Class | Ref(s) | Part | Package | Always fitted? |
|---|---|---|---|---|
| Charge-sens. preamp | `U_CSP` | Cremat **CR-112** (ref. board used CR-113) | SIP-8 module, **socketed** | yes (plugged in) |
| Shaping amp | `U_SHAPER` | Cremat **CR-200-1µs** | SIP-8 module, **socketed** | yes (plugged in) |
| Baseline restorer | `U_BLR` | Cremat **CR-210** | SIP-8 module, **socketed** | **optional** |
| Module sockets | (one per module site) | **Samtec SS-108-TT-2** SIP-8 socket (alt Harwin D01-9970842) | `PinSocket_1x08_P2.54mm_Vertical` | yes — **36/board** (3 × 12) |
| Output buffer | `U_BUF` | **TI THS3491** CFA line driver | 8-pin SOIC/PowerPAD | **DNP by default** (0R-bypassed) |
| AC coupling | `Cc` | 0.22 µF 100 V **X7R**, KEMET **C0805C224K1RACTU** (bias ≤ 70 V; keep 100 V) | 0805 | yes |
| Bias filter R | `Rf1`,`Rf2` | **10 kΩ** each (VUV4; [circuit-design.md](circuit-design.md)) | 0805 | **optional** |
| Bias filter C | `Cf` | **100 nF, 100 V, X7R** | 0805 | **optional** |
| Bias-filter bypass | `JP_Rf1`,`JP_Rf2` | 0R | 0805 | **optional** |
| BLR bypass | `JP_BLR` | 0R | 0805 | **optional** |
| P/Z trim | `RV_PZ` | **Bourns 3296W** 200 kΩ 25-turn trimpot | TH trim | yes (**12/board**) |
| Source termination | `R_OUT` | 49.9 Ω | 0805 | yes |
| Decoupling | `C_*` | 0.1 µF / 1 µF / 10 µF | 0805 | yes |
| `BIAS_IN`,`SIPM`,`TEST`,`OUT_50` jacks | `J_BIAS`,`J_SIPM`,`J_TEST`,`J_OUT` | MCX TE Linx `CONMCX013` (DK `343-CONMCX013-ND`) | edge SMT | yes (×4) |

Multiply per-channel quantities by **12** (→ **48 MCX**), then add the shared power-entry
parts once. `BIAS_IN` is per-channel, so its jack is in the per-channel count, not shared.

---

## DNP / populate tables (the optional logic)

Two independent options, **per channel**. Exactly one path in each pair is populated.

### Option A — bias filter

| Variant | `Rf1` | `Rf2` | `Cf` | `JP_Rf1` | `JP_Rf2` |
|---|---|---|---|---|---|
| **Filter fitted** | ● | ● | ● | DNP | DNP |
| **Filter bypassed** | DNP | DNP | DNP | ● (0R) | ● (0R) |

### Option B — CR-210 baseline restorer

| Variant | `U_BLR` | `U_BLR` decoupling | `JP_BLR` |
|---|---|---|---|
| **BLR fitted** | ● | ● | DNP |
| **BLR bypassed** | DNP | DNP | ● (0R) |

> **Rule of thumb:** a `JP_*` 0R and the block it bypasses are **mutually exclusive** —
> never populate both (it would short out / parallel the block). Encode this in the BOM
> `DNP` column and re-check after any schematic change. This pair-wise exclusivity is the
> single most important assembly invariant on the board.

---

## Board-level (shared) parts

| Class | Part | Notes |
|---|---|---|
| Bulk decoupling | 10 µF + 100 µF electrolytic per rail | At ±Vs entry |
| Power in `J_PWR` | **3-pos 5.08 mm Phoenix screw terminal** | ±Vs, GND supply in |
| Daisy-chain out `J_DAISY` | **3-pos 5.08 mm Phoenix screw terminal** | Raw ±Vs, GND out to the next 1U box (not the only shared connector) |
| Mounting | M3 holes / standoffs (off the case bottom cover) | Per outline |

---

## Sourcing notes

- **Cremat modules** are sourced from Cremat Inc. / distributors (e.g. Advatech UK, FAST
  ComTec). Long-ish lead time — order early. Parts chosen (D4): CSP **CR-112**, shaper
  **CR-200-1µs**, BLR **CR-210**. ×12 each (CR-210 ×12 only if the BLR-fitted variant).
- BOMs with supplier info ship in the references — `reference/cremat-x6-board/` and the
  Cremat eval boards `reference/cremat-CR-160-R7/CR-160-R7 BOM.xls` (CR-200/CR-210/buffer)
  and `reference/cremat-CR-150-R5/CR-150-R5 BOM.xls` (CR-11X). Reuse those line items for
  the parts carried forward, updating passive sizes to 0805.
- Generate the final fielded BOM from KiCad (see
  [../fabrication/fabrication-guide.md](../fabrication/fabrication-guide.md)); keep
  `pcbfab/`/`assembly/` outputs out of git (`.gitignore`), regenerate before each order.
