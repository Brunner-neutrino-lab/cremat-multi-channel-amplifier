# Session Report — A3 csp-bom

> **The summary other tracks read instead of my log.** Keep current (overwrite). A
> consumer must be able to integrate from this + `INTERFACE.md` alone.

Track: `A3 csp-bom` · Aspect: `models-bom` · Status: `criteria-met`
Last updated: `2026-06-25`

## Objective
Source every part on the standalone CR-112 CSP eval board (incl. the SiPM bias front-end) to a
real, in-stock, economical **Digi-Key** part, with full provenance, as the **real-parts gate**
for A1 (design) and A2 (sim).

## Success / failure criteria
- ✅ Every part on the CSP + bias front-end sourced to one chosen MPN, in stock, priced.
- ✅ HV caps `Cc` & `Cf` carry **≥100 V** (Murata GRM21AR72A224KAC5K 100 V; Samsung
  CL21B104KCC5PNC 100 V).
- ✅ 0805 default applied to all passives that allow it (incl. the rail bulk 10 µF).
- ✅ Per line: value, MPN, mfr, Digi-Key PN, unit cost @ qty, stock, package, datasheet,
  symbol/footprint/3D source.
- ✅ Delivered as CSV + readable report; generic→real 1:1 map published for design.
- ⚠ Two **non-blocking** flags (see Open issues): CR-112 isn't a DK part (sold by Cremat);
  `Cc` exact DK suffix to confirm on the live site.

## Current state
**Done.** All 13 line items sourced + in stock + priced. Per-board (1-off) BOM ≈ **$83**
(CR-112 $65 dominates). HV rating confirmed. All footprints resolve from KiCad stock + the
existing `hardware/lib/` project lib — no login download required to lay out or DRC.
Ready for the coordinator's real-parts gate.

## Deliverables (what & where)
- `chips-board/csp-cr112/models-bom/csp-cr112-bom.csv` — machine-readable BOM (one MPN/line).
- `chips-board/csp-cr112/models-bom/PARTS_REPORT.md` — readable report: HV confirmation,
  CR-150-R5 decoupling traceability, footprint provenance table, alternates, generic→real map.
- `chips-board/csp-cr112/models-bom/SESSION_LOG.md` — full sourcing trail.

## Interface I expose / consume
- **Expose:** the chosen-parts list (above CSV/report) — the source of truth for the real-parts
  swap. One MPN per generic so A1 sets values + footprints 1:1.
- **Consume:** A1 Design's final schematic part set (to reconcile decoupling cap count at
  COMPLETE); locked values in `docs/hardware/circuit-design.md`; reference `cremat-CR-150-R5`.

## How to use my output
**A1:** for each generic in the schematic, set Value+MPN+Footprint from the "generic→real" table
in `PARTS_REPORT.md` (footprints verified present in KiCad 10 stock + `hardware/lib/`), then
re-run ERC/DRC. **A2:** values are unchanged from the generics you simmed (10 k / 0.22 µF /
100 nF / etc.) — no figure-of-merit-moving param change; note "no change."

## Open issues / asks
- **CR-112 is not on Digi-Key** (by nature — Cremat module). Order from Cremat Inc / FAST ComTec
  / Cremat Amazon store. **$65 (1–24), $59 (25+)**, made-to-order → **long lead, order early**.
- **`Cc` Digi-Key PN suffix:** GRM21AR72A224KAC5K (0.22 µF/100 V/X7R/0805) is confirmed real &
  stocked; pull the exact 490-xxxx DK PN from the live digikey.com search. Drop-in alternates:
  TDK CGA4J3X7T2A224K125AE, KEMET C0805C224K1RAC (all 100 V/0805).
- **3D model to drop in (optional, non-blocking):** `CONMCX013.step` is referenced by the
  existing MCX footprint but the file is **missing** from `hardware/lib/cremat.pretty/`. Layout/
  DRC unaffected; only the 3D viewer shows a placeholder. Human download (login):
  https://www.snapeda.com/parts/CONMCX013-T/Linx/view-part/ or
  https://www.te.com/en/product-CONMCX013.html → save as `CONMCX013.step` in that dir.
- **Reconcile at COMPLETE:** if A1's final schematic changes the per-rail decoupling cap
  count/values, tell me and I'll append rows so Models-BOM == Design BOM.
