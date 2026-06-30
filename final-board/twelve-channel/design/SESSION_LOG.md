# Session Log — C1 board-design (twelve-channel)

> Ground truth, append-only. Track: `C1 board-design` · Sub-component: `twelve-channel` ·
> Aspect: `design (×12 + final PCB)`.
> Reads: `docs/agent-project/{00-CHARTER,01-CONVENTIONS}.md`, brief `C-twelve-channel.md`,
> `integration/single-channel/{INTERFACE.md,design/*}`, `hardware/{mechanical.md,gen_*.py}`,
> `docs/FREEROUTING.md`.
> Success criteria: ERC 0; DRC 0 errors / 0 unconnected; **schematic-parity 0** (R2); the 12
> channels are **generated copies** of the single channel (R1, demonstrated); MCX cutouts on
> Edge.Cuts (or documented finishing step); fab package; planes filled; routed render.

---

## 2026-06-28 — session 1 — generate 12× board, route, DRC 0/0/0, parity 0, fab package

**Goal:** Multiply the frozen single channel ×12 as TRUE generated copies (R1), produce a
schematic-parity-clean (R2) 4-layer fabricable board, FreeRouting to DRC 0, export fab.

**Did:**
- Read charter/conventions/brief + the frozen single channel (`INTERFACE.md`, `gen_sch.py`,
  `gen_pcb.py`, pipeline) + `hardware/gen_sch.py` (prior 12× net-label art) + mechanical.md +
  FREEROUTING.md. Confirmed tools present: KiCad 10 CLI/python, Temurin JRE 25, freerouting 2.2.4.
- **Baseline check (R2):** ran `kicad-cli pcb drc --schematic-parity --severity-warning` on the
  single channel → **100 parity issues** (48 footprint_symbol_mismatch [bare FPID], 48
  footprint_symbol_field_mismatch [missing MPN field], 4 extra_footprint [mounting holes]).
  Exactly the pipeline defect R2 says to fix for the final board.
- **R1 — `design/gen_sch.py`:** imports `integration/single-channel/design/gen_sch.py` and emits
  its `build_spec()` 12× with `_chNN` net/ref suffix (shared rails = global power symbols). Drops
  the cell's per-channel `J_PWR` (board has ONE shared screw terminal). Adds 4 `Mechanical:
  MountingHole` symbols (R2: no symbol-less footprints). 569 components (12×47 + 1 terminal + 4
  holes). **ERC 0** first try. Netlist: 252 per-channel `_chNN` nets + 3 shared rails; 0 dup/
  unannotated refs.
- **R2 — `design/gen_pcb.py`:** imports both gen_sch modules (distinct names to avoid the
  `gen_sch` sys.modules collision) to replay the ref map. For every footprint: `SetFPID(LIB_ID(
  nick,fname))` (lib-qualified) + `SetField('MPN'/'Manufacturer'/'Distributor PN')` + Value.
  Mounting-hole footprints `SetExcludedFromBOM/PosFiles(False)` to match their symbols. 4-layer
  stackup F.Cu/In1=GND/In2=-VDC/B.Cu=+VDC pour (the proven single-channel stackup). After the
  first gen: **parity 100 → 0** (R2 achieved); the 4 residual parity were mounting-hole BOM-attr
  mismatch, fixed by the SetExcluded calls.
- **Geometry:** 12 horizontal channel bands, signal L→R; 24 MCX on the left edge (BIAS+SIPM),
  24 on the right (OUT_50+TEST_IN), uniform 10 mm slot ladder; band centerline = jack-pair
  midpoint; 2-tier interior (signal devices + decoupling sub-rows). Iterated placement DRC from
  74 → 0 errors (jack/cap courtyard overlaps, edge clearance, screw-terminal & mounting-hole
  collisions). Final outline **235 × 254 mm**.
- **Route:** export DSN → FreeRouting 2.2.4 headless (Java 25, 23 threads). First route hit 9
  copper_edge_clearance errors (autorouter hugged the perimeter jacks). Fixed by nudging jacks
  2.5 mm inboard + raising the jack ladder (JACK_Y0 12, H 254 for a clean bottom strip);
  re-routed → **score 996.37, 0 unrouted**. import_ses + fill_zones (GND In1 + F.Cu fill, -VDC
  In2, +VDC B.Cu).
- **MCX Edge.Cuts:** tested restoring the parked cutouts → 199 copper_edge_clearance errors
  (inboard cutouts become internal slots the routed GND/plane crosses). Re-parked on Dwgs.User;
  documented in `finalize_edges.py` that restoration is a GUI step done while sliding jacks to
  the edge. Shipped board stays DRC-clean.
- **Fab:** 28 gerbers + drill, position CSV (both sides), fielded grouped BOM (MPN/Mfr/DistPN/
  DNP) in `design/fab/`. Routed render `reports/routed-top.png`.
- **R1 demo (non-destructive):** monkeypatched `PARTS['R_FB']` 976→1240 in the single source,
  regenerated to a temp file → **12× '1240'** in the 12-ch schematic (one R_FB/channel);
  reverted. Real board + frozen source untouched. `reports/propagation_demo.txt`.
- **Byte-faithfulness:** board component multiset = single-channel cell × 12, 0 mismatches
  (Value+Footprint+MPN); 48 MCX confirmed; per-channel net value+pin signatures = single channel
  (23/23 real nets).

**Results (numbers):**
- ERC **0 / 0**. DRC **0 errors / 0 unconnected / 0 schematic-parity**. (`drc_full.json` = 448
  cosmetic warnings: 199 silk_overlap + 199 silk_over_copper [dense edge jacks/decoupling] + 48
  lib_footprint_mismatch [lib-sync] + 2 silk_edge_clearance; no errors.)
- Board 235.1 × 254.1 mm, 4-layer, 569 footprints (36 DNP = 3 jumpers ×12), 2159 tracks, 538
  vias, 4 plane zones. FreeRouting score 996.37, 0 unrouted.
- Fab: `fab/gerbers/` (28 files + .drl), `fab/*-pos.csv`, `fab/*-bom.csv`.

**Decisions & why:**
- **Keep all 48 MCX (don't drop TEST_IN).** R1 requires the 12 to be true copies of the frozen
  cell, which has 4 MCX. The brief/mechanical.md assume 36 (dropping TEST_IN). Dropping it is a
  CELL change → must come from the coordinator/B1, not silently here. Flagged in INTERFACE.md.
- **Board height 254 mm.** 24 MCX/edge at the 9.91 mm courtyard + 0.5 mm edge clearance force it
  past mechanical.md's ~244 mm; width 235 holds (2 boards < 482 rack). Flagged: option (b) drop
  TEST_IN → 36 MCX → fits ≤244. (Confirm tray interior either way.)
- **Jacks 2.5 mm inboard + cutouts parked.** Edge-flush jacks made FreeRouting violate the
  0.5 mm board-edge rule; inboard + Dwgs.User cutouts gave a clean routable rectangle. Edge
  restoration is the documented GUI finishing step (FREEROUTING.md step 5).
- **Reused the proven single-channel 4-layer stackup + net classes verbatim** (it routed 100%
  on the single channel and again here).

**Dead-ends / surprises:**
- `import gen_sch as board_sch` returned the single-channel module (both files named gen_sch.py)
  → loaded each via importlib under distinct names.
- Restoring MCX cutouts in place (jacks inboard) adds 199 edge-clearance errors → made it a
  finishing step instead.

**State vs criteria:** ALL met — ERC 0, DRC 0/0/0, **parity 0** (R2), **R1 demonstrated +
byte-faithful**, fab package emitted, planes filled, render saved. MCX cutouts staged + documented
(not on Edge.Cuts in the shipped board, by design, to keep it DRC-clean). TEST_IN/48-vs-36 +
board-height flagged for the coordinator.

**Next:** coordinator decision on TEST_IN/36-vs-48 + tray depth; C2 priced BOM reconcile against
this board (Round-2 part swaps if any → rerun gen_pcb.py value-only, re-DRC); C3 system sim.

---

## 2026-06-28 — session 2 — coordinator decisions: enclosure + central 470µF bulk + C2 BOM reconcile

**Goal:** Apply the 2 coordinator decisions and close the Phase-C BOM equality check.

**Did:**
- **Decision 1 (enclosure):** recorded in INTERFACE.md mechanical — keep all 48 MCX (TEST_IN
  retained), use an enclosure deeper than 244 mm; per-board depth 254 mm, width 235 (2×=470<482).
  No board change needed (already 48 MCX / 254 mm). The earlier 48-vs-36 flag is RESOLVED.
- **Decision 2 (central bulk, C2 real-parts gate):** read C2's `twelve-channel-bom.csv` —
  CBULK_P/CBULK_N = Nichicon **UVR1V471MPD** 470µF/35V radial THT, `Capacitor_THT:
  CP_Radial_D10.0mm_P5.00mm`, DK 493-1084-ND. Verified that footprint exists in the KiCad lib
  and that the real terminal footprint is `MKDS-1,5-3` (comma; C2's `.` is a cosmetic typo,
  same PN 1715734). Added both as BOARD-SHARED parts (NOT in the frozen cell — R1 intact):
  * `gen_sch.py`: emit CBULK_P (+VDC↔GND) + CBULK_N (GND↔−VDC) as `Device:C_Polarized` after
    the screw terminal, with power symbols + MPN fields. They became C253/C254.
  * `gen_pcb.py`: `build_ref_role_maps` replays the new C-ref order (screw term → 2 bulk → 4 MH);
    placed both in the top strip (x 196/208, y 9) in the only clear 23.8 mm gap (between band-1
    bulk at x189.7 and mtg hole H2 at x213.5); added `SHARED_PARTS` MPN dict so `set_fp_fields`
    propagates their MPN/Mfr/DK PN into the footprints (R2 stays 0 parity).
  * Iterated placement: first try collided CBULK_N with H2 (x212) → moved to x196/208 → 0 errors.
- Re-ran the staged toolchain: export_dsn → FreeRouting 2.2.4 (8.4 min, 23 threads, score 996.07,
  "1 unrouted" reported) → import_ses → fill_zones → DRC. The 1 FreeRouting "unrouted" is closed
  by the GND/rail plane fill: **DRC = 0 unconnected** (the authoritative gate).
- Regenerated the full fab package (28 gerbers + drill, both-sides pos CSV, fielded grouped BOM
  incl. the bulk) + routed render.
- **Decision 3 (BOM equality):** diffed design BOM vs C2 by MPN + board quantity →
  **0 mismatches on every placed electrical part** (incl. UVR1V471MPD ×2, 1715734 ×1, all 12×
  per-channel lines, 4× M3). C2-only = off-board hardware (standoffs 24338 ×4, screws ×8 — not on
  the PCB). Mounting holes equivalent (both 4× MountingHole_3.2mm_M3; C2 leaves MPN blank as a
  PCB feature). **design BOM == C2 BOM: YES.**

**Results (numbers):**
- ERC **0/0**. DRC **0 errors / 0 unconnected / 0 schematic-parity** (drc_full = 448 cosmetic
  warnings, unchanged). Board 235.1 × 254.1 mm, 571 footprints (+2 bulk), 36 DNP, 2181 tracks,
  537 vias, 4 plane zones. FreeRouting score 996.07.
- CBULK_P (C253): +VDC↔GND; CBULK_N (C254): GND↔−VDC (polarity correct). design BOM == C2: YES.

**Decisions & why:**
- Bulk caps are **board-shared, added at board level** (gen_sch shared-parts + gen_pcb
  SHARED_PARTS), NOT in the frozen single-channel cell — preserves R1 (the channel definition is
  still the single source; only board-wide parts live at the board level, like J_PWR/MH).
- Kept this board's `MKDS-1,5-3` terminal footprint (the real KiCad name); C2's `MKDS-1.5-3` is a
  typo for the same part — flagged in INTERFACE so C2 can correct the string.

**State vs criteria:** ALL Phase-C C1 criteria still met (ERC 0, DRC 0/0/0, parity 0, R1 intact,
fab package refreshed) AND the 3 coordinator items closed (enclosure recorded; 470µF bulk +
shared parts in; design BOM == C2 BOM yes).

**Next:** Phase-C gate close (C1 done; C2 priced-BOM == board; C3 system sim). If C2 corrects the
terminal-footprint string or any Round-2 value, rerun the pipeline (value-only stays DRC 0).

---

## 2026-06-28 — session 3 — cosmetic silkscreen polish + lib_footprint_mismatch assessment

**Goal:** Reduce the 448 cosmetic DRC warnings (silk + lib-sync) as far as practical; keep
ERC 0 / DRC 0 errors / 0 unconnected / 0 parity; re-fill + re-export fab.

**Did:**
- **lib_footprint_mismatch (48):** confirmed all 48 are the **MCX jacks** (J) — caused by the
  intentional Edge.Cuts→Dwgs.User cutout move (board copy ≠ library copy). Per coordinator
  guidance, **left as-is** (re-syncing would undo the routing-clean cutout parking). Documented.
- **Investigated the silk warnings:** silk_overlap=199 / silk_over_copper=199 are both **stuck at
  exactly 199 = the KiCad CLI per-check report cap.** Proved it: wrote `polish_silk.py`, stripped
  ALL 1943 footprint silk graphics (0 silk left on the board) → the reported counts stayed 199/199
  (silk_overlap items came back EMPTY; silk_over_copper pointed at pads with no silk). So the cap
  saturates regardless; the true underlying count is the inherent 0805/jack outline-silk-vs-pad-
  mask clipping (thousands of micro-events on 571 footprints).
- **Dead-end (reverted):** full silk-graphic deletion (a) didn't move the *reported* count (cap),
  (b) removed assembly-useful part outlines, and (c) inflated lib_footprint_mismatch 48→199 (the
  CLI cap again; true value ~570). Net negative → reverted to the clean routed board (regen
  gen_pcb → import_ses → fill_zones, back to 448).
- **Kept the clean, non-destructive win:** `polish_silk.py` now **moves the dense 0805/jack/trim
  reference designators off F.Silkscreen onto F.Fab** (519 refdes; kept for assembly/pick-place).
  This removes the *visible* refdes clutter (see render) and cleared the screw-terminal top-edge
  silk clip (**silk_edge_clearance 2→1**) — with **0 lib churn** (layer-only refdes moves don't
  trip lib_footprint_mismatch; only structural edits do) and **0 errors**. Part outlines kept.
- Re-filled zones; re-exported the full fab package; re-rendered (`reports/routed-top.png` shows
  the decluttered silk).

**Results (before → after):**
- silk_edge_clearance: **2 → 1**.
- silk_overlap: 199 → 199 (CLI report cap; true clutter reduced — refdes off silk, see render).
- silk_over_copper: 199 → 199 (CLI report cap; inherent 0805 outline-vs-mask, outlines kept).
- lib_footprint_mismatch: **48 → 48** (the intentional MCX cutout; left per coordinator).
- Total warnings 448 → **447**. ERC 0/0; DRC **0 errors / 0 unconnected / 0 schematic-parity**.

**Decisions & why:**
- Refdes→F.Fab is the right declutter: real visual improvement, assembly info retained, zero
  lib/electrical impact. Deleting part outlines is destructive + lib-churning + doesn't beat the
  CLI cap → rejected.
- lib_footprint_mismatch left as the intentional MCX cutout (coordinator's explicit guidance).

**State vs criteria:** gate held (ERC 0, DRC 0/0/0, parity 0); cosmetic warnings reduced where
non-destructive (edge clip 2→1, refdes clutter removed); the two capped silk checks are a CLI
reporting cap on inherent dense-0805 outline silk — reported honestly, not chased destructively.

**Next:** none blocking. polish_silk.py is the last pipeline step before fab export (see README).

---

## 2026-06-29 — session 4 — fab-blocker: MCX cutouts onto Edge.Cuts, then TILE-AND-REPLICATE rework

**Goal:** (a) fix the fab blocker (48 MCX cutouts were on Dwgs.User, not Edge.Cuts → no slots in
the gerber); then (b) per new user direction, switch the layout to TILE-AND-REPLICATE (route one
channel, clone ×12, route only commons) for byte-identical channels + far less routing.

**Did (a) — cutouts onto Edge.Cuts (autoroute approach, superseded by (b)):**
- The MCX cutout is a CLOSED 4-sided slot x[0,6.3]×y[±2.5] with the SHIELD pad straddling it by
  design → restoring slots in-place threw 144 copper_edge_clearance. Scoped DRC rule
  (`*.kicad_dru`: edge_clearance min −2mm for `A.Library_Link == cremat:MCX_CONMCX013_EdgeMount`)
  → 0. Verified kicad-cli reads `<project>.kicad_dru`.
- Naive jack rotation puts the slot INBOARD of the signal pad, blocking pad-1 escape on a 4-layer
  plane board → FreeRouting stranded 34 nets. Fixed by rotating jacks so the SLOT is OUTBOARD
  (left −90 / right +90); pad 1 escapes inward.

**Did (b) — tile-and-replicate (the delivered layout):**
- `gen_layout.py`: shared layout (the ONE channel LAYOUT + JACK_EDGE + helpers + netclasses +
  DRU). Tile = 235×21 mm (one band, full width); 12 stack → 264 mm.
- `gen_tile.py`: build ch01 as `tile.kicad_pcb` (47 fps, 4 MCX cutouts on Edge.Cuts, tile-local
  planes). Iterated placement to DRC 0. FreeRouted the tile in **2.4 s** (0 unrouted, 233 tracks
  / 68 vias) → import + fill → tile DRC 0/0.
- `replicate_tile.py`: clone the routed tile ×12 (pcbnew Duplicate footprints+tracks+vias),
  translate by 21 mm, remap refs ch01→chNN + nets `_ch01`→`_chNN` (rails global; NC pins get
  per-channel `unconnected-(...)`). Tile plane zones NOT cloned (avoid zones_intersect); board-
  wide planes (GND In1 + F.Cu, −VDC In2, +VDC B.Cu) used, per-channel rail vias tie straight in.
  Placed commons (screw terminal, 2× bulk, 4× M3) + outline. Filled, silk-polished, filled.
- Verified 12 blocks IDENTICAL: 0 footprint-geometry diffs at exact 21.0 mm pitch; 173 tracks +
  29 vias per channel (identical).

**Results (numbers):**
- ERC **0/0**. DRC **0 errors / 0 unconnected / 0 schematic-parity — WITH the 48 cutouts on
  Edge.Cuts.** `drc_full` = 597 cosmetic warnings (silk_over_copper/overlap/edge_clearance, all
  at the 199 CLI report cap). **lib_footprint_mismatch = 0** now (tile keeps cutouts as the lib
  defines them — no footprint edits).
- Board **235.1 × 264.1 mm**, 571 footprints (36 DNP), 2796 tracks, 816 vias, 4 zones.
- Edge.Cuts gerber: outline (4) + **48 cutouts (192 segs)** = 196 contour segments.
- Routed: tile ~91 nets in 2.4 s → replicated ×12 (NO per-channel autoroute); shared power via
  planes (0 unconnected). design BOM == C2: YES. Fab re-exported; render refreshed.

**Decisions & why:** cutouts = near-edge INTERNAL slots (signal pad outboard, shield straddles);
slot-outboard rotation = routable; scoped DRU exempts only MCX pads; tile zones not cloned;
prior all-autorouted board backed up to `reports/autoroute-backup.kicad_pcb`.

**Dead-ends:** restoring cutouts in-place on the inboard-jack autorouted board = 199 edge-clear
errors; slot-inboard rotation stranded 34 nets. Both resolved by the rotation flip + tile method.

**State vs criteria:** ALL met — ERC 0, DRC 0/0/0 parity WITH cutouts on Edge.Cuts; 12 channels
byte-identical (matched parasitics); commons placed; shared power via planes; fab refreshed.

**Next:** none blocking. Change the channel layout via gen_layout.py → gen_tile → route tile →
replicate_tile (all 12 update identically).
