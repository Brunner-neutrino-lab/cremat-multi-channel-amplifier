# PCB Design Rules

Net classes, trace widths, clearances, and HV considerations for the 12-channel amplifier.
Modeled on the reference board and on `ets-breakout`'s net-class scheme, with the addition
of an explicit **HV bias** class because this board now carries the detector bias rail.

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
the coax-driven nets. Apply controlled impedance only if `OUT` runs are long.

---

## HV clearance / creepage (bias rail)

The detector bias sets the minimum spacing on the `hv_bias` class. **Confirm the actual
SiPM bias voltage** ([session-report.md](../session-report.md)) and apply at least:

| Bias voltage | Min clearance/creepage (uncoated FR4, guide) |
|---|---|
| ≤ 50 V | 0.5 mm |
| ≤ 100 V | 1.0 mm |
| ≤ 250 V | 2.0 mm |

These are conservative starting points (IPC-2221 B internal/external, no conformal
coating). Tighten only with justification. Enforce via the `hv_bias` clearance and KiCad's
**creepage** DRC rule (treat creepage/clearance violations as **errors**, as the reference
project does).

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

- Start from the fab's default **4-layer 1.6 mm** stack (sig / GND / GND or power / sig),
  as `ets-breakout` did, for a continuous ground reference under the analog chain.
- A 2-layer board is acceptable if density allows, but a ground plane under the front-end
  and output is strongly preferred for noise.
- If `OUT` is run as controlled impedance, **order as controlled impedance** so the fab
  tunes trace width to their measured stack (per `ets-breakout`'s note).
