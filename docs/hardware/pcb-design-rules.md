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
| Track width | ~0.33 mm signal (etch / current robustness; **not** impedance-tuned — the outer nets are grounded coplanar, see Stackup) |
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

### Why four layers (it is **not** for impedance control)

Asked directly, since 2-layer is cheaper and faster: the fourth layer here buys **plane-based
power/return distribution**, not controlled impedance. Impedance is explicitly *not* controlled on
this board — see the bullets below the table.

The as-routed board makes the case numerically. Of 1290 pads, **464 are `GND` / `+VDC` / `-VDC`**
(364 / 50 / 50), yet those three nets account for only **490 mm of track in total** across a
213 × 335 mm board — because each of those pads drops through a via straight onto its plane
(240 GND vias, 50 per rail). **A 2-layer build has to route all 464 of those connections as
tracks**, in the same two layers that already carry 12 analog signal chains and 12 HV bias nets.

Three reasons that matters here specifically:

1. **The return path is the signal.** A CSP is a charge integrator: it sums *every* current
   arriving at its input node. Return current from a neighbouring channel flowing through shared
   ground metal appears at that input as charge — i.e. as a pulse indistinguishable from a real
   SiPM event. A solid, unbroken **GND plane (In1) directly beneath the analog chain** gives each
   channel a low-impedance image return under its own trace, so 12 channels do not share return
   metal. On 2 layers the bottom-side ground must be sliced by rail routing; every slice forces a
   detour and re-introduces exactly the shared impedance we are trying to avoid. With 12 channels
   on one board, inter-channel crosstalk is the dominant systematic risk.
2. **The rails are bipolar and go everywhere.** Both `+VDC` **and** `-VDC` must reach all 12
   channels. That is two more distribution networks on top of ground. Two copper layers cannot
   hold GND + two rails + 12 signal chains + 12 HV bias nets and leave the ground solid — there
   is no arrangement where it survives.
3. **HV bias competes for the same space.** The 12 bias nets are on the `hv_bias` class
   (0.6 mm clearance, 0.4 mm track). Their creepage keep-outs consume routing channels on the
   outer layers; taking away two layers makes the crowding worse precisely where clearance is a
   safety rule rather than a preference.

Cost check: at this board size and a small build quantity, JLC's 4-layer adder is small in
absolute terms and far below the cost of one respin. The 4-layer version is already routed and
DRC-clean, so the 4→2 conversion would also be a full re-layout, not a stackup swap.

### The ordered stack

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
- **The outer traces are grounded coplanar (GCPW), not microstrip.** Every F.Cu signal runs
  inside the GND pour *and* over the In1 GND plane, so the coplanar side grounds add capacitance
  and pull the impedance **below** a microstrip of the same width — a "microstrip 50 Ω" width
  would read < 50 Ω here. Because we do **not** order controlled impedance (slow, sub-MHz analog
  — see above), the exact width is immaterial: `signal` stays **0.33 mm for etch / current
  robustness**, not for a target impedance. If impedance ever mattered, model it as **GCPW**
  (trace width **and** the coplanar gap, plus the plane below) and **order controlled impedance**
  so JLC tunes it to their etched stack — do not hand them a bare microstrip width, which ignores
  the surrounding ground.

---

## Copper zones and pad connection (thermal relief)

Four zones, filled as a separate pass by
[`fill_zones.py`](../../final-board/twelve-channel/design/fill_zones.py) (an in-memory
`ZONE_FILLER.Fill()` during board construction segfaults headless):

| Layer | Net | Priority | Filled area |
|---|---|---|---|
| `F.Cu` | `GND` | 2 | 53 295 mm² |
| `GND.Cu` (In1) | `GND` | 0 | 65 389 mm² |
| `PWR.Cu` (In2) | `-VDC` | 0 | 63 166 mm² |
| `B.Cu` | `+VDC` | 1 | 65 363 mm² |

**Pad connection = `THERMAL` (spoke relief), board-wide.** Gap 0.5 mm, spoke width 0.5 mm.

This was a **fix**, not a default: the zones had been left on `ZONE_CONNECTION_NONE`, which
isolates the pour from *every* pad. The GND pour then contributed nothing to the ground return —
all GND connectivity went via tracks and vias, so DRC still reported 0 unconnected and the defect
never surfaced in any automated check. Switching to `THERMAL` both restores the pad-to-pour ties
and keeps them solderable.

**Why thermal spokes rather than solid (`FULL`) connections:** **218 GND pads on this board are
hand-soldered** — 120 SIP-8 socket pins for the Cremat modules, 96 MCX shield pads, and the
2-pin screw terminal (the board reports 122 through-hole GND pads; the MCX shields are SMD-attribute
but still hand-assembled). Soldering those directly into a 65 000 mm² copper plane wicks heat away
faster than a hand iron can replace it, giving cold joints and lifted pads. Spokes are the standard
answer and cost essentially nothing here:

- **Current:** rail draw is milliamps per channel; a 0.5 mm spoke is orders of magnitude more
  copper than needed.
- **Inductance:** four spokes add ~1–2 nH. At a ~350 kHz knee that is <10 µΩ of reactance —
  irrelevant. (On a fast digital board this trade would go the other way.)

Regenerate with:

```bash
"C:/Program Files/KiCad/10.0/bin/python.exe" final-board/twelve-channel/design/fill_zones.py
```

`fill_zones.py` first checks that the `.kicad_pro` still holds its netclasses and restores them if
a GUI save has flattened the file — otherwise the fill silently ignores the `hv_bias` clearance and
a subsequent DRC passes vacuously.
