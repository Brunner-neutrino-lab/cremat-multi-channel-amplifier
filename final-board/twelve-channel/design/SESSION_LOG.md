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

---

## 2026-07-11 — session 12 — SOCKETED Cremat modules + HV-clearance defect found & fixed

**User request:** never solder the Cremat modules — solder SIP-8 **sockets** at every module
site and plug the modules in; add sockets to the BOM.

**Socket part (live-verified by 4 parallel agents, 2026-07-11):** **Samtec SS-108-TT-2**
(DigiKey **612-SS-108-TT-2-ND**, legacy `SAM1119-08-ND` — the exact part **Cremat's own
CR-160 eval-board BOM specifies** for these modules). Machined BeCu contacts accept
0.38–0.56 mm leads; the modules have **flat 0.51 × 0.25 mm** stamped pins (CR-112/CR-210
datasheet drawings), squarely in range. $1.37 (1) / $1.17 (10-99); DK stock ~650.
Verified alternate: **Harwin D01-9970842** (gold flash, ~3.9k stock, $0.75 @ 40).
**Do NOT sub Mill-Max/Preci-Dip 801-series** — their contacts take 0.7–0.9 mm pins.
Cremat sells no standalone sockets. Our 1.0 mm holes: oversized vs Samtec's 0.66 mm
recommendation but verified fits-and-hand-solders; insert a module while soldering to align.

**Footprint:** stock `Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical` is
**pad-for-pad and courtyard-identical** to the PinHeader_1x08 it replaces (verified in
pcbnew) → zero copper change. `FP_SIP` updated in the single-channel `gen_sch.py` (12-ch
inherits); both schematics regenerated, ERC 0, netlist membership IDENTICAL (29 / 271 nets).

**HV-clearance defect (found while verifying):** regenerating `twelve-channel.kicad_pro`
re-instated the netclasses — and DRC then showed **499 hv_bias (0.6 mm) clearance errors**.
Root cause chain: (1) the single-channel `.kicad_pro` netclass patterns `FE`/`N_filt` lacked
the leading `/` and so matched NOTHING — the 2026-07-11 MCX reroute packed the SiPM-bias
front-end at default 0.2 mm; (2) a GUI save had **flattened the 12-ch `.kicad_pro`
netclasses** (hv_bias deleted), committed unnoticed in `4554c4c`, so sessions 9–11 ran DRC
blind to the HV rule — the "DRC 0/0/0 order-ready" claim was **vacuously passing**.
**Fix at the source:** single-channel `gen_pcb.py` patterns now `*/`-prefixed
(`*/FE`, `*/N_filt`, …); single channel re-routed with hv_bias 0.6 mm/0.4 mm live in the
DSN (verified `width 400 clearance 600` on `/BIAS_IN /FE /N_filt`), DRC 0/0;
12-ch re-tiled (gen_pcb + fill_zones + polish_silk). **Final 12-ch DRC (parity): 0 errors /
0 unconnected / 0 parity**, 48 warning-level intentional `lib_footprint_mismatch` (MCX).
36 sockets, 0 headers, 48 MCX-T, 48 notches, 180 × 334.7 mm. Fab package regenerated.

**BOM:** `gen_bom.py` appends the socket row (qty 36, FIT, full sourcing metadata);
`gen_purchasing.py` SRC has the SS-108-TT-2 entry. Single-channel BOM CSV: 3 module rows →
PinSocket footprint + SKT1-3 socket row (qty 3). **12-ch CSV regen was blocked — both
`twelve-channel-bom.csv` and `twelve-channel-purchasing.csv` were share-locked by an open
Excel session; re-run `gen_bom.py` then `gen_purchasing.py` after closing Excel.**

**Lesson (keep):** never commit a GUI-saved `.kicad_pro` over the generated one — a KiCad
GUI save flattens the generator's netclasses and silently disables the HV DRC rule. Regen
with `gen_sch.py` (12-ch) / `gen_pcb.py` (single-channel) instead, and treat "netclass
patterns present in `.kicad_pro`" as part of the pre-order checklist.

---

## 2026-07-11 — session 13 — enclosure: 2U → 1U (one board per case) + MCX-recess analysis

**User decision:** one amplifier per box, 1U. BOM updated: **Hammond RM1U1908VBK** (vented,
DK HM1004-ND, $169.21, 70 stk; solid alt RM1U1908SBK HM995-ND $162.45). Vented chosen
because the board dissipates ~13.4 W under a 40 mm lid. `gen_purchasing.py` CASE + regen.

**Factory-drawing-verified dims (both 1U + 2U drawings fetched from hammfg.com, local
copies in the session scratchpad):** RM1U1908 internal depth **196.85 mm** [7.750] exact,
internal height **40.09 mm** [1.578], internal width 415.30 mm; front/rear panels =
separate flat 3.2 mm extruded plates, removable & interchangeable; no PCB bosses (mount on
standoffs off the bottom cover; Hammond offers free STEP models + factory machining).
**1U height check PASSES:** standoff ~4.8 + board 1.6 + socket seat 4.45 + module body
20.8 = **~31.7 mm < 40.09 mm** (~8 mm margin; trimpot/electrolytics are shorter). NOTE
there is NO 12"-deep RM; depths are 8"/13"/18" (13" = RM1U1913SBK if ever needed).

**MCX recess at the panels — options compared (all live-priced 2026-07-11):**
- **(A) Widen the board `W` 180 → ~194 mm — RECOMMENDED.** At W=180 the jack faces sit
  ~8.4 mm behind each panel (user: "push the cable ~1 cm through the hole"). At W=194 the
  board-edge-to-panel gap is ~1.4 mm/side; the CONMCX013 face protrudes ~3.6 mm past the
  board edge → the face lands ~1 mm inside the panel outer surface; a ~5.5 mm panel hole
  lets the plug nose engage at the panel. Assembly is a non-issue with the removable flat
  panels: mount the board, then slide each panel on axially over the jack barrels and screw
  it down (no angle-insertion needed). One `W` param + scripted re-run (the widening
  mechanism from session 10 — tile stays 138 mm, right-side extension traces stretch).
  Verify the 3.6 mm face protrusion on the CONMCX013 drawing before drilling panels.
- **(B) Panel bulkheads — REJECTED on sourcing.** MCX F-F feedthrough barrels are
  effectively non-stocked (~$370–500/48 at factory lead, PLUS 48 board→panel jumpers).
  MCX-bulkhead pigtail assemblies: unavailable ($500–2,200/48 or 250-pc MOQs). Cheapest
  real route = Molex 73415-5230 crimp bulkheads (~$112/48) + hand-built RG-316 pigtails
  ×48 + crimp tool — heavy labor, 96 extra RF joints. In-stock hybrid exists (Taoglas
  CAB.0130 SMA-bulkhead→MCX-plug pigtails, ~$314/48) but changes the panel connector to SMA.
- **(C) Open/semi-open box — ADVISED AGAINST for operation.** The shaping band is
  1.6–130 kHz; mains harmonics + SMPS hash land IN band, and the FE node (fC-scale, ENC
  ≈1.1 fC) sits ~1 cm from the would-be open face. Two full open faces make the box a poor
  shield at these frequencies (aperture-dominated); Cremat's own eval boxes are fully
  closed. The vented covers (Ø4.3 mm holes) already give the "semi-open" thermal benefit
  with EMI-negligible apertures. Open-air is fine for BENCH testing, not for the rack.

**Pending user go-ahead:** run the W=194 resize (gen_pcb + fill + polish + DRC + fab).

---

## 2026-07-11 — cross-session note (from the ets-breakout session — NOT the owning session)

A Claude session working in `ets-breakout` briefly operated on this tree (user redirected it
back to ets-breakout; it made **no commits**). What it found and did, ~13:40–13:50:

- **Found the HV defect reintroduced:** the 13:22 GUI save had re-flattened
  `twelve-channel.kicad_pro` (hv_bias netclass gone) and the zones had been refilled at the
  0.5 mm zone clearance — DRC (with netclasses restored) showed **505 hv_bias 0.6 mm
  clearance violations**, and the **13:32 fab exports carried that bad fill. Do not order
  from the 13:32 gerbers.**
- **Repair (per this project's own session-12 procedure):** re-ran `gen_sch.py` (schematics
  byte-identical; `.kicad_pro` netclasses restored), `fill_zones.py` refill, then
  `kicad-cli pcb drc --schematic-parity` → **0 errors / 0 unconnected / 0 parity, 48
  warning-level lib_footprint_mismatch (intentional MCX)**. ERC 0. Fab re-exported
  (gerbers/drill/pos/STEP, ~13:43) + `twelve-channel-fab.zip`.
- **BOM:** re-ran `gen_bom.py` + `gen_purchasing.py` (the session-12 Excel lock is gone) —
  outputs match session-12 totals ($2,682.12 FIT / $221.76 buffer / $189.67 case).
- Render images (`twelve-channel-3d.png`, `-top.png`, `.pdf`) regenerated from the fixed
  fill; a verification pass (Hammond RM2U1908 internal depth, per-line BOM re-check) was
  also run — results, if material, will be added below this note by the user or a later session.

Everything above is uncommitted working-tree state; the owning session should review,
re-verify (netclasses present in `.kicad_pro` → DRC), and commit.

**Addendum (same ets-breakout session, ~14:10) — verification-workflow results for the owning session:**

- **Case fit CONFIRMED from Hammond's own drawings** (`hammfg.com/files/parts/pdf/RM2U1908SBK.pdf`,
  §DD-DD; VBK identical): internal clear depth **196.85 mm** [7.750 in], panels 3.18 mm, external
  203.20 mm. The 180 mm board fits with 16.85 mm total margin. Interior W 415.30 mm / H 84.53 mm.
  HANDOFF open item 1 is closed — no width change needed; RM2U1912 not required.
- **Cremat prices stale** (official US list effective 2026-01-01, tiers 1-9/10-99/100+):
  CR-112 $65/$55/$47, CR-200-1us $65/$55/$47, CR-210 $86/$77/$73.10. At qty 12 → CR-112 $660
  (not $780), CR-200 $660 (not $708), CR-210 $924 (unchanged). Modules total **$2,244, -$168 vs
  PURCHASING.md**. Qty 12 > Amazon's ≤10 limit → order by email (info@cremat.com).
- **THS3491 buffer option: PN trap** — `296-49085-2-ND` is the 250-pc reel (~$3,020, can't order 12).
  Use cut tape **`296-49085-1-ND`**, $18.28 q1, same 680-pc DK stock.
- **Murata 0.22 µF 100 V (490-8306-1-ND): DK stock ZERO, 17-wk lead.** Buy Mouser
  `81-GRM21AR72A224KAC5K` (~$0.24, tens of k, reconfirm) or DK alt KEMET
  `399-C0805C224K1RACTUCT-ND` (95,632 stk, $0.49 q1). Update gen_purchasing.py SRC accordingly.
- All other 17 catalog lines re-verified OK (incl. MCX CONMCX013 DK 1,050 stk; SS-108-TT-2 $1.168 @36).
- **PCB fab (indicative, qty 5 = practical min at both):** JLCPCB ~$62 HASL / ~$85 ENIG (+~$30 ship);
  PCBWay ~$172 / ~$202. 180×335 accepted by both, no large-board surcharge (JLC threshold 650 cm²;
  board is 603 cm² — don't grow the outline).
- BOM arithmetic audit: exact pass (380 FIT / 120 DNP; totals match). Renders + PDF regenerated
  13:56 from the fixed fill; `twelve-channel-fab.zip` at 13:49.

---

## 2026-07-11 — session 14 — SLOT-THROUGH panels: board 180 → 213.2 mm (+ 2nd re-flatten caught)

**User decision (option A, improved):** instead of 48 panel holes, mill ONE slot in each
front/rear panel and let the **board pass through, protruding 5.0 mm past each panel outer
face**. Easier machining (one straight op), the slot absorbs all alignment tolerance, MCX
snap-on happens fully in the open, and the board can slide in/out with the panels mounted.

**Executed:** `W = 213.2 mm` (= external depth 203.20 + 2 × 5.0) in `gen_pcb.py`; full
pipeline (gen_pcb → fill_zones → polish_silk). **Honest DRC: 0 / 0 / 0** (48 intentional
MCX warnings), 48 notches (24/edge), board **213.2 × 334.7 mm**, fab + render regenerated.

**Panel slot spec (mill BOTH panels identically):**
- ~**340 mm long × 7 mm tall**, centered horizontally (board 334.7 long; panel internal
  width 415.3 → ≥37 mm meat each end; slot must be CONTINUOUS — the board edge is).
- Vertical: centered on the board mid-plane = standoff height + 0.8 mm above the
  bottom-cover inner face (4.8 mm standoffs → slot spans ≈2–9 mm above the floor).
  **Measure against the assembled case + real standoffs before milling.**
- Board edge 5.0 mm proud; MCX faces ≈8.6 mm proud (face ~3.6 mm past the edge — confirm on
  the CONMCX013 drawing; cosmetic only). EMI: the ~340×7 aperture is mostly filled by the
  board + grounded shells; FE nodes are 10–25 mm inboard — negligible in the 1.6k–130 kHz band.

**⚠ .kicad_pro re-flattened AGAIN (incident #2) — root cause found: an OPEN pcbnew GUI**
(`twelve-channel — PCB Editor`) was holding the project; its saves rewrite the netclasses
away (and its stale in-memory board would overwrite the disk board on Ctrl+S). The first
W=213.2 DRC ran vacuously and its fill/fab were bad — caught, healed, re-verified.
**Pipeline is now self-healing:** `gen_pcb.py` re-asserts `build_pro()` after SaveBoard, and
`fill_zones.py` refuses to fill blind (checks for hv_bias, restores it + warns loudly).
Rule stands: close the 12-ch pcbnew window (without saving) before running the pipeline.

**BOM corrections folded in** (from the ets-session verification addendum above): Cremat
2026-01 price list at the qty-12 tier → modules **$2,244** (CR-112/CR-200 $55, CR-210 $77;
q1 $65/$65/$86); **FIT subtotal $2,514.12**. THS3491 DK PN → cut-tape **296-49085-1-ND**
(the -2-ND is a 250-pc reel!) — fixed in gen_sch PARTS (schematics/netlists regenerated,
ERC 0, membership identical) + both CSVs + purchasing. Murata 0.22 µF 100 V: DK stock 0 →
buy Mouser 81-GRM21AR72A224KAC5K or KEMET alt (noted). Case = RM1U1908VBK $169.21/board.

**Fab-cost flag:** at 213.2 × 334.7 the board is ~714 cm², ABOVE JLCPCB's 650 cm²
large-board threshold (it was 603 cm² at W=180) — expect a surcharge or use PCBWay; get a
fresh quote before ordering.

---

## 2026-07-11 — session 15 — JLCPCB fab+assembly package + KEMET swap (order-ready v2)

**User decisions:** (a) HV coupling cap primary = **KEMET C0805C224K1RACTU** (Murata went
DK 0-stock; Murata retained as alt) — swapped in gen_sch PARTS, both CSVs, purchasing SRC;
full regen chain re-run (ERC 0, membership identical, re-tile, DRC 0/0/0, hv_bias verified,
fab re-exported). (b) **Buy boards from JLCPCB with SMT assembly of the passives**; the
rest in a DigiKey hand-BOM. Cremat modules: user already has them.

**JLC feasibility (13-agent live verification, incl. a live wizard quote):**
- Fab: 4L 213.2×334.7 fits easily (max 1016×596); large-size fee just **$5**/order.
  Live quote qty 5: **$73.70 HASL / $98.40 ENIG** (incl. $25 eng fee). Edge notches fine
  (routing ~12 m/m² vs 80 limit).
- Assembly: qualifies for the cheap **Economic tier** (single PCB to 470×500, 4L/1.6mm,
  top-side, no rails/fiducials). $8 setup + $1.50 stencil + $3/Extended line.
  ⚠ possible undocumented $59.23 per-order assembly large-size fee — confirm in the live
  assembly quote.

**Package written → `design/fab/jlc/` + `ORDERING.md` (master buy sheet):**
- `gerber-twelve-channel-jlc.zip`, `bom-twelve-channel-jlc.csv` (JLC headers, 12 lines,
  LCSC C-numbers), `cpl-twelve-channel-jlc.csv` (246 FIT-SMD placements; DNP/THT excluded).
- LCSC mapping policy: **Basic-library part when spec-equal-or-better** (8/12 lines free),
  exact MPN when no Basic exists (0.22µF-100V KEMET C2167405, 1pF C513668, 470µF C494847,
  PTC C207066 → 4×$3 fees). Notable subs: 10µF 25V → Samsung CL21A106KAYNNNE C15850
  (KEMET 25V not at LCSC in 0805 — beware their 106K8 = 10V parts); SSA24 → **MDD SS34
  C8678** (SMA 40V 3A, Basic; onsemi had 2 pcs). Resistors → UNI-ROYAL 1% Basic equivalents.
- Rotation caveat: check D1/D2 + C10/C11 polarity in JLC's parts-review preview.
- DigiKey hand-BOM (`models-bom/digikey-hand-bom.csv` + Quick-Add in ORDERING.md):
  MCX ×48, SS-108-TT-2 ×36, 3296W ×12, terminals ×2, case ×1 ≈ **$399/board**; optional
  buffer +$222. `.gitignore`: fab/* stays ignored but `fab/jlc` BOM/CPL are tracked.

---

## 2026-07-11 — session 16 — fix: KiCad opened the CHILD sheet + twelve-channel.pdf was a PCB plot

Engineer reviewing the board hit two issues:

1. **Opening the project opened `channel` (the child), not `twelve-channel` (the root).** Root
   cause: `gen_sch.py`'s `sheet_file()` appended `(sheet_instances (path "/" (page "1")))` to
   BOTH files, so the child `channel.kicad_sch` declared itself a standalone ROOT — KiCad then
   opened it as the top sheet. The known-good `reference/cremat-x6-board` child has NO
   `sheet_instances` block. Fix: `sheet_file(..., is_root=False)` — only the root gets the
   `(sheet_instances (path "/" ...))`; `build_root()` calls it with `is_root=True`. Regenerated:
   child now has 0 `sheet_instances`, root has 1. ERC 0; netlist membership IDENTICAL (271 nets,
   circuit untouched); board↔schematic parity still 0 (48 MCX lib_footprint_mismatch are the
   intentional warnings). Root/project/netlist/board files regenerated byte-identical — only
   `channel.kicad_sch` changed.

2. **`twelve-channel.pdf` was "PCB artwork on a schematic page".** It was a `kicad-cli pcb
   export pdf` output (title block: "File: twelve-channel.kicad_pcb", 1 page) misnamed as the
   schematic. Replaced with the real schematic: `kicad-cli sch export pdf twelve-channel.kicad_sch
   -o twelve-channel.pdf` → 13 pages (root block-diagram page 1 + 12 channel sheets). Regenerate
   the reviewable schematic PDF with that command; the PCB is viewed via `twelve-channel-3d.png`
   / the fab gerbers.

---

## 2026-07-11 — session 17 — REAL fix for "KiCad GUI opens the channel sheet"

Session 16's guess (child `sheet_instances`) was NOT the cause — the engineer reproduced it on
the fixed files. Actual root cause: **`twelve-channel.kicad_pro` → `schematic.top_level_sheets`
pointed at `channel.kicad_sch`.** `build_pro()` copies the single-channel `channel.kicad_pro`
(whose root genuinely IS channel) as its base and never re-pointed `top_level_sheets` to this
project's root. **`kicad-cli` ignores `top_level_sheets` (filename-based root → opened
twelve-channel, 13-page export)**, which is why every headless check passed — but the **GUI
honors `top_level_sheets`** and opened the child. That's the kicad-cli-vs-GUI split.

Fix: `build_pro()` now sets `top_level_sheets = [{filename: twelve-channel.kicad_sch, name:
twelve-channel, uuid: ROOT_UUID}]`; patched the committed `.kicad_pro` in place too. Schematic
`.kicad_sch` files unchanged (regen byte-identical), ERC 0, netclasses intact, board untouched.
The single-channel `channel.kicad_pro` correctly keeps channel as its own root (not touched).
(The session-16 `sheet_instances` cleanup + the schematic `twelve-channel.pdf` are still valid.)

---

## 2026-07-22 — session 18 — clean up the root common-power section (text/GND/wire cosmetics)

Engineer review of the root `twelve-channel` power section flagged three cosmetic/connectivity
issues (see the "before" at `_before` render): (a) net/ref/value labels overlapping — the two
rails were only 12.7 mm apart while the uprated `PTC 1.1A 24V` value ran right across both
columns; (b) GND symbols whose ground pin/text was buried in the adjacent part instead of
pointing away; (c) power symbols dropped directly on component pins (no wire stub) so a GUI
*move* detached them — "looks like lines, not wires".

Re-laid the whole power block (single-channel `layout_power()` + the 7 board-part SPEC
positions; `J_DAISY` in the 12-ch `build_root`) as **two spacious horizontal rails**:
`+VDC_IN → [F PTC] → +VDC_F → [D Schottky] → +VDC → PWR_FLAG → [C_BULK] → GND`, +VDC on top /
−VDC below. Node labels on the left, ref/value centred under each part, rail power-symbols and
PWR_FLAGs on their own short **up-stubs pointing away**, one isolated GND+PWR_FLAG pair for ERC,
and a shared `power_terminal()` helper for J_PWR/J_DAISY (GND runs out past the label column and
points down). Bulk caps hang below their rail with the electrolytic **+** to the GND side.

Two generator bugs fixed along the way:
- **`text_pos` mis-classified `D_Schottky`** — its pins are horizontal at rot 0 (R/C/fuse are
  vertical), so its text orientation is rotated 90° from the others (`horiz0` handling added).
- **rot-180 symbols got left-justified text that KiCad flips to the right**, so a right-stacked
  value rendered *over* the cap body. KiCad mirrors horizontal justify for a 180°-rotated symbol,
  so `sym_instance` now pre-flips L↔R justify at rot 180 (`_flip_just_h`). `tang` (text angle)
  kept at the original upright formula — the earlier `tang = rot` experiment rendered rot-180
  text upside-down, confirming the angle was already correct and only justify was wrong.

Verification: **ERC 0** (root + single-channel); **netlist partition IDENTICAL** to the pre-change
baseline (271 nets, same pin-sets — pure cosmetics, connectivity untouched); the **12 child sheets
are byte-identical** to HEAD (the power roles are board-level / excluded from the child, and the
child's 5 rot-180 parts use centred justify so the swap is a no-op); `.kicad_pro` still opens the
root (session-17 fix intact). Refreshed `twelve-channel.pdf`. Fab outputs (gerber/CPL/BOM) are
untouched — they derive from the PCB, not the schematic. Renders (KiCad → PDF, rasterised with
the bundled PyMuPDF) confirmed each rail reads cleanly with no overlaps.

---

## 2026-07-22 — session 19 — clear the 48 `lib_footprint_mismatch` DRC warnings (MCX)

`kicad-cli pcb drc --schematic-parity` on the final board reported **0 unconnected, 0 schematic
parity**, and **48 `lib_footprint_mismatch` warnings** — the "tremendous amount of parity
warnings" the engineer saw are these 48 (KiCad groups them with the parity section of the DRC
dialog). All 48 were the MCX jack `cremat:MCX_CONMCX013-T`, each "Local override".

Root cause: the library copy `lib/cremat.pretty/MCX_CONMCX013-T.kicad_mod` was **legacy
KiCad-6/7 format** (`tedit`, `fp_text reference`) and, crucially, kept the MCX edge notch on
**`Edge.Cuts`**, whereas the as-placed board footprints carry that notch on **`Dwgs.User`**
(the deliberate "demote" `gen_pcb` documents, so the 48 notches don't each become a board-edge
cut — the real notches are drawn once in the board outline). Orientation-normalised geometry
diff (`pcbnew`): OLD vs board-as-built differ ONLY by those 3 notch lines' layer
(Edge.Cuts→Dwgs.User); all 3 pads, courtyard, fab, silk, mask/paste and the 3D model are
identical.

Fix (what the engineer asked — "add the footprint to our library"): exported one board MCX
instance, normalised to origin/0°/REF**, nets stripped, via `pcbnew.FootprintSave()` back into
`cremat.pretty`, so the library copy is now the **as-built KiCad-10 footprint**. Did the same
for the single-channel `integration/.../lib/cremat.pretty`. Only the two `.kicad_mod` library
files changed — **no `.kicad_pcb` touched**.

Verification: final board DRC now **0 / 0 / 0 / 0** (violations / unconnected / parity /
mismatches); library footprint geometry proven equivalent to the as-built copy (only the notch
layer moved, matching the board); the `${KIPRJMOD}/lib/cremat.pretty/CONMCX013-T.step` model is
preserved and the 3D top render shows all 48 MCX jacks resolving; fab outputs untouched (board
unchanged). Single-channel board also cleared its 4 MCX mismatches; its **45
`footprint_symbol_field_mismatch`** are pre-existing on that dev testbed (session-18 changed no
component fields — diff shows only power-symbol #PWR/#FLG markers moved, and those have no
footprint — and the final board is 0 parity), so they're out of scope for the ordered board.
(`MCX_CONMCX013_EdgeMount.kicad_mod` in the single-channel lib is an older, unreferenced name —
harmless, left as-is.)

---

## 2026-07-22 — session 20 — REAL cause of GUI parity 199+: broken footprint↔symbol PATHS

Engineer's GUI DRC showed **Schematic Parity 199+**, components looking disconnected, and —
the decisive clue — **"Update PCB from Schematic" DUPLICATED every component**. That symptom =
the footprint↔symbol **link is broken**: KiCad matches footprints to symbols by **UUID sheet-path**,
not by reference.

Root cause (in `gen_pcb.py`): **`parse_netlist` grabbed only the 36-char component tstamp and set
each footprint path to `/<symbol_uuid>`**, dropping the per-channel sheet prefix. Our child sheet
is instantiated **12× sharing ONE symbol uuid per role**, so the sheet prefix is the *only* thing
that makes the 12 instances unique. Result: **468 footprints but only 47 distinct paths** — massive
collisions, and none match the schematic's real symbol paths (`/<sheet>/<symbol>`). KiCad therefore
links nothing → 199+ parity + duplicate-on-update. (My earlier ref-based parity check matched by
`(ref,pad)` so it read "0 mismatches" — nets *were* right; only the UUID linkage was broken.)

The correct path = **`sheetpath.tstamps` (root-omitted, e.g. `/559c…/`) + `component.tstamps`**,
proven against the flat single-channel board (there sheetpath is just `/`, so `/symbol` is right —
which is why *it* was never broken). Fixes:
- **`gen_pcb.py`**: `parse_netlist` now builds the full `/sheet/symbol` path; both `SetPath()` sites
  use it directly (root parts collapse to `/symbol` automatically).
- **The existing routed board**: re-pathed in place with `pcbnew.SetPath()` (a metadata-only edit —
  **no track/pad/zone touched**). 456 footprints re-pathed → **464 distinct paths** (+4 mounting
  holes, no symbol). Verified: **DRC 0/0, pad-net parity 0, identical segment count (routing intact),
  and a full BIJECTION** — every one of the 464 schematic symbols maps to exactly one footprint and
  vice-versa (0 orphans either way). So "Update PCB from Schematic" now finds everything already
  placed (no duplicates) and parity clears.

Also fixed two real cosmetics found while investigating:
- **Coax shield GND symbols pointed into the jack body** (legibility). New `coax_gnd()` helper stubs
  each shield away and points GND outward (J_BIAS/J_TEST up, J_SIPM right, J_OUT50 down); added a
  text-angle term to the power-symbol emitters so a rotated GND keeps upright "GND" text.
- **`gen_sch` stamped a fictitious `(version 20260306)`** (real KiCad-10 = 20250114) → **20250114**.
  Good hygiene (avoids a "newer-file" warning) but NOT the parity cause — the paths were.

Not defects (confirmed): the "blue X" on U4 pin 2 is the correct `no_connect` on the THS3491 NC pin;
a from-scratch dangling-end detector found **0 stray wire ends**; ERC 0. The single-channel dev
board's 45 `footprint_symbol_field_mismatch` remain pre-existing/out-of-scope.

---

## 2026-07-22 — session 21 — ROOT CAUSE: netclasses were missing their SCHEMATIC fields

The real cause of "wire T-taps read as unconnected in the GUI" (sessions 18-20 chased this and
got it wrong three times): **our four netclasses in `.kicad_pro` were PCB-only.** Each defined
`clearance` / `track_width` / `via_diameter` / `via_drill` but omitted every SCHEMATIC field:

    missing: wire_width, bus_width, line_style, diff_pair_gap, diff_pair_width,
             microvia_diameter, microvia_drill

A netclass with no `wire_width` breaks eeschema's connectivity for every net in that class --
wires stop joining at T-taps. Introduced in session 15 when the `hv_bias` class was hand-written
to get the 0.6 mm bias clearance; the PCB half was written, the schematic half was not.

Why it hid for so long: netclasses only exist when the project is loaded. Opening a sheet
standalone (no `.kicad_pro`) works, and **`kicad-cli` never reads the project file at all** --
so ERC, `sch export netlist`, and the pcbnew pad-net parity check ALL reported "connected" while
the GUI showed unconnected stubs. Every automated gate was structurally blind to it. KiCad's own
re-save then dissolved the junctions it considered unreachable (116 wires/36 junctions -> 89/3),
which looked like KiCad corrupting good geometry but was a downstream symptom.

Found by bisection on tiny generated projects (`A_bare` .. `J_nonetclass`): minimal-everything
worked; swapping in the REAL `.kicad_pro` reproduced the failure with identical schematics;
dropping `net_settings.classes` fixed it; diffing our classes against a known-good project
exposed the 7 missing keys.

Fix: `build_pro()` now fills the schematic defaults on every class (wire_width 6, bus_width 12,
line_style 0, diff_pair_gap 0.25, diff_pair_width 0.2, microvia 0.3/0.1); the single-channel
`channel.kicad_pro` (which `build_pro` copies) was patched the same way. PCB rules unchanged --
`hv_bias` still 0.6 mm clearance / 0.4 mm track, and the board's 288 bias tracks measure 0.4 mm,
confirming the class WAS applied during routing.

Also in this pass: the child sheet is now emitted as 12 SEPARATE files (`channel_ch01..12`), each
instantiated once, with per-channel symbol UUIDs -- so footprint<->symbol paths are unique by
construction. (Aimed at a hypothesis that turned out wrong; kept because it removes the
shared-UUID path collision at the source. `gen_pcb.parse_netlist` builds `/sheet/symbol` paths.)

Verified: ERC 0; PCB DRC 0 violations / 0 unconnected; footprint<->symbol bijection 464<->464;
pad-net parity 0/1290; 271 nets with only the 24 intentional NC pins unconnected. Fab outputs
(gerber/CPL/BOM, 07-11) untouched -- no copper changed.

LESSON: a "0 violations" from ERC/kicad-cli does NOT mean the GUI agrees. Those tools never load
`.kicad_pro`. When the engineer's GUI disagrees with the CLI, trust the GUI and bisect the
PROJECT, not just the schematic.

---

## 2026-07-23 — session 22 — engineer review round: thermal relief + 4-layer justification

Two questions from the reviewing engineer. One was a real defect; one was a documentation gap.

**1. "Why is there no thermal relief on pins connected to the ground pour?" — a real bug.**

All four zones were on `ZONE_CONNECTION_NONE`, which does not merely omit spokes — it **isolates
the pour from every pad**. The GND pour and the In1 GND plane were therefore contributing *nothing*
to the ground return: every GND connection was being carried by tracks and vias alone. DRC still
reported 0 unconnected (the tracks satisfied connectivity), so no automated gate ever flagged it.
Another instance of the project's recurring pattern — a green check that was structurally unable
to see the defect.

Fixed in `fill_zones.py`: all zones → `ZONE_CONNECTION_THERMAL` (gap 0.5 mm, spoke 0.5 mm), refilled.
THERMAL rather than FULL because **218 GND pads on this board are hand-soldered** (120 SIP-8 socket
pins + 96 MCX shields + 2 screw-terminal); soldering those into a 65 000 mm² plane gives cold joints
and lifted pads. Spoke cost is negligible here: rail draw is milliamps, and ~1–2 nH of spoke
inductance at a ~350 kHz knee is <10 µΩ.

Effect on copper: 6.45 → 7.13 MB, `filled_polygon` count 16 → 40. Routing untouched (tracks 1920,
vias 388, footprints 468 all unchanged). Fab outputs regenerated; gerber zip 2.58 → 2.72 MB, same
28-file set (drill re-exported **merged**, matching the original — do *not* pass
`--excellon-separate-th`, which splits it into PTH/NPTH). CPL/BOM unchanged and re-verified
(246 rows, all designators present, all positions match).

**2. "Why 4 layers — is it for impedance control?" — no, and the docs never said why.**

It is explicitly *not* impedance control (that was already documented). The real reason is
plane-based power/return distribution, and the routed board makes it numerical: **464 of 1290 pads
are GND/+VDC/−VDC** (364/50/50) yet those three nets carry only **490 mm of track total** — each pad
drops through a via onto its plane (240 GND vias, 50 per rail). A 2-layer build must route all 464
as tracks alongside 12 signal chains and 12 HV bias nets. Three-part justification (return-path
integrity for a charge integrator, bipolar rails to 12 channels, HV creepage competing for outer-layer
space) written up in `docs/hardware/pcb-design-rules.md` § *Why four layers*.

**New: `check_board.py` — the acceptance gate as a runnable tool.**

The parity/bijection/netclass checks had only ever existed as ad-hoc scratchpad code, so the engineer
could not re-run them. Now a project script covering: footprint↔symbol UUID bijection · **pad-net
parity** (the real one — `kicad-cli pcb drc --schematic-parity` is footprint-level and does not
compare pad nets) · ERC/DRC · **zone pad-connection mode** (would have caught the bug above) ·
**netclass schematic-fields + measured copper width** (would have caught session 21's root cause) ·
CPL-vs-board consistency. Every check prints what it *cannot* see.

It immediately found something the ad-hoc checks had not: the 12 `OUT_50` nets carry both 0.33 and
0.4 mm copper. Investigated — **not a defect**: `gen_pcb.py:172` draws the 76 mm right-edge extension
run to the output MCX at 0.4 mm, and a netclass `track_width` is the default/minimum, not a cap.
Wider is electrically better on a long run. The *check* was wrong, so the check was fixed to assert
"no copper narrower than the class width" and report wider runs as informational. No copper changed.

**Verified after all of the above:** ERC 0 · DRC 0 violations / 0 unconnected / 0 parity ·
bijection 464↔464 · pad-net parity 1290/1290 · 4 zones filled and THERMAL · all 4 netclasses carry
their 7 schematic fields and measure correctly in copper · CPL 246/246. `check_board.py` exits 0.

LESSON (again, in a new costume): "DRC reports 0 unconnected" does not mean the pours are doing
anything. Assert the *mechanism* (pad-connection mode, measured track width), not just the outcome.
