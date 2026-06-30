# INTERFACE — `twelve-channel` final board (Phase C)

> Owned by **C1 board-design**. The contract C2 (models-BOM) and C3 (system-sim) integrate
> against. Status: **ERC 0/0 · DRC 0 errors / 0 unconnected / 0 schematic-parity**, built by
> **TILE-AND-REPLICATE** (route ONE channel tile, clone it ×12 — all 12 channel blocks
> BYTE-IDENTICAL = matched parasitics; then route only the shared power). The board is **12
> generated copies of the frozen single channel** (`integration/single-channel/`) — see R1.
> Real parts carried from the single-channel cell (per-channel design BOM == B3 line × 12);
> board-shared parts (screw terminal, central 470 µF bulk pair, 4× M3) reconciled with C2 —
> **design BOM == C2 `twelve-channel-bom.csv`.** Board **235 × 264 mm**, 48 MCX cutouts on
> Edge.Cuts.

## What this board is — 12 channels of the proven single channel

```
   ┌──────── LEFT long edge (input, 24 MCX) ────────┐   ┌──── RIGHT long edge (24 MCX) ────┐
   │  J_BIAS / J_SIPM  per channel (interleaved)     │   │  J_OUT50 / J_TEST per channel    │
   │  ch01  BIAS->filter->CR-112->CR-200->CR-210->THS3491 buf ->49.9R-> OUT_50              │
   │  ch02  ............................................................................     │
   │   ...   (12 identical bands, signal flows left -> right)                               │
   │  ch12  ............................................................................     │
   └────────────────────────────────────────────────┘   └──────────────────────────────────┘
   shared +12V/GND/-12V 3-pos screw terminal (top-center) · 4× M3 mounting holes (corners)
   4-layer: F.Cu / In1=GND plane / In2=-VDC plane / B.Cu(+VDC pour) — the proven single-ch stackup
```

Each channel is the **frozen Phase-B `channel` cell** reproduced verbatim (CR-112 CSP + SiPM
bias front-end → CR-200 1µs shaper → CR-210 BLR → TI THS3491 CFA buffer, 50 Ω back-term).
Per-channel nets are suffixed `_ch01 … _ch12`; the supply rails are shared.

## R1 — single source of truth (the 12 ARE generated copies)
**Schematic:** the channel circuit is defined in **exactly one place**:
`integration/single-channel/design/gen_sch.py` (`build_spec()`, `PARTS`, …). This board's
`design/gen_sch.py` **imports that module** and emits `build_spec()` **12×** with a `_chNN`
net/ref suffix (shared rails stay global).

**Layout (tile-and-replicate):** the channel LAYOUT is defined once in `design/gen_layout.py`;
`design/gen_tile.py` builds + FreeRoutes **ONE** channel tile (`tile.kicad_pcb`);
`design/replicate_tile.py` **clones that routed tile ×12** (translate by one row pitch, remap
ch01→chNN refs+nets). So the channel layout lives in ONE place and is stamped 12× — all 12
blocks are byte-identical.

**Propagation path** (edit once → all 12 update):
```
SCHEMATIC: edit integration/single-channel/design/gen_sch.py (build_spec/PARTS — the ONE source)
  → run design/gen_sch.py (restamps ×12 → .kicad_sch) → kicad-cli sch export netlist
LAYOUT:    edit design/gen_layout.py (the ONE tile layout)
  → gen_tile.py → export tile.dsn → FreeRoute tile → import tile.ses → fill
  → replicate_tile.py (clone tile ×12 + place commons) → fill_zones → DRC
```
**Demonstrated** (`design/reports/propagation_demo.txt`): (schematic) `PARTS['R_FB']` 976→1240 →
12× `1240`; (layout) all 12 channel blocks verified geometrically identical — **0 footprint-
geometry diffs channel-to-channel at exact 21.0 mm pitch, identical 173 tracks + 29 vias each**.

**Efficiency win:** routed the tile (~91 nets) in **2.4 s**; replicated ×12 with NO per-channel
autoroute; only the shared power (screw terminal + 2 bulk → planes) remains, carried by the
GND/+VDC/−VDC planes (0 unconnected). vs the prior all-12 autoroute: 8–32 min AND the channels
were not identical.

**Byte-faithfulness:** the board's component multiset = the single-channel cell × 12 (0 mismatches
on Value+Footprint+MPN; 48 MCX = 4/ch × 12); per-channel net topology matches the cell.

**Byte-faithfulness verified:** the board's component multiset = the single-channel cell × 12
(0 mismatches on Value+Footprint+MPN; 48 MCX = 4/ch × 12) and every per-channel net's
value+pin signature equals the single channel's (23/23 real nets; the 2 exceptions are KiCad
auto no-connect names on CR-112 pin 3 and THS3491 pin 5 NC).

## R2 — schematic-parity-clean (the manufacturing deliverable)
`kicad-cli pcb drc --schematic-parity --severity-warning` reports **0 parity items**. Fixes
(in `gen_layout.set_fp_fields` + `gen_sch.py`, applied in the tile and the commons):
- **lib-qualified footprint FPIDs** (`SetFPID(LIB_ID(nick, fname))`) matching each symbol's
  Footprint field.
- **MPN / Manufacturer / Distributor PN + Value copied into each footprint** (`SetField`).
- **Mounting holes have real schematic symbols** (`H1..H4`, `Mechanical:MountingHole`) → 0
  `extra_footprint`s.
- `lib_footprint_mismatch` is now **0** (the tile keeps the MCX cutouts on Edge.Cuts exactly as
  the library footprint defines them — no footprint editing — so the board copies match the lib).

## Electrical I/O (per channel; identical to the single channel, suffixed `_chNN`)

| Port | Dir | Connector | Signal | Range / notes |
|------|-----|-----------|--------|---------------|
| `BIAS_IN_chNN` | in | MCX (left edge) | SiPM bias DC | ≤ 60 V (`hv_bias` class 0.6 mm). |
| `SIPM_chNN`    | i/o | MCX (left edge) | detector bias + charge | DC-coupled to filtered bias; HV. |
| `TEST_IN_chNN` | in | MCX (right edge) | test pulse | 47 Ω + 1 pF charge inject → CSP. |
| `OUT_50_chNN`  | out | MCX (right edge) | shaped Gaussian | **Zout 50 Ω**, +67.1 mV/0.5 pC into 50 Ω (B2). |
| `+12V`/`GND`/`-12V` | pwr | one 3-pos screw terminal (J49) | supply | ±12 V; **central 470 µF bulk pair at the entry (CBULK_P/CBULK_N)** + per-channel decoupling + 12× 100 µF distributed bulk inside the cells. |

## DNP / optional blocks (per channel, carried from the cell — 36 DNP total)
| Block | Populated (default) | DNP (default) |
|-------|--------------------|---------------|
| CSP bias filter Rf1/Rf2 | Rf1, Rf2 (10k) | **JP_Rf1, JP_Rf2 (0R)** |
| Shaper CR-210 BLR | **CR-210 (U3)** | **JP_BLR (0R)** |
DNP refs on the PCB: the 36 0R bypass jumpers (3/channel × 12), confirmed `SetDNP(True)` and
flagged `DNP` in the fab BOM.

## Mechanical / stackup
- **Board outline 235.1 × 264.1 mm**, 4-layer (F.Cu GND fill / In1=GND plane / In2=-VDC plane /
  B.Cu=+VDC pour). 12 channel tiles × 21 mm + top/bottom strips → 264 mm.
- **ENCLOSURE (user decision): keep all 48 MCX (per-channel TEST_IN retained); use an enclosure
  DEEPER than the 244 mm 1U-tray spec.** Per-board depth = **264 mm**; width 235 mm holds (2
  boards = 470 < 482 mm rack). No MCX change, no cell change.
- **48 MCX `CONMCX013`** edge jacks split **24 / 24** on the two long edges (BIAS+SIPM left,
  OUT_50+TEST_IN right). **All 48 connector cutouts are ON `Edge.Cuts`** (192 segments) as
  near-edge internal slots — the connector slot is OUTBOARD of the signal pad so pad 1 escapes
  inward (this rotation is what makes the tile routable); a scoped DRC rule
  (`multi-channel-cremat-amplifier.kicad_dru`) exempts the MCX shield pad, which straddles its
  slot by design, from the board-edge-clearance check. The Edge.Cuts gerber contains the outline
  + 48 cutouts (196 contour segments), NOT just the bare rectangle.
- 4× M3 mounting holes (`MountingHole_3.2mm_M3`, H1–H4): top-strip + bottom-strip corners. Match C2.
- 1× Phoenix MKDS 3-pos screw terminal (**1715734**, 5.08 mm), top-center strip. Match C2.
- **Central rail-entry bulk: CBULK_P / CBULK_N = Nichicon UVR1V471MPD, 470 µF / 35 V radial THT**
  (`Capacitor_THT:CP_Radial_D10.0mm_P5.00mm`, DK 493-1084-ND), top strip near J_PWR. CBULK_P
  +12V↔GND, CBULK_N −12V↔GND (C_Polarized pin1 = +). Added at the C2 real-parts gate; backs the
  12× distributed 100 µF. Tall radial parts (D10×16 mm) — clear the deeper enclosure.

## TEST_IN / 48-vs-36 MCX and board height — RESOLVED (user decision)
- The frozen channel cell has **4 MCX** (BIAS/SIPM/TEST/OUT_50). **DECISION: keep all 48 MCX**
  (per-channel TEST_IN retained) and **use a deeper enclosure** — no MCX change, no cell change.
- Board depth **264 mm** (12 × 21 mm tiles + strips); width 235 mm (2 boards = 470 < 482 mm
  rack). The enclosure must be deeper than the original 244 mm 1U-tray spec.

## Part list pointer — design BOM == C2 BOM (Round-2 real-parts gate, RECONCILED)
- Design BOM (this board) = the per-symbol fields, exported to
  `design/fab/multi-channel-cremat-amplifier-bom.csv` (grouped, fielded, DNP-flagged).
- **Verified design BOM == C2 `models-bom/twelve-channel-bom.csv`** on every placed electrical
  part (MPN + board quantity): **0 mismatches** — single-channel cell × 12 + screw terminal
  (1715734 ×1) + central bulk UVR1V471MPD ×2 + 4× M3 holes. C2-only lines are off-board mounting
  hardware (standoffs 24338 ×4, screws PMSSS 3-6 ×8 — not placed on the PCB). C2 owns the priced
  BOM + DNP variants. (Note: C2's screw-terminal footprint string has a cosmetic `.`-vs-`,` typo
  `MKDS-1.5-3`; the real KiCad footprint + this board use `MKDS-1,5-3`; same part 1715734.)

## Verified-by
- ERC: `design/reports/erc.json` = **0 / 0**.
- DRC: `design/reports/drc.json` = **0 errors / 0 unconnected / 0 schematic-parity**, **WITH the
  48 MCX cutouts on Edge.Cuts** (gate = `kicad-cli pcb drc --schematic-parity`). `drc_full.json`
  = **597 cosmetic warnings**: silk_over_copper 199 + silk_overlap 199 + silk_edge_clearance 199
  — **all three at the KiCad CLI per-check report cap of 199**; inherent 0805/jack outline silk
  on a 571-footprint board. **lib_footprint_mismatch = 0** (tile keeps MCX cutouts as the lib
  defines them). All **warnings, no errors**.
- **Silk declutter (`design/polish_silk.py`):** the dense 0805/jack/trim **reference designators
  are moved off F.Silkscreen onto F.Fab** (kept for assembly), removing visible refdes clutter
  (see render), **0 lib churn / 0 errors**. The capped silk checks are inherent 0805 part-outline
  silk; fully clearing them needs deleting all outlines (assembly-useful) — kept.
- Routed: `design/reports/routed-top.png`; 4-layer, **2796 tracks, 816 vias**, 4 plane zones,
  571 footprints (incl. the 2 central bulk caps), 36 DNP. Per channel: 173 tracks + 29 vias,
  **identical across all 12** (matched parasitics).
- Edge.Cuts gerber: outer outline + **48 connector cutouts** (196 contour segments).
- Function (per channel) inherited from B2/single-channel `INTERFACE.md` (unchanged topology).
- Fab package: `design/fab/` (28 gerbers + drill, position CSV, fielded BOM).
