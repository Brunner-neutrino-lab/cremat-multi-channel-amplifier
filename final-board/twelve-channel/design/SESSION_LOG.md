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
