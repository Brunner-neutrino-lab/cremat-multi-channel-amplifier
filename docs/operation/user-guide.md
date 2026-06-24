# User and Operation Guide

How to power, bias, and operate the 12-channel Cremat amplifier, and how to choose the
populate/bypass options. This is a **passive (always-on) analog board** — there is no
firmware, no commands, no channel selection. All 12 channels amplify continuously.

---

## What you connect

| Connector | Qty | Connect to |
|---|---|---|
| `SIPM` (per channel) | 12 | One detector each (coax). Carries **DC bias + signal** on the same line. |
| `OUT` (per channel) | 12 | DAQ / digitizer / scope input (50 Ω, coax). |
| `BIAS_IN` | 1 | Detector bias supply (HV). Shared by all 12 channels. |
| Power (±Vs, GND) | 1 | Dual analog supply (Cremat-style, typically ±12 V — confirm module ratings). |

Because the bias rail is shared, **all detectors run at the same bias voltage.** Group
detectors that want the same over-voltage on one board.

---

## Choosing the configuration (set at assembly)

The board is built in one fixed configuration (see
[../hardware/bom.md](../hardware/bom.md)). Pick based on your setup:

| If you… | Bias filter | CR-210 |
|---|---|---|
| bias SiPMs from a noisy supply | **fit** the RC+R filter | — |
| have a clean external bias / external bias-tee | **bypass** the filter (0R) | — |
| run at medium/high count rate, care about resolution | — | **fit** the CR-210 |
| run at low rate or want minimum latency | — | **bypass** the CR-210 (0R) |

You cannot change these at runtime; they are populate/DNP choices on the PCB.

---

## Power-up sequence

1. Confirm the build's jumper configuration matches your intended use (label the board).
2. Apply **±Vs** first (analog supply). The amplifier chain powers up.
3. Ramp **`BIAS_IN`** from **0 V** up to the detector operating voltage **gradually** —
   the on-board filter (if fitted) adds an RC settling time; allow it to settle.
4. Observe `OUT` on a scope: with a detector and light (or dark counts), you should see
   shaped Gaussian pulses.

## Power-down sequence

1. Ramp **`BIAS_IN`** to **0 V** first.
2. Then remove **±Vs**.
3. Only then disconnect detectors or output cables.

> **Never** connect/disconnect a detector while `BIAS_IN` is live.

---

## Per-channel signal path (what happens to a detector pulse)

```
detector charge ─► SiPM (DC-biased via filter) ─► Cc (AC) ─► CR-11X CSP ─► CR-200-X shaper
                                                            ─► [CR-210 BLR] ─► buffer ─► OUT
```

- The **filtered DC bias** holds the SiPM at operating voltage (DC path to `SIPM`).
- The SiPM's **current pulse** passes through `Cc` into the charge-sensitive preamp (AC
  path) — the DC bias is blocked from the amplifier.
- The shaper produces a Gaussian pulse; if the **CR-210** is fitted it holds the baseline
  at ground (better at high rate); the buffer drives it into 50 Ω coax at `OUT`.

---

## Tuning

- **Pole-zero (P/Z):** each channel has a P/Z trimpot on the CR-200-X. With a test pulse
  (or detector pulses) on the scope, adjust until the shaped pulse returns cleanly to
  baseline with no undershoot/overshoot.
- **Gain/offset:** the buffer trimpots set per-channel gain/offset; match channels if your
  DAQ expects uniform amplitude.
- **Shaping time** is fixed by the CR-200-**X** part installed (chosen at order time).

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| No pulses on a channel | bias not reaching detector | check `BIAS_IN`, and that the filter path or its 0R bypass is populated (not neither) |
| Output railed / large DC offset | `Cc` not blocking, or buffer offset | verify `Cc` populated & rated; trim offset |
| Baseline shifts with rate | CR-210 bypassed | rebuild with CR-210 fitted, or accept for low-rate use |
| Excess noise on all channels | bias-supply noise / filter bypassed | fit the bias filter; check `GND` integrity |
| One channel oscillates | P/Z mis-trim or layout | re-trim P/Z; inspect that channel's front-end |
| Both block and its 0R fitted | assembly error | remove one — block and bypass are mutually exclusive ([bom.md](../hardware/bom.md)) |

---

## Safety

1. **High voltage:** `BIAS_IN` and the `SIPM` lines carry the bias voltage (tens of volts
   for SiPMs, possibly more). Ramp down before touching detector cabling. Follow lab HV
   practice.
2. **ESD:** SiPMs and the front-end are ESD-sensitive — grounded strap + mat.
3. **Shared bias:** all 12 channels share `BIAS_IN`; a fault on one detector line affects
   the shared rail. Use per-detector series protection if that risk matters.
