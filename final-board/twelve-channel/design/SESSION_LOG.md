# SESSION LOG — twelve-channel design

## 2026-07-08 — rebuild from the reworked single channel (schematic + PCB)

The pre-existing `final-board/twelve-channel` was built on the OLD single channel (no rail
protection, populated buffer, 235×264 mm, flat `_chNN` net labels). Deleted the old `design/`
+ `models-bom/` (preserved `sim/`) and rebuilt from the current single channel.

**Scout.** Mapped the single-channel cell (roles/refs/nets, common vs per-channel), the old
12-ch schematic + tile-and-replicate technique, and the current routed PCB structure.

**Schematic → hierarchical (ERC 0).** Split the single-channel `layout()` into
`layout_channel()` + `layout_power()` (verified byte-identical output). New `gen_sch.py`:
- CHILD `channel.kicad_sch` = the single channel minus board-level roles (J_PWR, F_P/D_RP/F_N/
  D_RN, C_BULKP/C_BULKN). Each symbol placed once with a **12-instance** block (strided refs),
  so KiCad expands to 12 channels. Self-contained (MCX inside, only +VDC/-VDC/GND global) →
  no hierarchical pins, matching `reference/cremat-x6-board`. Validated the KiCad-10 sheet +
  multi-instance format with a 2-instance spike first.
- ROOT `twelve-channel.kicad_sch` = 12 `(sheet)` instances + common power: `J_PWR` in +
  `J_DAISY` board-to-board daisy (raw rails), up-rated PTC/SS24 reverse-block, 470 µF bulk.
- `.kicad_pro` net-class patterns globbed for the `/chNN/` names.
- Netlist: 464 unique parts (R216 U48 C134 J50 RV12 D2 F2), 12 scoped channel net-groups.

**PCB → tile-and-replicate (DRC 0/0/0).** `gen_pcb.py`:
- Cloned the routed single-channel channel row ×12 (`Duplicate` every footprint/track/via,
  `Move` 25 mm/row, ref via role ch1→chNN, net `/X`→`/chNN/X`; pad nets + values + FPID + BOM
  fields pulled from `twelve-channel.net`). Channel-vs-COM tracks split by Y (clean, 0 straddle).
- Common section placed + hand-routed once: PTC/Schottky oriented so each `_F` pad pair is at
  the same y; `+VDC_IN` on a bus above / `-VDC_IN` below (stubs off the outer pins never cross
  the mid GND pin); SMD bulk rail pads take plane vias. Board-wide plane pours carry the rails.
- Iterated DRC: fixed bulk-cap opens (SMD → plane vias), common-section shorts/mask-bridges
  (bus routing), mounting-hole collisions with edge MCX (moved to top/bottom strips + bottom
  margin), and common-part parity (value/FPID/fields from netlist). `fill_zones.py` +
  `polish_silk.py` (refdes → F.Fab) → **0 violations / 0 unconnected / 0 schematic-parity**.

Result: 138 × 335 mm, 468 footprints, 1836 tracks + 424 vias, 120 DNP. Render:
`twelve-channel-top.png`.

**Open:** regenerate the BOM (models-bom); verify the provisional up-rated protection MPNs.

---

## 2026-07-11 — NEXT UP (resume here): propagate single-channel connector fixes to 12-ch

**This board is STALE.** It was tiled from the single channel BEFORE the 2026-07-11 connector
fixes. It still uses the OLD MCX footprint — `cremat:MCX_CONMCX013_EdgeMount` (4 child-sheet
refs, **48** board instances) with old `CONMCX013.STEP` in `design/lib/cremat.pretty/` — and
the old J5 orientation. The single channel (`integration/single-channel/design`, session 8)
now has: (a) the user's **Linx `cremat:MCX_CONMCX013-T`** footprint, (b) MCX 3D
`(rotate (xyz 270 0 0))` so the coax faces off the edge, (c) MCX edge-**notch** outline, and
(d) J5 screw terminal at **rot 180**.

**How to propagate.** The 12-ch `gen_pcb.py` **tiles by cloning the routed single-channel row**
(`integration/single-channel/design/channel.kicad_pcb`) ×12, and `gen_sch.py` instantiates the
child sheet 12×. Since the single-channel source is already updated, the cleanest path is to
**re-run the 12-ch generators against it** and then verify each item transferred:

1. **Footprint files.** Copy `MCX_CONMCX013-T.kicad_mod` + `CONMCX013-T.step` into the 12-ch
   `design/lib/cremat.pretty/`. (The `.kicad_mod` already has pads 1 / `2`×2 and the `rotate
   270` 3D fix baked in.)
2. **Schematic.** Re-run 12-ch `gen_sch.py` (its `FP_MCX` must point at `cremat:MCX_CONMCX013-T`;
   grep the child `channel.kicad_sch` afterward — must show 0 refs to `_EdgeMount`). ERC 0.
3. **PCB.** Re-run 12-ch `gen_pcb.py` (re-tiles the updated single channel). Then confirm on the
   regenerated board:
   - all **48** MCX FPIDs = `cremat:MCX_CONMCX013-T`, model `(rotate (xyz 270 0 0))`;
   - the **notched outline** ports for 48 MCX = **24 notches per long edge** (single-channel
     `gen_pcb.py` cuts the notch read-back from each placed MCX + demotes footprint Edge.Cuts →
     Dwgs.User — make sure the 12-ch outline builder does the same for every tiled MCX);
   - a `channel.kicad_dru`/board `.kicad_dru` waives `edge_clearance` for
     `A.Library_Link == 'cremat:MCX_CONMCX013-T'`;
   - J5-equivalent power connector(s) at rot 180 (wire entry to the rear/top edge).
4. **Fill zones, DRC → 0/0, render** to eyeball that all 48 MCX lie flat facing off the edges
   and J5 faces out. Delete the old `MCX_CONMCX013_EdgeMount.kicad_mod` + `CONMCX013.STEP` from
   the 12-ch lib once nothing references them.

**Cross-refs:** exact recipe + the KIPRJMOD/quality **render gotcha** →
`integration/single-channel/design/SESSION_LOG.md` (2026-07-11); autoroute (Java 25 +
dead-proxy headless) → `docs/FREEROUTING.md` — **both tools must be reinstalled on the new
machine** (`C:\Users\<you>\tools\jdk-25...jre` + `freerouting-2.2.4.jar`). The single-channel
`channel.kicad_pcb` is the proven reference: routed, DRC 0/0.

NOTE: this board's `channel.kicad_sch` / `twelve-channel.kicad_sch` / `.kicad_pro` had a large
uncommitted rebuild (from 2026-07-08) — now committed WIP; open it and confirm it's clean
before starting layout.

---

## 2026-07-11 — session 9 — connector fixes PROPAGATED to 12-ch (DONE)

Followed the recipe above; all items transferred + verified:
- Copied `MCX_CONMCX013-T.kicad_mod` + `CONMCX013-T.step` into the 12-ch lib; **deleted** the old
  `MCX_CONMCX013_EdgeMount.kicad_mod` + generated `CONMCX013.step` + the now-obsolete `gen_mcx_step.py`.
- `gen_sch.py` re-run (inherits `sc.FP_MCX = cremat:MCX_CONMCX013-T`): child `channel.kicad_sch`
  now **0** refs to `_EdgeMount`, 4 to `-T`. ERC 0.
- `gen_pcb.py` updated: (a) **stop** promoting MCX cutouts to Edge.Cuts; (b) **notch builder** reads
  each tiled MCX's Dwgs.User cutout and cuts **48 notches (24/edge)** into the outline; (c) `.kicad_dru`
  waives `edge_clearance` for `cremat:MCX_CONMCX013-T`; (d) `J_PWR`/`J_DAISY` rot **180** (funnels out).
  Also add MPN/Mfr/DistPN fields to the tiled channel footprints (the regenerated single-channel board
  drops them → had been 199 `field_mismatch`).
- Verified on the board: 48 MCX = `cremat:MCX_CONMCX013-T`, model rot **(270,0,0)**; J49/J50 rot 180;
  48 notches; 0 old `_EdgeMount`. **DRC (error severity) 0 / 0 / 0**; the 48 `lib_footprint_mismatch`
  are warning-level + intentional (Edge.Cuts → Dwgs.User demotion). Render (`twelve-channel-3d.png`,
  from the design dir, `--quality high`) confirms the MCX lie flat facing off the edges. Fab regenerated
  (`fab/`, git-ignored).

Board 138 × 334.7 mm, DRC 0/0/0. **Order-ready pending the enclosure-depth width resize** (widen the
138 mm dimension so the MCX edges meet the box front/back bulkheads).

---

## 2026-07-11 — session 10 — widened to the Hammond RM2U1908 enclosure (DONE)

The user picked a **Hammond RM2U1908** 2U rack case (8"/203 mm external, ~185 mm internal depth) to
stack two 12-ch boards. The board must be as **wide as the box is deep** so the two MCX rows land on
the front and back bulkheads. Widened the board **138 → 180 mm** (one parameter, `gen_pcb.py` `W`,
conservatively 5 mm shy of the ~185 mm internal — the barrels reach through the panel; **adjust to
the box's real internal depth**).

- The single-channel **tile stays 138 mm** (`W_CELL`); the board grows only on the **output/bias
  (right) side** by `DW = W - W_CELL = 42 mm`. Signal integrity is unaffected — the shaper outputs
  are slow (µs) Gaussian pulses, so the longer OUT_50/BIAS run is immaterial; BIAS is DC.
- Clone loop: for each right-edge MCX (`RIGHT_MCX = {J_OUT50, J_BIAS}`) record pad-1, `Move(+DW)`,
  and lay a 0.4 mm **F.Cu extension** from the old pad location to the new one so the moved jack stays
  connected (this is why unconnected stays 0). The notch reader then sees the MCX at `x≈W` and cuts
  the right-edge notch there; left-edge (input) MCX are untouched.
- Re-ran `gen_pcb.py` + `fill_zones.py` + `polish_silk.py`: **180.0 × 334.7 mm, 48 notches (24 L /
  24 R), DRC 0 / 0 / 0** (incl. 0 unconnected). Render `twelve-channel-3d.png` confirms the output
  MCX sit on the far edge with the extension traces crossing the right region; input side stays
  compact. Fab regenerated at 180 mm (`fab/`, git-ignored).

**Order-ready.** Remaining pre-order check is purely mechanical: confirm `W=180` against the actual
RM2U1908 internal depth before sending gerbers.

---

## 2026-07-11 — session 11 — SPICE extension + purchase-ready BOM + cross-machine handoff (DONE)

Board layout unchanged this session (still 180 × 335 mm, DRC 0/0/0). Work was on `sim/` and
`models-bom/`, plus a handoff doc:

- **SPICE** (`../sim/`): re-ran the 3-criterion pipeline on the widened design — reproduces
  bit-identically (widening is mechanical). Added three analyses — **AC transfer function**
  (band-pass 1.59 kHz–130 kHz, upper corner confirms the 1 µs shaping), **charge
  linearity / dynamic range** (133 mV/pC, linear ~1 % to ≈30 pC, OUT_50 hard-clip 5.13 V set
  by the THS3491 buffer railing at +10.25 V — the shaper is still linear at 60 pC), and
  **ENC/noise** (design ENC = CR-112 datasheet 7000 e⁻ + 30 e⁻/pF @ 1 µs; `.noise` is only a
  cross-check because the Cremat macromodels are noiseless). Decks `chain_ac`/`chain_linearity`/
  `chain_noise`, `scripts/analyze_ac_lin.py`, report in `../sim/SESSION_REPORT.md`.
- **BOM** (`../models-bom/`): a 21-agent sourcing pass verified every DigiKey PN live (all
  Active, 2026-07-11) + Mouser second sources. `gen_purchasing.py` → `PURCHASING.md` +
  `twelve-channel-purchasing.csv` (clickable links, DigiKey Quick-Add, totals, Cremat-direct +
  Hammond ordering). Enclosure = **Hammond RM2U1908SBK** (DK HM998-ND, $189.67); its ~197 mm
  clear internal depth **confirms the 180 mm board fits** (~17 mm margin). Fixed the stale MCX
  BOM row (footprint → `MCX_CONMCX013-T`, all-4-roles desc, bias ≤70 V; `gen_bom.py` override).

- **Handoff:** wrote **`../HANDOFF.md`** — the "resume on another machine" doc: current state,
  the full toolchain + paths (LTspice / anaconda-python / KiCad / Java-FreeRouting) with the
  portability flags (`run_ltspice.ps1` hard-codes the LTspice path), the solved gotchas, how to
  regenerate every artifact, and the open user-decisions. **A new session should read that first.**

Commits: `58d0945` (SPICE + BOM), `ab68975` (widening). **Next machine: start at `HANDOFF.md`.**
