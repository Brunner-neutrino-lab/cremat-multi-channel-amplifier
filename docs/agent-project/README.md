# Agent-developed build — start here

This directory orchestrates the **parallel, agent-developed** rebuild of the amplifier
(bottom-up: per-chip eval boards → single channel → 12-channel board). Run sessions in
danger/bypass mode.

## Read order
1. [00-CHARTER.md](00-CHARTER.md) — phases, the 12 tracks, dependency graph, gating, locked decisions.
2. [01-CONVENTIONS.md](01-CONVENTIONS.md) — directory layout, log/report protocol, interface contracts, toolchain, **SPICE rules (use Cremat's official models)**, real-parts gate, sourcing rules, success-criteria philosophy.
3. Your **brief** (below). 4. The reports/`INTERFACE.md` your brief says to consume.

## How to assign a session
Give the new session this (fill in the track):

> You are **track `<ID>`** of the agent-developed Cremat amplifier project. Read
> `docs/agent-project/00-CHARTER.md`, `docs/agent-project/01-CONVENTIONS.md`, and your brief
> `docs/agent-project/briefs/<brief>.md`. Work only in your track subdir, keep
> `SESSION_LOG.md` (ground truth) + `SESSION_REPORT.md` (summary) current from the templates,
> update your row in `docs/agent-project/02-TRACKS.md`, define your success/failure criteria
> first, then execute autonomously. Honor the gates in the charter.

| Track | Brief | Subdir |
|---|---|---|
| A1 csp-design / A2 csp-sim / A3 csp-bom | [briefs/A-csp-cr112.md](briefs/A-csp-cr112.md) | `chips-board/csp-cr112/{design,sim,models-bom}/` |
| A4/A5/A6 shaper {design,sim,bom} | [briefs/A-shaper-cr200-cr210.md](briefs/A-shaper-cr200-cr210.md) | `chips-board/shaper-cr200-cr210/...` |
| B1/B2/B3 single-channel {design,sim,bom} | [briefs/B-single-channel.md](briefs/B-single-channel.md) | `integration/single-channel/...` |
| C1/C2/C3 twelve-channel {design,bom,sim} | [briefs/C-twelve-channel.md](briefs/C-twelve-channel.md) | `final-board/twelve-channel/...` |

Phase A (6 tracks) can all start now. Phase B gates on both Phase-A sub-components COMPLETE;
Phase C gates on single-channel COMPLETE. The **Coordinator** owns
[02-TRACKS.md](02-TRACKS.md) and marks COMPLETE.

## Prior art (read-only)
`reference/` (incl. Cremat's `cremat-CR-150-R5`, `cremat-CR-160-R7` eval boards), and the
earlier rapid build in `hardware/` + `docs/` — reuse the toolchain/scripts, but this
bottom-up build is the source of truth for the final design.
