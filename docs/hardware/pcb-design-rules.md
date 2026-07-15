# PCB Design Rules

Net classes, trace widths, clearances, and HV considerations for the 12-channel amplifier.
Modeled on the reference board and on `ets-breakout`'s net-class scheme, with the addition
of an explicit **HV bias** class because this board now carries the per-channel detector
bias nets (12× `BIAS_IN`, ≤ 70 V).

Set these in the KiCad project (`*.kicad_pro`) so they apply automatically by net name.

---

## Net classes

### `Default`
| Parameter | Value |
|---|---|
| Track width | 0.20 mm (~8 mil) |
| Clearance | 0.20 mm |
| Via Ø / drill | 0.6 / 0.3 mm |

Low-current analog/logic-level interconnect between modules.

### `power` — `+VDC`, `-VDC`, `GND`
| Parameter | Value |
|---|---|
| Track width | 0.5 mm (~20 mil) min, wider on the plane feeds |
| Clearance | 0.2 mm |

Wider for low IR drop; prefer a poured plane for `GND`.

### `hv_bias` — `BIAS_IN` and per-channel filtered bias / `SIPM` (NEW)
| Parameter | Value |
|---|---|
| Track width | 0.4 mm (current is tiny; width is for robustness/HV) |
| Clearance / creepage | **set from the SiPM bias voltage** — see table below |

Assign by net-name pattern: `BIAS*`, `SIPM*`, and the front-end node nets. This is the
only HV class; give it the most clearance and keep it off plane edges.

### `signal` — amplifier I/O, `OUT`
| Parameter | Value |
|---|---|
| Track width | ~0.33 mm (≈50 Ω microstrip on a typical 4-layer stack, as `ets-breakout` used) |
| Clearance | 0.2 mm |

Use for `OUT` (50 Ω-driven). Match the reference board's pattern of a dedicated class for
the coax-driven nets. This board is **not** ordered as controlled impedance — see
[Stackup](#stackup) for why transmission-line effects are negligible at the ~1 µs pulse
bandwidth.

---

## HV clearance / creepage (per-channel bias nets)

The detector bias sets the minimum spacing on the `hv_bias` class. **Bias is confirmed
≤ 70 V**, so the `hv_bias` class is fabbed with **0.6 mm clearance/creepage** (with the
0.4 mm track above); parts (`Cc`,`Cf`) stay rated 100 V for margin.

| Bias voltage | Min clearance/creepage (uncoated FR4, guide) |
|---|---|
| ≤ 50 V | 0.5 mm |
| **≤ 70 V (this board → `hv_bias` class)** | **0.6 mm (as fabbed)** |
| ≤ 250 V | 2.0 mm |

These are conservative starting points (IPC-2221 B internal/external, no conformal
coating). Tighten only with justification. Enforce via the `hv_bias` clearance and KiCad's
**creepage** DRC rule (treat creepage/clearance violations as **errors**, as the reference
project does). The final board's live DRC confirms the 0.6 mm `hv_bias` clearance with
**0 errors**.

---

## Guard / sensitive node

- The **front-end node** (`BIAS_IN→filter→node→Cc→CSP input`) is the high-impedance,
  noise-sensitive node. Keep it small; consider a `GND`-referenced guard or a local pour
  back-off, following the reference board and `ets-breakout`'s guard-ring practice.
- Keep `Cc` and the CSP input pads tight together to minimize the exposed HV-to-amp node.

---

## DRC severities (match the reference project)

**Errors (block fab):** clearance, creepage, copper-to-edge, annular ring, hole/hole &
hole-to-copper, drill out of range, courtyard overlap, invalid outline, items on disabled
layers.

**Warnings:** connection width, copper slivers, duplicate/extra/missing footprints,
silk overlaps.

**Gate:** `kicad-cli pcb drc` must report **0 errors** before generating fab outputs — the
same gate `ets-breakout` enforces.

---

## Stackup

Fabbed at **JLCPCB on their standard 4-layer 1.6 mm stackup `JLC04161H-7628`** — a **normal,
non-impedance-controlled** build:

| Layer | Copper | Assignment | Dielectric below |
|---|---|---|---|
| **L1 (F.Cu)** | 1 oz | signal / pour | 0.2104 mm **7628 prepreg** (Dk ≈ 4.4) |
| **L2 (In1)** | 0.5 oz | **GND plane** | 1.065 mm **core** (Dk ≈ 4.6) |
| **L3 (In2)** | 0.5 oz | **−VDC plane** | 0.2104 mm **7628 prepreg** |
| **L4 (B.Cu)** | 1 oz | **+VDC pour** | — |

Total ≈ 1.6 mm. A solid **GND plane (In1)** sits directly under the outer signal layers for a
continuous return reference under the analog chain.

- **Do NOT order controlled impedance.** The fastest signal on the board is a ~1 µs Gaussian
  pulse (knee ≈ 300–350 kHz); a quarter-wave in FR-4 at that bandwidth is ~100 m — roughly
  1000× any trace here — so reflections / ringing / mismatch are negligible. Controlled
  impedance would only add cost, lock the stackup, and tighten the design rules for zero
  benefit. Order as a **normal (non-impedance) 4-layer** build.
- **Impedance reference (informational, not ordered):** a 50 Ω single-ended microstrip on an
  outer layer over the adjacent In1 plane (across the 0.2104 mm 7628 prepreg) is ≈ 0.35 mm
  wide on this stack. The `signal` class (0.33 mm) lands ~51–53 Ω over that plane essentially
  by coincidence — keep 0.33 mm for **etch / current robustness**, not for impedance.
