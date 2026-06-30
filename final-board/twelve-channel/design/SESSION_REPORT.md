# Session Report — C1 board-design (twelve-channel)

Track: `C1 board-design` · Aspect: `design (×12 + final PCB)` · Status: `criteria-met — TILE-AND-REPLICATE; 48 cutouts on Edge.Cuts; 12 channels byte-identical`
Last updated: `2026-06-29`

## Objective
Multiply the frozen single channel ×12 into the final fabricable 4-layer PCB, as **generated
copies** of the one channel (R1), **schematic-parity-clean** (R2), DRC 0, with the fab package.
Built by **tile-and-replicate** (user direction): route one channel tile, clone ×12, route commons.

## Success / failure criteria
- ✅ ERC **0 / 0** (`reports/erc.json`).
- ✅ DRC **0 errors / 0 unconnected / 0 schematic-parity** (`reports/drc.json`), **WITH the 48 MCX
  cutouts on Edge.Cuts** (the prior "0/0/0" lacked the cutouts; this is clean WITH them).
- ✅ **R1 — the 12 channels are generated copies** of the single channel: schematic via gen_sch
  import ×12; layout via ONE routed tile cloned ×12. **12 channel blocks byte-identical**
  (0 footprint-geometry diffs at exact 21.0 mm pitch; 173 tracks + 29 vias per channel).
- ✅ R2 schematic-parity 0; **lib_footprint_mismatch = 0** (tile keeps cutouts as the lib defines).
- ✅ Power/GND on planes (F.Cu GND fill / In1=GND / In2=-VDC / B.Cu=+VDC pour).
- ✅ Central 470 µF bulk (CBULK_P/N, UVR1V471MPD) + screw terminal + 4× M3 placed; shared power
  via planes (0 unconnected). **design BOM == C2** (0 mismatches on placed electrical parts).
- ✅ TEST_IN/height: keep 48 MCX, deeper enclosure (**264 mm** depth).
- ✅ Fab package re-exported; routed render saved.

## Current state
COMPLETE. **Tile-and-replicate** board, 235.1 × 264.1 mm, 4-layer, **571 footprints (36 DNP)**,
2796 tracks, 816 vias, 4 plane zones, **48 MCX cutouts on Edge.Cuts** (192 segs). ERC 0 · DRC 0
errors / 0 unconnected / 0 schematic-parity. Warnings = 597 cosmetic (silk_over_copper/overlap/
edge_clearance, all at the KiCad CLI 199-per-check report cap on inherent dense-0805 outline silk;
lib_footprint_mismatch = 0).

## Deliverables (what & where)
- `design/gen_sch.py` — 12× schematic generator (imports the frozen cell — R1).
- `design/gen_layout.py` — shared layout (the ONE channel LAYOUT + helpers + netclasses + DRU).
- `design/gen_tile.py` — build the single channel tile (Phase 1).
- `design/replicate_tile.py` — clone the routed tile ×12 + commons + planes (Phase 2).
- `design/{fill_zones,polish_silk,finalize_edges}.py` — plane fill / silk declutter / cutout diag.
- `design/tile.kicad_pcb` — the routed single-channel tile (the layout source).
- `design/multi-channel-cremat-amplifier.{kicad_sch,kicad_pcb,kicad_pro,net,kicad_dru}` — board.
- `design/lib/` — project libs (cremat modules + MCX CONMCX013).
- `design/fab/` — 28 gerbers + drill, position CSV, fielded BOM (MPN/Mfr/DistPN/DNP).
- `design/reports/` — erc.json, drc.json (gate), drc_full.json, routed-top.png,
  propagation_demo.txt, autoroute-backup.kicad_pcb (prior method, for reference).
- `../INTERFACE.md` — the contract (I own it).

## Interface I expose / consume
- **Expose:** see `../INTERFACE.md`. 12× channel (BIAS/SIPM left edge, OUT_50/TEST right edge),
  shared ±12 V screw terminal, 4-layer planes. Schematic handle = the 12× root.
- **Consume:** `integration/single-channel/INTERFACE.md` + its frozen `design/gen_sch.py` (the
  R1 source), `hardware/mechanical.md`, `docs/FREEROUTING.md`.

## How to use my output
- **C2 (models-BOM):** the design BOM is `design/fab/multi-channel-cremat-amplifier-bom.csv`,
  **== C2 `twelve-channel-bom.csv`** (cell × 12 + screw terminal + 470 µF bulk ×2 + 4× M3;
  off-board standoffs/screws are C2-only). Per-channel swaps = edit the single-channel cell PARTS;
  board-shared swaps = the gen_sch shared-parts + `gen_layout.SHARED_PARTS`; then rerun pipeline.
- **C3 (system-sim):** topology byte-identical to the single channel ×12; reuse B2 per-channel
  FoM. Bulk to check vs 12× supply current = central 470 µF + 12× distributed 100 µF + per-rail.

## How to change the channel layout (R1)
Edit `gen_layout.py` (the ONE channel LAYOUT) → `gen_tile.py` → route `tile.dsn`/`tile.ses` →
import+fill the tile → `replicate_tile.py` → fill_zones → DRC. All 12 channel blocks update
identically.

## Open issues / asks
- **Enclosure depth:** per-board depth = 264 mm (user-approved deeper enclosure, keeps 48 MCX).
- **C2 footprint-string typo:** C2 lists the terminal as `MKDS-1.5-3` (dot); the real KiCad
  footprint + this board use `MKDS-1,5-3` (comma) — same part 1715734. Cosmetic; C2 to fix string.
- **Cosmetic warnings:** 597 silk warnings (all at the CLI 199/check report cap) on the dense
  0805 outline silk — no electrical/fab blocker; refdes already moved to F.Fab.
