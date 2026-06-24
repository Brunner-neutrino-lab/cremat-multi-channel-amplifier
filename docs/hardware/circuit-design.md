# Circuit & Front-End Design (Track 2)

Concrete component values and the front-end topology choices, derived for the target
detector. This is the Track 2 deliverable; it fixes the placeholder values used elsewhere
in the docs. Bench-verify items are listed at the end.

---

## Target detector — Hamamatsu VUV4 MPPC (S13370, 6 mm, 75 µm pixel)

| Parameter | Value | Source |
|---|---|---|
| Active area / pitch | 6 × 6 mm, 75 µm micro-cells | Hamamatsu (the "70 µm" pixel) |
| Terminal capacitance `Cdet` | **≈ 1.28 nF** | Hamamatsu / nEXO characterization |
| Breakdown `Vbr` | ≈ 55 V (room) / ≈ 42 V (86 K) | Hamamatsu |
| Operating reverse bias | **45–55 V** (≤ 60 V → D1 OK, 100 V parts) | user |
| Charge / avalanche | **≈ 220 fC per 1 V overvoltage** (≈ 1.37×10⁶ e⁻/V) | user; matches Hamamatsu gain 5.8×10⁶ @ 4 V OV |
| Polarity | reverse-biased (cathode positive) | user |

The 45–55 V operating point sits just above the **cold** breakdown (~42–45 V at LXe
temperatures), i.e. the device is expected to run **cold** → **low dark current**, which
relaxes the bias-filter DC-drop budget (see below). The board must still behave at room
temperature for bench bring-up, where dark current is much higher.

---

## Operating point / charge budget

- Charge per fired micro-cell scales with overvoltage: `Q1pe ≈ 220 fC × OV[V]`.
  - At 1 V OV: 0.22 pC. At a typical 3–4 V OV: **0.66–0.88 pC** per p.e.
- The SiPM's own gain (~1.4×10⁶ e⁻ per p.e. per volt OV) is enormous, so **preamp noise
  is negligible for single-p.e. resolution** even with the large `Cdet` (the CSP ENC of a
  few 10³ e⁻ is ≪ the 10⁶ e⁻ single-p.e. charge).

---

## Front-end polarity (decision)

The channel topology biases and reads the **same** SiPM terminal (the front-end node),
with the other terminal grounded. To reverse-bias the VUV4 (cathode positive):

- **Front-end node = SiPM cathode**, biased to **+45…+55 V** through the filter.
- **SiPM anode → GND.**
- Read the cathode node through `Cc` into the CR-112.

This uses a **positive** bias supply (simplest). The avalanche discharges the node, so the
charge coupled into the CR-112 is negative-going; the resulting CR-112 output-step polarity
is fixed by this connection — **confirm the sign against the CR-112 datasheet on the bench**
and set the CR-200 / DAQ to match. (If the opposite polarity were ever required, the only
alternative in this single-node topology is anode-on-node with a **negative** bias supply;
not preferred.)

---

## Bias filter (the "RC-in-series-with-R", optional/bypassable)

```
 BIAS_IN(+45..55V) ──[ Rf1 ]──┬──[ Rf2 ]──► front-end node ──► SiPM cathode
                              │                            └──► Cc ─► CR-112
                             Cf
                              │
                             GND
```

| Part | Value | Footprint | Role |
|---|---|---|---|
| `Rf1` | **10 kΩ** | 0805 | series R of the RC low-pass (with `Cf`) |
| `Cf`  | **100 nF, 100 V, X7R** | 0805 | shunt reservoir / supply-noise bypass |
| `Rf2` | **10 kΩ** | 0805 | isolates the SiPM node from `Cf` so the fast charge flows into `Cc`, not back to the supply |

- **Supply-noise low-pass:** `fc = 1/(2π·Rf1·Cf) ≈ 159 Hz` → strong rejection of bias-supply
  ripple/noise above ~160 Hz.
- **DC drop** = `I_bias × (Rf1+Rf2) = I_bias × 20 kΩ`. Cold (`I` ~ nA): **negligible**
  (< 1 mV). Warm bench (`I` up to ~10 µA for a 6 mm VUV4): ~0.2 V — keep in mind when
  setting OV on the bench, or temporarily fit smaller `Rf` for warm characterization.
- **Node recovery** `Rf2·Cdet = 10 kΩ × 1.28 nF ≈ 13 µs` — fast enough for 1 µs shaping at
  moderate rates.
- **Tuning:** for production **cold-only** boards, `Rf1`/`Rf2` may be raised to **100 kΩ–1 MΩ**
  for stronger filtering and near-total charge transfer into the CSP, since the cold DC drop
  stays small. Keep 10 kΩ as the default that also survives warm bench testing.
- **Bypass (0R):** fit `JP_Rf1`,`JP_Rf2` and DNP `Rf1`,`Rf2`,`Cf` to feed `BIAS_IN` straight
  to the node (clean external supply / external filter).

---

## AC coupling `Cc`

| Part | Value | Footprint |
|---|---|---|
| `Cc` | **0.22 µF, 100 V, X5R/X7R** | 0805 |

- Blocks the ≤ 55 V DC bias from the CR-112 input; 100 V rating gives margin (matches the
  reference board's `0.22 µF 100 V X5R`).
- **Charge transfer:** `Cc (0.22 µF) ≫ Cdet (1.28 nF)` by ~170×, so ≈ **99.4 %** of the
  SiPM charge transfers into the (virtual-ground) CR-112 input. This is why `Cc` is large —
  a small coupling cap comparable to `Cdet` would lose a large fraction of the signal.

---

## Preamp / shaper / output (carried from the reference, sized to the VUV4)

- **CR-112 CSP** (gain **13 mV/pC**): single-p.e. output step ≈ `0.22 pC × OV × 13 mV/pC`
  → **~10 mV at 3.5 V OV**, scaling linearly with p.e. count and OV.
  - **Linear range:** with a CSP output swing of ~±2 V, the CR-112 stays linear to
    ~`2 V / 13 mV·pC⁻¹ ≈ 150 pC` (≈ **200 p.e. at 3.5 V OV**). For larger scintillation
    signals, **CR-113** (10× lower gain, pin-compatible) is the drop-in fallback — but D4
    selected CR-112; revisit only if saturation is observed.
- **CR-200-1µs shaper** + pole-zero trim: as on the reference board; 1 µs shaping (D4).
- **Output buffer** (EL5167 / LM7321) + **49.9 Ω** series source termination into 50 Ω coax;
  gain/offset trims per channel — unchanged from the reference.

---

## Power / decoupling

- Rails `+VDC` / `-VDC` (±Vs, Cremat-style, typ. ±12 V — confirm against module max ratings),
  shared across all 12 channels.
- Local decoupling at every Cremat module + op-amp (0.1 µF / 1 µF / 10 µF per the reference),
  0805 where the rating allows; bulk 10 µF + 100 µF per rail at entry.

---

## Bench-verify checklist (closes the remaining open items)

1. **CR-112 output-step polarity** for the cathode-on-node connection → set CR-200 / DAQ
   polarity to match.
2. **Warm vs cold OV offset** from the 20 kΩ bias-filter drop at the actual dark current;
   decide whether production cold boards raise `Rf` to 100 kΩ–1 MΩ.
3. **Single-p.e. amplitude & linear range** at the intended OV; confirm CR-112 (vs CR-113)
   is the right gain for the expected photon yield.
4. **Pole-zero trim** for a clean return-to-baseline at 1 µs shaping.
