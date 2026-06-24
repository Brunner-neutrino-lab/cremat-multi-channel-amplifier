# System Architecture

## Purpose

The Multi-channel Cremat Amplifier is a **12-channel analog front-end** for Silicon
Photomultipliers (SiPMs) and similar charge-producing detectors. Each channel:

1. **Biases** its detector from its own per-channel `BIAS_IN` jack through an optional
   filter, and
2. **Amplifies and shapes** the detector's charge pulses with the Cremat module chain
   (charge-sensitive preamp → Gaussian shaper → optional baseline restorer → buffer),
   presenting a 50 Ω-driven pulse at a per-channel coax output.

It is a remake of the Brunner-lab **6-channel Cremat CSP & Shaper board**
(`reference/cremat-x6-board/`, *"6 Channel Cremat CSP & Shaper Board"*, McGill Physics /
Brunner Neutrino Lab, 2023) with the four modifications listed in
[modifications.md](modifications.md). Unlike the reference board — which took an already
externally-biased detector signal in on coax — this board **biases the detector itself**.

---

## Board Block Diagram

```
        +Vs  -Vs  GND
         │    │    │
   ┌─────┴────┴────┴───────────────────────────────────────────────────────────┐
   │  Power entry + bulk decoupling  (±Vs, GND distributed to all modules)       │
   │                                                                             │
   │   ┌──────────────── Channel 1 ─────────────────┐   BIAS_IN1 ◄─(bias supply) │
   │   │ bias filter → node → SiPM (DC) / amp (AC)   │   SIPM1   ──►(to detector) │
   │   │ CR-11X → CR-200-1µs → [CR-210] → buffer     │   OUT1    ──►(to DAQ/coax) │
   │   └─────────────────────────────────────────────┘                           │
   │   ┌──────────────── Channel 2 ─────────────────┐   BIAS_IN2 / SIPM2 / OUT2   │
   │   │  … identical …                              │                            │
   │   └─────────────────────────────────────────────┘                           │
   │            ⋮  (12 identical channels)             BIAS_IN12 / SIPM12 / OUT12 │
   └───────────────────────────────────────────────────────────────────────────┘
        Every channel has its own 3 MCX jacks: BIAS_IN, SIPM, OUT (36 MCX total).
```

All 12 channels are **electrically identical** and instantiated from one hierarchical
sheet, exactly as the reference board instantiates `channel.kicad_sch` six times. The
board adds, per channel, the bias front-end (with its own `BIAS_IN` jack) and the CR-210
stage. **`BIAS_IN` is per-channel** — there is no shared on-board bias rail; the bias
supply is fanned to the 12 `BIAS_IN` jacks externally, or each channel is biased on its own.

---

## Per-channel Signal Chain

```
                          bias filter (optional, 0R-bypassable)
 BIAS_IN ───►  Rf1 ──┬── Rf2 ──►──┐
                     │            │  FRONT-END NODE  (node "FE")
                    Cf            ├──────────────────► SIPM connector
                     │            │                    (DC-coupled: reverse-biases detector)
                    GND           │
                                  └─► Cc ─► [ CR-11X ] ─► [ CR-200-X ] ─► [ CR-210 ] ─► [ buffer ] ─► OUT
                                     AC      charge-       Gaussian        baseline      EL5167 /     50 Ω
                                     coupling sensitive     shaper          restorer      LM7321       coax
                                              preamp        (+P/Z trim)     (optional)    (+gain trim)
```

| Stage | Part (reference board) | Function | New? |
|---|---|---|---|
| Bias filter | `Rf1`, `Cf`, `Rf2` (0805) | Low-pass + isolate the SiPM bias from supply noise | **New** |
| Front-end node | — | Shared by SiPM (DC) and amplifier (AC) | **New** |
| AC coupling | `Cc` (HV cap, e.g. 0.22 µF 100 V) | Block DC bias, pass the current pulse to the preamp | (reference input cap) |
| Charge-sensitive preamp | Cremat **CR-112** (CR-113 on ref.) | Integrate detector charge → voltage step | existing |
| Shaping amplifier | Cremat **CR-200-1µs** | Gaussian pulse shaping (1 µs); pole-zero trimmed | existing |
| Baseline restorer | Cremat **CR-210** | Hold baseline at ground at high rate | **New, optional** |
| Output buffer | EL5167 / LM7321 + `49.9R` series | Drive 50 Ω coax; gain/offset trims | existing |

See [hardware/channel.md](hardware/channel.md) for component-level detail and the bypass
jumper scheme.

---

## Design Partitioning

### Why one repeated channel cell?
12 channels of identical analog electronics is exactly the case KiCad's hierarchical
sheets handle well. One reviewed, DRC-clean channel cell instantiated 12× guarantees the
channels match and keeps the schematic reviewable — the same pattern the reference board
uses for 6 channels and that `ets-breakout` uses for 24.

### Why an on-board bias front-end?
The reference board amplified an already-biased signal arriving on coax. Folding the bias
network onto the board means the **detector connects with one cable** (the on-board
bias-tee both biases the SiPM and reads it out on the `SIPM` jack), removes an external
bias-tee, and lets the bias filter sit right at the detector node where it does the most
good. The penalty is that the board now carries HV (the 12 per-channel `BIAS_IN` nets,
≤ 60 V) — handled by net-class spacing and 100 V-rated parts (see
[pcb-design-rules.md](hardware/pcb-design-rules.md)).

### Why everything optional is a jumper, not a switch
Populate-or-bypass via 0R / solder jumpers (resolved by DNP at assembly) is zero-cost,
zero-failure, and needs no control logic. Each build is a fixed configuration; there is no
runtime switching. This matches the reference board's existing use of `SolderJumper`,
`Jumper_2_Open`, and `Jumper_3_Open` parts.

---

## Power and Bias Domains

| Domain | Nets | Source | Notes |
|---|---|---|---|
| Analog supply | `+VDC` / `-VDC` (±Vs), `GND` | External dual rail (Cremat-style, typ. ±12 V) | Per-module + bulk decoupling; **shared** across channels |
| Detector bias | `BIAS_IN<n>` (HV, ≤ 60 V) | External bias supply, fanned out | **Per-channel** jack → per-channel filter → SiPM. No shared on-board rail. |

The analog supply and the detector bias are **independent**. `GND` is the common
reference for both. The 12 `BIAS_IN<n>` nets are the only HV nets (≤ 60 V; parts rated
100 V) and each is kept on its own routing with widened creepage near its filter.

---

## What this board does *not* do

- **No multiplexing / no switching / no microcontroller.** Every channel is always live;
  there is no firmware (contrast the `ets-breakout`/IV-pulse-mux system, which is a
  relay mux with an Arduino). This is a parallel analog amplifier array.
- **No *on-board* per-channel bias adjust.** Each channel has its own `BIAS_IN` jack, so
  per-channel bias *is* possible by driving each jack separately — but the board itself
  does no on-board trimming/regulation of the bias (the optional filter only low-passes it).
