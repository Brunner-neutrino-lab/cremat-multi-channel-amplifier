# Box mounting — two boards stacked in a 2U rack case

Two 12-channel boards stacked on standoffs in **one Hammond RM2U1908VBK** 2U vented case
(DigiKey HM1166-ND). The other 3 assembled boards are spares (unboxed). Drawings are the
`*.svg` files here (regenerate with `python gen_drawings.py <png_out_dir>`).

## Box + board

| | mm |
|---|---|
| Box interior (Hammond drawing) | **84.53 H × 415.30 W × 196.85 D** |
| Board | 213.3 (depth, connectors) × 334.8 (width) × 1.6 |
| Board mounting holes | 4× M3 (3.2 mm) at board-x {8.0, 205.2}, board-y {5.0, 329.7} |

## Horizontal placement (drawings 1, 5)

- **Width:** board 334.8 mm centered → **40.25 mm clear each side.**
- **Depth:** board is 16.45 mm **deeper** than the box → protrudes **8.2 mm past each panel**;
  the 24+24 MCX sit proud through the front/rear slots.
- **Standoff holes (bottom cover):** X = **45.25 / 369.95** mm (from the left interior wall),
  Y ≈ **0 / 196.85** mm. ⚠ The hole rectangle (197.2 mm) is 0.35 mm wider than the 196.85 mm
  interior, so the holes land **right on the front/rear panel lines** — the front/rear panels
  need a small corner-relief cutout at X = 45.25 / 369.95 for the standoff columns (they're
  outside the connector-slot span X ≈ 69–356, so the relief is clean).

## Vertical stack (drawings 2, 3, 4) — target 1″ board-to-board

| From → to | height |
|---|---|
| bottom cover → board 1 | **12.7 mm (½″)** standoff |
| board 1 → board 2 | **25.4 mm (1″)** standoff — the board-to-board spec |
| board 2 → top cover | **43.2 mm** air |

Board planes (connector-slot centers): **Z = 13.5 mm** (board 1), **Z = 40.5 mm** (board 2).
Sum: 12.7 + 1.6 + 25.4 + 1.6 + 43.2 = 84.53 ✓.

A standing Cremat module is **~26.5 mm** (socket 4.2 + body ~22.3) — **1.1 mm taller than the
25.4 mm gap**, so **board 1's modules bend** to fit the inter-board gap (as on Cremat's own eval
boards); board 2's modules stand freely in the 43 mm top clearance.

*Standoff note:* the recommended in-stock parts are metric (12 mm / 25 mm), 0.7 / 0.4 mm short of
½″ / 1″. That makes board-to-board 25.0 mm (~0.98″); the 0.4 mm is absorbed by the top air. Source
true 25.4 / 12.7 mm M3 M-F standoffs if exact-inch is required.

## Panels (drawings 3, 4) — machine into the removable front/rear plates

- **2 connector slots** each, ~8 mm tall, X 69.2 → 356.2, at Z = 13.5 (board 1) and Z = 40.5 (board 2).
- **2 standoff-relief cutouts** each, ~8 mm wide, at X = 45.25 / 369.95, from the bottom up to Z ≈ 42.

## Standoff hardware (per box, DigiKey — see `../models-bom/digikey-hand-bom.csv`)

All M3. Both standoffs are **male-female, male-up** (an F-F bottom standoff won't mate with B).

| Role | MPN | DK PN | length |
|---|---|---|---|
| A — bottom cover → board 1 | Würth 971120321 | 732-10406-ND | 12 mm + 6 mm stud |
| B — board 1 → board 2 | Würth 971250321 | 732-971250321-ND | 25 mm + 6 mm stud |
| screw (into A, from under cover) | Keystone 29311 | 36-29311-ND | M3×6 mm pan |
| nut (top of B, fixes board 2) | Keystone 4708 | 36-4708-ND | M3 |

## Assembly (per the described order of operations)

1. Remove front, rear, and top panels. Machine the front/rear panel slots + corner reliefs.
2. Drill the 4 standoff holes in the bottom cover (match the PCB: X 45.25/369.95, Y ~0/196.85).
3. Screw the 4× standoff **A** (12 mm) to the bottom cover from below.
4. Slide **board 1** in through the front; drop onto standoffs A (male studs through the holes).
5. Thread the 4× standoff **B** (25 mm) onto A through board 1 → clamps board 1.
6. Slide **board 2** in; drop onto standoffs B; **fix a nut** on each top stud.
7. Refit the front/rear panels (over the protruding board edges / connectors) and the top.
