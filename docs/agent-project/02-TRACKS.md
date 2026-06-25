# Track Index & Status Board

The Coordinator (Track 0) keeps this current. Each track updates its **own row** when its
state changes (and keeps its `SESSION_REPORT.md` current). Status: `not-started` →
`in-progress` → `blocked(<on>)` → `criteria-met` → `COMPLETE` (Coordinator sets COMPLETE).

## Phase A — chips-board

| Track | Dir | Status | Milestone | Report |
|---|---|---|---|---|
| A1 csp-design | `chips-board/csp-cr112/design/` | not-started | generic → real | — |
| A2 csp-sim | `chips-board/csp-cr112/sim/` | not-started | 0.5 pC response | — |
| A3 csp-bom | `chips-board/csp-cr112/models-bom/` | not-started | real parts sourced | — |
| A4 shaper-design | `chips-board/shaper-cr200-cr210/design/` | not-started | M1 CR-200 → M2 +CR-210 | — |
| A5 shaper-sim | `chips-board/shaper-cr200-cr210/sim/` | not-started | M1 → M2 | — |
| A6 shaper-bom | `chips-board/shaper-cr200-cr210/models-bom/` | not-started | M1 → M2 | — |

**csp-cr112 COMPLETE:** ☐  **shaper-cr200-cr210 COMPLETE:** ☐

## Phase B — single-channel integration (gates on both Phase-A sub-components COMPLETE)

| Track | Dir | Status | Report |
|---|---|---|---|
| B1 chan-design | `integration/single-channel/design/` | not-started | — |
| B2 chan-sim | `integration/single-channel/sim/` | not-started | — |
| B3 chan-bom | `integration/single-channel/models-bom/` | not-started | — |

**single-channel COMPLETE:** ☐

## Phase C — twelve-channel final board (gates on single-channel COMPLETE)

| Track | Dir | Status | Report |
|---|---|---|---|
| C1 board-design | `final-board/twelve-channel/design/` | not-started | — |
| C2 board-bom | `final-board/twelve-channel/models-bom/` | not-started | — |
| C3 board-sim | `final-board/twelve-channel/sim/` | not-started | — |

**PROJECT DONE:** ☐

---

## Coordinator gate checklist (per sub-component COMPLETE)

- [ ] Design: ERC 0, DRC 0 on the real-parts board; `INTERFACE.md` current.
- [ ] Sim: success criteria met, plots in report, used the design's actual topology.
- [ ] Models-BOM: every part real/in-stock/sourced; BOM == design BOM (identical MPNs).
- [ ] The three reports are mutually consistent. Then mark COMPLETE here + announce.
