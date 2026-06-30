# Session Report — C2 board-bom

> The summary other tracks read instead of my log.

Track: `C2 board-bom` · Aspect: `models-bom` · Status: `criteria-met`
Last updated: `2026-06-28`

## Objective
The **final fabricable twelve-channel BOM**: the COMPLETE single-channel BOM scaled **×12**
plus the **board-level shared parts** (one shared ±12 V/GND power terminal, central bulk
electrolytics, M3 mounting hardware), every line real/in-stock/economical on Digi-Key, with
the DNP build-variant table and total cost @ qty 1 and qty 25. Source of truth for the
board-shared parts (C1 matches them).

## Success / failure criteria
- ✅ S1 per-channel parts = exact ×12 of the single-channel BOM (same MPNs; only `J_PWR` and
  the central-bulk role lifted to board-shared).
- ✅ S2 board-shared parts added & sized for 12×: J_PWR (17.5 A, ~30× margin over 0.56 A/rail),
  2× central 470 µF, 4× M3 standoff + 8× screw, 4× M3 hole feature.
- ✅ S3 every line real/in-stock/Digi-Key with full fields (only Cremat modules are direct-order).
- ✅ S4 DNP build-variant table (Full / bias-bypass / CR-210-bypass / bench-test).
- ✅ S5 per-line + total cost @ q1 and q25 with ×12 price-break tiering.
- ✅ S6 long-lead flagged (36 Cremat modules/board; 900 for a 25-board run).
- ✅ S7 board-shared parts published unambiguously for C1.
- ✅ No FAIL flags: no unsourced/out-of-stock line; per-channel set == single-channel BOM.

## Current state
COMPLETE-ready. Final BOM written; costs rolled up; DNP table done. Awaiting C1 design-BOM
for the Coordinator's Models-BOM == Design-BOM check.

## Deliverables (what & where)
- `final-board/twelve-channel/models-bom/twelve-channel-bom.csv` — the BOM (PER-CHANNEL ×12 +
  BOARD-SHARED), 20 fields/line, per-line q1 & prod cost + board qty.
- `final-board/twelve-channel/models-bom/BOM-REPORT.md` — scaling model, **board-shared parts
  table (C1 must match)**, current budget, **cost roll-up**, **DNP variant table**, long-lead.

## Cost (per board)
| Variant | 1 board @ q1 | 1 board @ q25 | 25 boards |
|---|---|---|---|
| **FULL** (CR-210 + bias filter populated, test DNP) | **$2,847.27** | **$2,517.63** | **$62,940.80** |
| CR-210 bypassed | $1,915.83 | $1,687.62 | $42,190.40 |

36 Cremat modules = ~85% of cost ($2,412 q1). Board-shared section = $7.11.

## Interface I expose / consume
- **Expose:** the board-shared parts (BOM-REPORT §3) — J_PWR=Phoenix 1715734 (277-1264-ND, ×1),
  CBULK_P/N=Nichicon UVR1V471MPD 470 µF/35 V (493-1084-ND, ×2), MH1..4=MountingHole_3.2mm_M3,
  HW_STDOFF=Keystone 24338 ×4, HW_SCREW=M3×6 ×8. Per-channel = single-channel BOM ×12 (frozen),
  channel-suffixed refs. DNP rules in §5. Board quiescent current +0.56 A / −0.51 A per rail.
- **Consume:** `integration/single-channel/models-bom/` (the ×12 source, frozen); `mechanical.md`
  (4× M3, 1U height); Cremat + TI datasheets (current budget).

## How to use my output
C1: instantiate the channel ×12 (suffixed refs) + place the 6 board-shared lines exactly as
BOM-REPORT §3; then Design BOM == this Models-BOM. C3: use the §3 current budget + bulk for
shared-rail loading.

## Open issues / asks
- None blocking. On C1 publishing its design-BOM, reconcile any ref-naming/shared-part diffs.
- `Cc` (490-13815-1-ND) and `HW_SCREW` (H743-ND) PNs are generic-line — confirm exact suffix
  at cart; equal-spec alternates listed in the CSV/report.
