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
                                     (AC)   CSP        shaper     BLR(opt)   THS3491    (50 Ω
                                                       +P/Z trim  0R-byp.    DNP-def     coax)
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

> **Looking for the actual orderable board? It is [`final-board/twelve-channel/`](final-board/twelve-channel/).**
> Reviewing it → [REVIEW.md](final-board/twelve-channel/REVIEW.md) · ordering it →
> [ORDERING.md](final-board/twelve-channel/ORDERING.md) · resuming work on it →
> [HANDOFF.md](final-board/twelve-channel/HANDOFF.md).

| Doc | Contents |
|-----|----------|
| **[final-board/twelve-channel/REVIEW.md](final-board/twelve-channel/REVIEW.md)** | **Design-review pack** — verified state, the acceptance gate, and what needs human eyes before ordering |
| [final-board/twelve-channel/INTERFACE.md](final-board/twelve-channel/INTERFACE.md) | The final board: layout intent, connector map, stackup, per-channel cell |
| [final-board/twelve-channel/ORDERING.md](final-board/twelve-channel/ORDERING.md) | Buy sheet — JLCPCB (fab + SMT) + DigiKey (hand parts), quantities, upload steps |
| [final-board/twelve-channel/HANDOFF.md](final-board/twelve-channel/HANDOFF.md) | Resume on a new machine: toolchain, paths, regeneration commands, gotchas |
| [docs/agent-project/](docs/agent-project/) | **Parallel agent-developed build** — bottom-up (per-chip eval boards → single channel → 12-ch board), 12 tracks with briefs, conventions, session-log/report protocol. **Start at [docs/agent-project/README.md](docs/agent-project/README.md).** *(Historical: intermediate figures here — e.g. bias ≤ 60 V, board 235.1 × 264.1 mm — are superseded by the final board.)* |
| [docs/development-plan.md](docs/development-plan.md) | Earlier work-track breakdown (the rapid top-down build in `hardware/`); superseded by the agent-project for the final design |
| [docs/architecture.md](docs/architecture.md) | System/board block diagram, channel signal chain, design partitioning |
| [docs/modifications.md](docs/modifications.md) | **The four changes vs. `cremat-x6-board`, with rationale + the optional/DNP jumper scheme** |
| [docs/hardware/channel.md](docs/hardware/channel.md) | Per-channel circuit: bias front-end, AC/DC coupling, CSP/shaper/BLR/buffer, jumpers |
| [docs/hardware/circuit-design.md](docs/hardware/circuit-design.md) | **Front-end values for the Hamamatsu VUV4** — bias filter, coupling, polarity, CR-112 gain/range |
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
  **Phase 1 is built:** [hardware/](hardware/) has the `kicad-cli`-validated symbol library
  ([hardware/lib/cremat.kicad_sym](hardware/lib/cremat.kicad_sym)), the project + net classes,
  lib tables, the fielded BOM ([hardware/bom/](hardware/bom/)), the golden per-channel netlist
  ([hardware/integration-notes.md](hardware/integration-notes.md)), and the mechanical spec
  ([hardware/mechanical.md](hardware/mechanical.md)). **Track 5 (schematic) is done** — the
  12-channel hierarchical schematic is generated by [hardware/gen_sch.py](hardware/gen_sch.py)
  and is **ERC-clean (0 errors)** with a netlist that matches the spec node-by-node. **Layout
  + fab (Tracks 6–7)** remain — guide: [hardware/BUILD-IN-KICAD.md](hardware/BUILD-IN-KICAD.md).
- **CR-210 pinout + bypass-jumper integration: confirmed** against Cremat's open-source
  [CR-160-R7](reference/cremat-CR-160-R7/) board (pin 2 = GND vs the CR-200's P/Z).
- **Build decisions resolved** (D1–D6, see the plan): bias ≤ 70 V (100 V parts); all
  per-channel I/O is **MCX `CONMCX013`** (`BIAS_IN`, `SIPM`, `TEST`, `OUT_50` — **`BIAS_IN` is
  per-channel**, 4/channel → 48 MCX/board); modules **CR-112** + **CR-200-1µs** (+ CR-210),
  **socketed** on Samtec SS-108-TT-2 SIP-8 sockets (36/board), the modules plug in; rack-mounted,
  **one board per 1U Hammond RM1U1908VBK case, boards daisy-chained**; first build = Full.
- **Front-end designed for the Hamamatsu VUV4** (S13370, 45–55 V, ≈220 fC/V, Cdet≈1.28 nF):
  bias filter `Rf1=Rf2=10 kΩ`, `Cf=100 nF`, `Cc=0.22 µF`; cathode-on-node +45–55 V; CR-112
  ([docs/hardware/circuit-design.md](docs/hardware/circuit-design.md)).
- **Enclosure (D5):** **Hammond RM1U1908VBK** (1U, vented), **one board per case**; boards are
  **daisy-chained** (each board in its own 1U box, `J_DAISY` passes the raw rails box-to-box).
  Board outline **213.2 × 334.7 mm**; it mounts on standoffs off the bottom cover and passes
  **through a ~340 × 7 mm milled slot** in each front/rear panel (slot-through, protruding ~5 mm;
  the MCX faces sit ~8.6 mm proud). Usable interior height 40.09 mm; tall parts must clear it.
  Inputs (`BIAS_IN`+`SIPM`) on one long edge, outputs (`OUT_50`) on the other (24 MCX per long edge).
- **Open items**: final jack/outline placement (Track 4), and bench-verify (CR-112 output
  sign, warm/cold OV offset, single-p.e. range, P/Z trim). Power terminals are resolved —
  two 3-pos 5.08 mm Phoenix screw terminals, `J_PWR` (supply in) + `J_DAISY` (raw rails out).
