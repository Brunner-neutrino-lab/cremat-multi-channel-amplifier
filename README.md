# Multi-channel Cremat amplifier

A **12-channel** SiPM charge-sensitive preamplifier + Gaussian shaper board, derived
from the Brunner-lab **6-channel Cremat CSP & Shaper board**
([`cremat-x6-board`](reference/cremat-x6-board/)) with four deliberate changes:

1. **12 channels** (was 6).
2. **0805 passives wherever possible** (was a mix of larger imperial sizes).
3. **A Cremat CR-210 baseline restorer on every channel**, *optional* — populate the
   module **or** an 0805 `0R` jumper to bypass it.
4. **An on-board SiPM bias front-end on every channel**: a `BIAS_IN` feed through an
   *optional* RC-in-series-with-R **bias filter**, then a node shared by the **SiPM**
   (DC-coupled) and the **amplifier** (AC-coupled). The detector and the amplifier hang
   off the same biased node.

> This repository is the **design specification + build documentation** for the new
> board. It is structured to mirror the Brunner-lab **`ets-breakout`** project, which is
> included as the *reference for how to document and build*. The KiCad implementation is
> the next track (see [Status](#status)).

## What each channel does (new signal chain)

```
                          bias filter (optional, 0R-bypassable)
 BIAS_IN ───►  Rf1 ──┬── Rf2 ──►──┐
                     │            │   FRONT-END NODE
                    Cf            ├─────────────► SIPM   (DC-coupled: reverse-biases the detector)
                     │            │
                    GND           └─► Cc ─► CR-11X ─► CR-200-X ─► [CR-210] ─► buffer ─► OUTPUT
                                     (AC)   CSP        shaper     BLR(opt)   EL5167/    (50 Ω
                                                       +P/Z trim  0R-byp.    LM7321      coax)
```

- **`BIAS_IN` → bias filter → front-end node.** "RC in series with R": series `Rf1`,
  shunt `Cf` to ground, series `Rf2`. The whole filter is bypassable with 0R jumpers.
- **Front-end node → `SIPM` (DC-coupled).** The filtered bias voltage reverse-biases the
  detector directly.
- **Front-end node → `Cc` → amplifier (AC-coupled).** Only the SiPM's fast current pulse
  reaches the charge-sensitive preamp; the DC bias is blocked by `Cc`.
- **CR-11X → CR-200-X → CR-210 → buffer → output**, the classic Cremat chain. The CR-210
  baseline restorer is new and optional.

Full detail: [docs/hardware/channel.md](docs/hardware/channel.md).

## Documentation map

| Doc | Contents |
|-----|----------|
| [docs/development-plan.md](docs/development-plan.md) | **Work-track breakdown** (parts/models/BOM, circuit, integration, mechanical → schematic → layout → fab), dependencies, decisions needed |
| [docs/architecture.md](docs/architecture.md) | System/board block diagram, channel signal chain, design partitioning |
| [docs/modifications.md](docs/modifications.md) | **The four changes vs. `cremat-x6-board`, with rationale + the optional/DNP jumper scheme** |
| [docs/hardware/channel.md](docs/hardware/channel.md) | Per-channel circuit: bias front-end, AC/DC coupling, CSP/shaper/BLR/buffer, jumpers |
| [docs/hardware/board.md](docs/hardware/board.md) | 12-channel board: power distribution, connectors, layout intent |
| [docs/hardware/bom.md](docs/hardware/bom.md) | 0805 strategy, Cremat modules, optional-population (DNP) variants |
| [docs/hardware/pcb-design-rules.md](docs/hardware/pcb-design-rules.md) | Net classes, trace widths, HV creepage, guard rings |
| [docs/hardware/component-libraries.md](docs/hardware/component-libraries.md) | Symbols + footprints to provide (Cremat SIP-8, 0805 passives, jumpers) |
| [docs/fabrication/fabrication-guide.md](docs/fabrication/fabrication-guide.md) | Fab output generation, assembly, population variants |
| [docs/operation/user-guide.md](docs/operation/user-guide.md) | Power-up, biasing SiPMs, choosing populate/bypass options |
| [docs/session-report.md](docs/session-report.md) | Integration/manager handoff: tracks, decisions, what's done vs. open |

## References (git submodules)

| Path | Repo | Role |
|------|------|------|
| [reference/cremat-x6-board/](reference/cremat-x6-board/) | `Brunner-neutrino-lab/cremat-x6-board` | **What we're building** — the 6-channel CR-110/CR-200 eval board this design derives from |
| [reference/ets-breakout/](reference/ets-breakout/) | `Brunner-neutrino-lab/ets-breakout` | **How we build/document** — KiCad-from-source-of-truth pipeline + doc structure to imitate |
| [reference/cremat-CR-160-R7/](reference/cremat-CR-160-R7/) | `CrematInc/CR-160-R7` | **CR-210 pinout + integration** — Cremat's open-source CR-200/CR-210 eval board (the CR-210 bypass-jumper scheme) |
| [reference/cremat-CR-150-R5/](reference/cremat-CR-150-R5/) | `CrematInc/CR-150-R5` | **CR-11X reference** — Cremat's open-source CSP eval board (source of the CR-11X symbol) |

Clone with submodules:

```
git clone --recurse-submodules <this-repo>
# or, in an existing clone:
git submodule update --init --recursive
```

## Status

- **Specification + documentation: complete.** This repo fully specifies the modified
  12-channel board.
- **Development is divided into tracks** — see [docs/development-plan.md](docs/development-plan.md).
  Phase 1 (parts/models/BOM, circuit, integration, mechanical) runs in parallel; Phase 2
  (schematic → layout → fab) is serial. KiCad implementation has not started.
- **CR-210 pinout + bypass-jumper integration: confirmed** against Cremat's open-source
  [CR-160-R7](reference/cremat-CR-160-R7/) board (pin 2 = GND vs the CR-200's P/Z).
- **Build decisions resolved** (D1–D6, see the plan): bias ≤ 60 V (100 V parts); all
  per-channel I/O is **MCX `CONMCX013`** (`BIAS_IN`, `SIPM`, `OUT` — **`BIAS_IN` is
  per-channel**, 36 MCX/board); modules **CR-112** + **CR-200-1µs** (+ CR-210); rack-mounted,
  two boards per box; first build = Full.
- **Open items**: bias-filter R/C values and SiPM terminal polarity (Track 2/3 — need the
  detector's bias current/capacitance), and the rack box's exact internal dimensions (D5).
