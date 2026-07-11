# INTERFACE — `twelve-channel` final board

> Status: **ERC 0 · DRC 0 errors / 0 unconnected / 0 schematic-parity**. Rebuilt 2026-07-08
> from the reworked single channel (`integration/single-channel/`) as a KiCad **hierarchical**
> design (channel sheet instantiated 12×) with a **tile-and-replicate** layout (one routed
> channel row stamped 12× — all 12 blocks geometrically identical = matched parasitics).
> Board **180 × 335 mm**, 4-layer (widened from 138 mm so the two MCX rows reach the front/back
> bulkheads of a **Hammond RM2U1908** 2U rack case — see `design/gen_pcb.py` `W`, adjustable to
> the box's real internal depth).

## What this board is — 12 copies of the proven single channel + shared power

```
   ┌── LEFT edge: 24 MCX ──┐                                    ┌── RIGHT edge: 24 MCX ──┐
   [ COMMON: J_PWR in · J_DAISY daisy-out · PTC/Schottky reverse-block · 470 µF bulk · 2×M3 ]
   [ SIPM ][TEST]  ch01  filter->CR-112->CR-200->CR-210->THS3491 buf ->49.9R   [OUT_50][BIAS]
   [ SIPM ][TEST]  ch02  ............................................................ [OUT][BIAS]
     ...            ...   (12 identical rows, signal flows left -> right, 25 mm pitch)
   [ SIPM ][TEST]  ch12  ............................................................ [OUT][BIAS]
   [ 2× M3 mounting holes (bottom corners) ]
   4-layer: F.Cu / In1 = GND plane / In2 = -VDC plane / B.Cu = +VDC pour (single-channel stackup)
```

Each channel is the frozen single-channel cell reproduced verbatim (SiPM bias front-end +
CR-112 CSP → CR-200 1 µs shaper → CR-210 BLR → TI THS3491 CFA buffer, 50 Ω back-terminated).
The 4 MCX per channel (SIPM/TEST left edge, OUT_50/BIAS right edge) tile to 24 per long edge.

## Power — one input feeds two stacked boards (24 channels in a 19" rack)

A 19" box can't fit 24 channels on one board, so the system is **two identical 12-channel
boards stacked**. Each board self-protects and passes the raw supply through:

- **`J_PWR`** (3-pos screw terminal): supply in — `+VDC_IN / GND / -VDC_IN`.
- **`J_DAISY`** (3-pos screw terminal): same raw rails, in parallel → short cable to the next
  board's `J_PWR`. So one supply feeds board 1; board 1 daisies to board 2.
- Per board: reverse-polarity **series Schottky** (`D_RP/D_RN`, SS24 2 A) + fault-interrupt
  **PTC** (`F_P/F_N`, ~1.1 A hold — up-rated from the single channel's 0.1 A for 12× current)
  → board rails; **470 µF** central bulk (`C_BULKP/C_BULKN`) backs the 12× distributed 10 µF.
- Board 1's input trace/connector carries **both** boards' current (~0.9-1.1 A/rail); each
  board's protection sees only its own 12 channels (~0.3-0.5 A/rail).

## Nets — hierarchical scoping

Per-channel nets auto-scope per sheet instance: `/ch01/CSP_OUT … /ch12/CSP_OUT`, `/chNN/FE`,
`/chNN/SHVP`, etc. Shared rails are global: `+VDC`, `-VDC`, `GND`. Raw/pre-protection nets
(root sheet): `/+VDC_IN`, `/+VDC_F`, `/-VDC_IN`, `/-VDC_F`. Net classes (in `.kicad_pro`):
`hv_bias` 0.6 mm clearance (bias/FE), `signal` 0.33 mm, `power` 0.5 mm, `Default` 0.2 mm.

## Refs

Flat-contiguous per prefix, channel n striding: U 4/ch (U1-48), R 18/ch (R1-216), C 11/ch
(C1-132), J 4/ch (J1-48), RV 1/ch (RV1-12). Board-level tail: `J49`=J_PWR, `J50`=J_DAISY,
`F1/F2`=PTC, `D1/D2`=Schottky, `C133/C134`=bulk, `H1-H4`=M3. 120 DNP (10/channel: the bias &
BLR bypass jumpers + the DNP-by-default THS3491 buffer block).

## Single source of truth

**Schematic** — `design/gen_sch.py` imports the single-channel `gen_sch.py` and emits
`channel.kicad_sch` (the channel minus board power entry, each symbol carrying a 12-instance
block) + `twelve-channel.kicad_sch` (12 `(sheet)` instances + the common power section) +
`twelve-channel.kicad_pro`. **Layout** — `design/gen_pcb.py` clones the routed single-channel
`channel.kicad_pcb` row 12× (Move by pitch, re-map refs via role, re-net `/X`→`/chNN/X`) and
places+routes the common section once; `fill_zones.py` fills the planes; `polish_silk.py`
moves refdes to F.Fab. Gate: `kicad-cli pcb drc --schematic-parity`.

## Status / open items

- **BOM** — `models-bom/twelve-channel-bom.csv` regenerated (23 line items, 464 parts: 344 FIT
  + 120 DNP), enriched from the single-channel BOM. Generator: `models-bom/gen_bom.py`.
- **Common-power MPNs verified in-stock 2026-07-08** (`models-bom/SOURCING-VERIFICATION-2026-07-08.md`):
  Littelfuse `1812L110/24DR` PTC (1.1 A/24 V), onsemi `SSA24` Schottky (2 A/40 V SMA), Panasonic
  `EEE-FN1V471UP` 470 µF/35 V — all three provisional picks were rejected (obsolete / wrong
  package / fictional) and replaced.
- Daisy-chain cable between boards is user-supplied (3-conductor, ≥1 A/rail).
