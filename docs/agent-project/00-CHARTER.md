# Project Charter — Agent-Developed Multi-Channel Cremat Amplifier

> **Superseded 2026-07-11** — final board is 213.2 x 334.7 mm, one per Hammond RM1U1908VBK 1U case (slot-through, daisy-chained); THS3491 output buffer (DNP-by-default); socketed Cremat modules (Samtec SS-108-TT-2). See final-board/twelve-channel/ (SESSION_LOG sessions 12-15, ORDERING.md).

This repository is being developed **end-to-end by parallel Claude Code sessions**, run as
if by a team of engineers: each session is a **track** with a scoped job, explicit
**success/failure criteria**, a chronological **session log** (ground truth), and a concise
**session report** (the interface other tracks read). Read this charter +
[01-CONVENTIONS.md](01-CONVENTIONS.md) before doing anything; then read your track's brief.

The end goal is unchanged from the rest of the repo: a **12-channel SiPM charge-sensitive
preamp + Gaussian shaper board** (CR-112 CSP → CR-200 shaper → CR-210 baseline restorer →
output buffer, with a per-channel SiPM bias front-end). This charter rebuilds it
**bottom-up and verified at every stage**, instead of all at once.

> **Why bottom-up:** an earlier pass built the whole 12-channel board quickly, but
> simplified the per-module support circuitry (decoupling, P/Z, buffer) and never validated
> against the module makers' application circuits. This project fixes that: every
> sub-component is **designed, simulated, and BOM'd as a standalone eval board first**, and
> only composed once each piece is proven. Prior work in [hardware/](../../hardware/) and
> [docs/](../) is **prior art / reference**, not the source of truth for this build.

---

## Phases & sub-components

```
 PHASE A — chips-board (standalone eval boards, one dir per sub-component)
   ┌─ csp-cr112/            CR-112 CSP  + the SiPM bias front-end (BIAS_IN→RC+R→Cc→CSP)
   └─ shaper-cr200-cr210/   CR-200 shaper, then sequentially integrate CR-210 (BLR)
 PHASE B — integration (single channel)
   └─ single-channel/       merge CSP + shaper/CR-210, add CFA output buffer (50 Ω out)
 PHASE C — final board
   └─ twelve-channel/       multiply the proven channel ×12, final PCB
```

Each sub-component / phase is worked by **three parallel sibling tracks**: **Design**,
**Simulation**, **Models-BOM**. Everything is for a **single channel** until Phase C.

---

## The 12 tracks

| # | Track ID | Sub-component | Aspect | Brief |
|---|---|---|---|---|
| A1 | `csp-design` | csp-cr112 | Design (schematic→layout) | [briefs/A-csp-cr112.md](briefs/A-csp-cr112.md) |
| A2 | `csp-sim` | csp-cr112 | Simulation (ngspice) | " |
| A3 | `csp-bom` | csp-cr112 | Models-BOM (Digikey) | " |
| A4 | `shaper-design` | shaper-cr200-cr210 | Design | [briefs/A-shaper-cr200-cr210.md](briefs/A-shaper-cr200-cr210.md) |
| A5 | `shaper-sim` | shaper-cr200-cr210 | Simulation | " |
| A6 | `shaper-bom` | shaper-cr200-cr210 | Models-BOM | " |
| B1 | `chan-design` | single-channel | Design (merge + buffer) | [briefs/B-single-channel.md](briefs/B-single-channel.md) |
| B2 | `chan-sim` | single-channel | Simulation (full chain) | " |
| B3 | `chan-bom` | single-channel | Models-BOM (merge + buffer) | " |
| C1 | `board-design` | twelve-channel | Design (×12 + final PCB) | [briefs/C-twelve-channel.md](briefs/C-twelve-channel.md) |
| C2 | `board-bom` | twelve-channel | Models-BOM (×12 final) | " |
| C3 | `board-sim` | twelve-channel | Simulation (system check) | " |

A **Track 0 — Coordinator** (a human or a dedicated session) owns
[02-TRACKS.md](02-TRACKS.md), gates phase transitions, and resolves cross-track conflicts.

---

## Locked decisions (2026-06-25)

| Topic | Decision |
|---|---|
| SiPM bias front-end | **Inside the CSP (csp-cr112) board** as its input stage; sim injects 0.5 pC at the CSP input after the coupling cap |
| SPICE | **ngspice + behavioral models** built from datasheets; ideal **0.5 pC** charge impulse at the CSP input |
| Sub-board I/O / stackup | **Match the final board:** MCX `CONMCX013` coax I/O, 3-pos screw terminal for ±12 V/GND, **4-layer** (GND + power planes) |
| Output buffer | **Current-feedback amp, EL5167-class, 50 Ω back-terminated** output |
| Channel count | Single channel through Phases A–B; ×12 in Phase C |

---

## Dependency graph & gating

```
   A1 csp-design ─┐                         (generic parts -> real parts at A3 gate)
   A2 csp-sim ────┼─► csp-cr112 COMPLETE ──┐
   A3 csp-bom ────┘                         │
                                            ├─► B1/B2/B3 single-channel ─► single-channel COMPLETE ─► C1/C2/C3 twelve-channel ─► DONE
   A4 shaper-design ─┐  M1:CR-200  M2:+CR-210│
   A5 shaper-sim ────┼─► shaper-cr200-cr210 ─┘
   A6 shaper-bom ────┘     COMPLETE
```

Rules:
1. **All Phase-A tracks start immediately** (no blocking). Design + Sim use **generic
   parts** (e.g. "10 kΩ"); Models-BOM finds the **real** parts in parallel.
2. **Real-parts gate (per sub-component):** when the Models-BOM track publishes its parts
   report, the Design track swaps generics → chosen real parts and re-runs ERC/DRC; the Sim
   track updates any value-sensitive models. (See "real-parts swap" in
   [01-CONVENTIONS.md](01-CONVENTIONS.md).)
3. **Shaper sequential milestone:** A4/A5/A6 first complete **M1 = CR-200 only**, then
   **M2 = CR-200 + CR-210** (BLR added, with the 0R bypass). The sub-component is COMPLETE
   only after M2.
4. A sub-component is **COMPLETE** when its three tracks are each at their success criteria
   **and mutually consistent** (design BOM == models BOM; sim used the design's topology).
   The Coordinator marks it complete in [02-TRACKS.md](02-TRACKS.md).
5. **Phase B** starts only when **both** Phase-A sub-components are COMPLETE.
   **Phase C** starts only when **single-channel** is COMPLETE.

---

## What "done" means for the whole project

A fabricated-ready 12-channel board whose single-channel building blocks were each
**simulated to meet their success criteria** and **BOM'd with real, in-stock, economical
Digikey parts**, with the full provenance in session logs and the integration story in
session reports.
