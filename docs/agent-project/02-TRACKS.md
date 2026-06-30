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
| B1 chan-design | `integration/single-channel/design/` | criteria-met | ERC 0 / DRC 0/0/0, THS3491 buffer @ 976 Ω | [report](../../integration/single-channel/design/SESSION_REPORT.md) |
| B2 chan-sim | `integration/single-channel/sim/` | criteria-met | OUT_50 67 mV @ 0.5 pC, TI official model | [report](../../integration/single-channel/sim/SESSION_REPORT.md) |
| B3 chan-bom | `integration/single-channel/models-bom/` | criteria-met | 48 refs / 19 MPNs, == design BOM | [report](../../integration/single-channel/models-bom/SESSION_REPORT.md) |

**single-channel COMPLETE:** ☑ (2026-06-28)

> **Coordinator gate (2026-06-28):** single-channel signed off after an independent re-run of the gates (not agent self-report): ERC 0, DRC 0 violations / 0 unconnected on the routed real-parts board; design BOM == models BOM (THS3491 + Rf=Rg=976 Ω, the TI datasheet G=+2 / B2-validated value). Buffer decision: **EL5167 (locked) was unusable** (±6 V part on ±12 V rails + obsolete) → replaced with **TI THS3491** HV-CFA (user-approved), runs direct on ±12 V. CR-210 polarity resolved as a documented detector charge-sign constraint (no added hardware). Known cosmetic: schematic-parity *warnings* (footprint lib-nickname + MPN field not propagated; +4 mounting holes) are a gen-pipeline artifact present on the Phase-A boards too — **Phase C must produce a parity-clean final fab board.**

## Phase C — twelve-channel final board (gates on single-channel COMPLETE)

| Track | Dir | Status | Report |
|---|---|---|---|
| C1 board-design | `final-board/twelve-channel/design/` | criteria-met | ERC 0 / DRC 0/0/0, parity 0, fab package | [report](../../final-board/twelve-channel/design/SESSION_REPORT.md) |
| C2 board-bom | `final-board/twelve-channel/models-bom/` | criteria-met | final BOM == board, $2,847 q1 FULL | [report](../../final-board/twelve-channel/models-bom/SESSION_REPORT.md) |
| C3 board-sim | `final-board/twelve-channel/sim/` | criteria-met | one-ch unchanged ×12; rails/bulk OK | [report](../../final-board/twelve-channel/sim/SESSION_REPORT.md) |

**PROJECT DONE:** ◑ board fab-ready & independently verified (2026-06-29) — final user sign-off pending visual schematic audit

> **Coordinator gate (2026-06-29) — tile-and-replicate re-architecture:** Per user direction the PCB layout was rebuilt from "autoroute all 12 channels" to **route one channel tile → clone ×12 → route only the shared power** (far less routing; identical, matched channels). Independently verified (re-run, not agent self-report): ERC 0; DRC **0 errors / 0 unconnected / 0 schematic-parity** (with `--severity-warning`); **all 12 channels bit-identical** (exact integer-nm: same parts/X/relative-Y/rotation, 173 tracks + 29 vias each, exact 21.0 mm pitch); **48 MCX cutouts now on Edge.Cuts** (196-segment gerber — the earlier "cutouts parked on Dwgs.User" blocker is resolved by construction). Edge-clearance DRU exemption is narrowly scoped to the MCX shield pad only (creepage/clearance/hole rules still enforced). Board **235.1 × 264.1 mm** (deeper-enclosure decision). design BOM == C2 BOM unchanged. **Bias confirmed ≤60 V** (user, 2026-06-29) → closes CLAUDE.md iron-rule-#5 HV item; 0.6 mm hv_bias clearance + 100 V caps adequate. Earlier decisions stand: buffer = TI THS3491 (EL5167 unusable); 48 MCX kept. Remaining (cosmetic, non-blocking): dense-0805 silkscreen warnings (KiCad 199-per-check report cap; refdes already moved to F.Fab). **Final PROJECT DONE pending the user's visual audit via the wired single-channel schematic (separate session).**

---

## Coordinator gate checklist (per sub-component COMPLETE)

- [ ] Design: ERC 0, DRC 0 on the real-parts board; `INTERFACE.md` current.
- [ ] Sim: success criteria met, plots in report, used the design's actual topology.
- [ ] Models-BOM: every part real/in-stock/sourced; BOM == design BOM (identical MPNs).
- [ ] The three reports are mutually consistent. Then mark COMPLETE here + announce.
