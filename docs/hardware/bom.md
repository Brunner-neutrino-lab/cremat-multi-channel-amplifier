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
  (reference: `0.22 µF 100 V X5R`); spec `Cf` similarly. An 0805 100 V X7R/X5R is fine;
  do not drop the rating to hit a size.
- **Never 0805** (different package): Cremat SIP-8 modules, op-amps, trimpots, coax jacks,
  power/HV connectors.

---

## Key components per channel

| Class | Ref(s) | Part | Package | Always fitted? |
|---|---|---|---|---|
| Charge-sens. preamp | `U_CSP` | Cremat **CR-11X** (ref: CR-113) | SIP-8 TH | yes |
| Shaping amp | `U_SHAPER` | Cremat **CR-200-X** (pick shaping time) | SIP-8 TH | yes |
| Baseline restorer | `U_BLR` | Cremat **CR-210** | SIP-8 TH | **optional** |
| Output buffer | `U_BUF` | EL5167 / LM7321 | SOT-23-5 / SO-8 | yes |
| AC coupling | `Cc` | 0.22 µF 100 V X5R (≥ bias V) | 0805 | yes |
| Bias filter R | `Rf1`,`Rf2` | series R (tune; e.g. 10 kΩ) | 0805 | **optional** |
| Bias filter C | `Cf` | shunt C (e.g. 100 nF, ≥ bias V) | 0805 | **optional** |
| Bias-filter bypass | `JP_Rf1`,`JP_Rf2` | 0R | 0805 | **optional** |
| BLR bypass | `JP_BLR` | 0R | 0805 | **optional** |
| P/Z trim | `RV_PZ` | trimpot ~100 kΩ | TH/SMD trim | yes |
| Gain/offset trim | `RV_*` | trimpot (per reference) | TH/SMD trim | yes |
| Source termination | `R_OUT` | 49.9 Ω | 0805 | yes |
| Decoupling | `C_*` | 0.1 µF / 1 µF / 10 µF | 0805 | yes |
| `SIPM`, `OUT` jacks | `J_*` | MCX/SMA coax | — | yes |

Multiply per-channel quantities by **12**, then add the shared power-entry / `BIAS_IN`
parts once.

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
| Power connector | screw terminal / locking header | ±Vs, GND |
| `BIAS_IN` connector | SHV / isolated HV | Single HV entry |
| Mounting | M3 holes / standoffs | Per outline |

---

## Sourcing notes

- **Cremat modules** (CR-11X, CR-200-X, CR-210) are sourced from Cremat Inc. / distributors
  (e.g. Advatech UK, FAST ComTec). Long-ish lead time — order early. Pick the CR-200 `-X`
  shaping time and the CR-11X gain grade per the detector before ordering.
- BOMs with supplier info ship in the references — `reference/cremat-x6-board/` and the
  Cremat eval boards `reference/cremat-CR-160-R7/CR-160-R7 BOM.xls` (CR-200/CR-210/buffer)
  and `reference/cremat-CR-150-R5/CR-150-R5 BOM.xls` (CR-11X). Reuse those line items for
  the parts carried forward, updating passive sizes to 0805.
- Generate the final fielded BOM from KiCad (see
  [../fabrication/fabrication-guide.md](../fabrication/fabrication-guide.md)); keep
  `pcbfab/`/`assembly/` outputs out of git (`.gitignore`), regenerate before each order.
