# Channel Circuit

One channel of the Multi-channel Cremat Amplifier. The board contains **12 identical
copies** of this cell. It derives from the reference per-channel sheet
[`reference/cremat-x6-board/channel.kicad_sch`](../../reference/cremat-x6-board/channel.kicad_sch)
with the bias front-end and CR-210 added (see [modifications.md](../modifications.md)).

Reference designators below are *cell-local*; the board flattens them per channel
(e.g. channel 7's preamp is `U7_CSP`). Use a hierarchical-sheet naming scheme so refs
stay unique across the 12 instances.

---

## Full schematic-level topology

```
                       ░░ bias filter (optional) ░░
  BIAS_IN ●───[ Rf1 ]──┬──[ Rf2 ]───●───────────────────●  SIPM        (coax to detector)
            │   ▲       │      ▲     │  FRONT-END NODE
            │  JP_Rf1   Cf    JP_Rf2 │                      DC-coupled: filtered bias
            │ (0R byp) │   (0R byp)  │                      reverse-biases the SiPM
            │          │             │
            │         GND            └──[ Cc ]──●  amp input        AC-coupled
            │                          (HV cap)  │                  (DC bias blocked)
            │                                    ▼
            │                            ┌──────────────┐
            │                            │  CR-11X CSP  │  charge-sensitive preamp
            │                            │  (U_CSP)     │  ±Vs, GND, decoupling
            │                            └──────┬───────┘
            │                                   ▼
            │                            ┌──────────────┐
            │                            │  CR-200-X    │  Gaussian shaper
            │                            │  (U_SHAPER)  │  P/Z trim (RV), ±Vs, GND
            │                            └──────┬───────┘
            │                          ░░ CR-210 (optional) ░░
            │                  ┌──────────────┐      ┌─ JP_BLR (0R bypass) ─┐
            │                  │  CR-210 BLR  │      │                      │
            │       shaper out ●──┤ (U_BLR)   ├──●───┴──────────────────────┴──● buffer in
            │                  └──────────────┘   (exactly one path populated)
            │                                          │
            │                                   ┌──────▼───────┐
            │                                   │ EL5167/LM7321│  output buffer
            │                                   │  (U_BUF)     │  gain/offset trim (RV)
            │                                   └──────┬───────┘
            │                                          │
            │                                        [ 49.9R ]  series source termination
            │                                          │
            │                                          ●  OUT   (50 Ω coax)
           GND, +VDC, -VDC distributed to every module
```

---

## Sub-blocks

### 1. Bias front-end (NEW)

| Ref | Value (starting point) | 0805? | Notes |
|---|---|---|---|
| `Rf1`, `Rf2` | bias-filter series R (e.g. 10 kΩ; tune to detector) | yes | "R" of the RC+R filter; isolate + limit SiPM current |
| `Cf` | bias-filter shunt C (e.g. 100 nF, **rated ≥ bias V**) | yes | "C" of the RC; shunts supply noise to GND |
| `JP_Rf1`, `JP_Rf2` | 0R | yes | bypass links across `Rf1`/`Rf2` |
| `Cc` | AC-coupling cap (ref: `0.22 µF 100 V X5R`) | yes (HV part) | blocks DC bias, passes pulse to CSP |

- **`BIAS_IN → Rf1 → (Cf to GND) → Rf2 → front-end node`** is the RC-in-series-with-R
  filter. Corner frequency ≈ `1 / (2π·Rf·Cf)`; choose `Rf`,`Cf` for the detector's bias
  current and the noise you need to reject. The series R also limits surge into a SiPM.
- **Front-end node → `SIPM`: solid copper (DC).** The detector is reverse-biased by the
  filtered DC. No series part here.
- **Front-end node → `Cc` → CSP input: AC.** `Cc` is the only thing between the HV node
  and the (ground-referenced) preamp input — it must hold off the full bias voltage.
- **Bypass:** fit `JP_Rf1`/`JP_Rf2` and DNP `Rf1`/`Rf2`/`Cf` to feed `BIAS_IN` straight
  to the node (see [bom.md](bom.md) DNP table).

> **Polarity / which SiPM terminal:** the reference board is agnostic (signal in on
> coax). Decide cathode-bias vs anode-bias from the detector and the CR-11X input polarity
> when implementing; the topology above is drawn terminal-agnostic. Tracked in
> [session-report.md](../session-report.md).

### 2. Charge-sensitive preamp — Cremat CR-11X (`U_CSP`)

- 8-pin SIP module. Reference board populates **CR-113**; the CR-11X family
  (CR-110/-111/-112/-113) is pin-compatible — pick per detector charge/capacitance.
- Pinout (from the reference symbol `CR-11X`): `1=input`, `2=GND`, `3=NC`, `4=GND`,
  `5=-Vs`, `6=+Vs`, `7=GND`, `8=output`.
- Local decoupling on `+Vs`/`-Vs` (the reference uses values like 0.1 µF / 1 µF / 10 µF
  per rail — keep equivalents in 0805).

### 3. Shaping amplifier — Cremat CR-200-X (`U_SHAPER`)

- 8-pin SIP module. The `-X` suffix selects shaping time (0.1–8 µs); choose per
  application. Pinout (reference symbol `CR-200`): `1=input`, `2=P/Z`, `3=GND`, `4=-Vs`,
  `5=+Vs`, `6=GND`, `7=GND`, `8=output`.
- **Pole-zero (P/Z) trim** on pin 2 via a trimpot (reference: `RV` ~100 kΩ) — carry it
  forward per channel.

### 4. Baseline restorer — Cremat CR-210 (`U_BLR`) — NEW, optional

- 8-pin SIP module, follows the shaper. Holds the output baseline at ground at high
  count rate. Shares `+VDC`/`-VDC`/`GND` + decoupling.
- **Optional:** `U_BLR` populated **xor** `JP_BLR` (0R) populated. See
  [modifications.md](../modifications.md#change-3) and the DNP table in [bom.md](bom.md).
- ⚠️ **Pinout to be confirmed against the `CR-210-R0` spec sheet** — it is a distinct
  module; do not assume the CR-200 map.

### 5. Output buffer (`U_BUF`)

- Reference populates an **EL5163/EL5167** current-feedback amp and/or **LM7321** as the
  50 Ω line driver, with a **`49.9R` series** resistor for source termination into coax,
  plus gain/offset trims (`RV` ~100 kΩ) and feedback R's.
- Carry the reference buffer forward unchanged except for resizing passives to 0805.

---

## Per-channel I/O and nets

| Net / port | Direction | Description |
|---|---|---|
| `BIAS_IN` | in (shared) | HV detector bias, common to all 12 channels |
| `SIPM` | out (per ch) | Coax to the detector; carries DC bias + the detector's pulse |
| `OUT` | out (per ch) | 50 Ω-driven shaped pulse to DAQ |
| `+VDC`,`-VDC`,`GND` | power | Analog supply, common to all modules |

---

## Optional-block jumper summary (per channel)

| Optional block | Populate for "fitted" | Populate for "bypassed" |
|---|---|---|
| Bias filter | `Rf1`,`Rf2`,`Cf` | `JP_Rf1`,`JP_Rf2` (0R); DNP `Rf1`,`Rf2`,`Cf` |
| CR-210 BLR | `U_BLR` (+ decoupling) | `JP_BLR` (0R); DNP `U_BLR` |

`Cc`, the CSP, the shaper, and the buffer are **always populated** — they are the core
amplifier. Only the bias filter and the CR-210 are optional.
