# Track Index & Status Board

The Coordinator (Track 0) keeps this current. Each track updates its **own row** when its
state changes (and keeps its `SESSION_REPORT.md` current). Status: `not-started` →
`in-progress` → `blocked(<on>)` → `criteria-met` → `COMPLETE` (Coordinator sets COMPLETE).

## Phase A — chips-board

| Track | Dir | Status | Milestone | Report |
|---|---|---|---|---|
| A1 csp-design | `chips-board/csp-cr112/design/` | criteria-met | real parts, ERC 0 / DRC 0/0/0 | [report](../../chips-board/csp-cr112/design/SESSION_REPORT.md) |
| A2 csp-sim | `chips-board/csp-cr112/sim/` | criteria-met | 0.5 pC → CSP_OUT 6.66 mV | [report](../../chips-board/csp-cr112/sim/SESSION_REPORT.md) |
| A3 csp-bom | `chips-board/csp-cr112/models-bom/` | criteria-met | sourced, == design BOM | [report](../../chips-board/csp-cr112/models-bom/SESSION_REPORT.md) |
| A4 shaper-design | `chips-board/shaper-cr200-cr210/design/` | criteria-met | M1 + M2 ERC 0 / DRC 0/0/0 | [report](../../chips-board/shaper-cr200-cr210/design/SESSION_REPORT.md) |
| A5 shaper-sim | `chips-board/shaper-cr200-cr210/sim/` | criteria-met | M1 FWHM 2.5 µs, M2 BLR −98% droop | [report](../../chips-board/shaper-cr200-cr210/sim/SESSION_REPORT.md) |
| A6 shaper-bom | `chips-board/shaper-cr200-cr210/models-bom/` | criteria-met | sourced, == design BOM (incl DNP) | [report](../../chips-board/shaper-cr200-cr210/models-bom/SESSION_REPORT.md) |

**csp-cr112 COMPLETE:** ☑ (2026-06-25)  **shaper-cr200-cr210 COMPLETE:** ☑ (2026-06-25)

> **Coordinator gate (2026-06-25):** All 6 Phase-A tracks at criteria-met and mutually consistent after the real-parts gate (Round 2) + two cross-track reconciliations: (1) csp BOM gained the 47 Ω test-inject resistor R5 that design had; (2) shaper dropped a 100 kΩ that A6 mis-attributed as a CR-200 pole-zero — per `reference/cremat-CR-160-R7/CR-160-R7.net` (net code 10) it belongs to the excluded MAX4649/SW1 buffer section; the CR-200 P/Z is the 200 kΩ trim alone. Sim real-parts impact assessed "no change" (gain/decay fixed inside the sealed Cremat modules; shaper P/Z covered by the adjustable trim). Both sub-components ready for COMPLETE.

## Phase B — single-channel integration (gates on both Phase-A sub-components COMPLETE)

| Track | Dir | Status | Report |
|---|---|---|---|
| B1 chan-design | `integration/single-channel/design/` | in-progress | — |
| B2 chan-sim | `integration/single-channel/sim/` | in-progress | — |
| B3 chan-bom | `integration/single-channel/models-bom/` | in-progress | — |

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
