# cremat.pretty — project-local footprints

Most parts use **KiCad stock footprint libraries** (see the footprint column in
[../../../docs/hardware/bom.md](../../../docs/hardware/bom.md)). This library holds parts
with no suitable stock footprint:

| Footprint | Part | Source / status |
|---|---|---|
| `MCX_CONMCX013-T` | TE Connectivity / Linx `CONMCX013` 50 Ω MCX board-edge jack (×4 per channel: BIAS/SIPM/TEST/OUT_50) | **In use** (`FP_MCX` = `cremat:MCX_CONMCX013-T`). User-downloaded Linx `CONMCX013-T` footprint (`CONMCX013-T.step` 3D model, `(rotate 270 0 0)` so the coax faces off the edge); shield tabs renumbered to **pad 2 = shield/GND** to match the `Conn_Coaxial` symbol. Carries an `Edge.Cuts` cutout (±2.5 × 6.3 mm) — placed at the board edge so the cutout merges with the outline. The old SnapEDA `MCX_CONMCX013_EdgeMount` is retained in the lib but unused. |

Files: `MCX_CONMCX013-T.kicad_mod` (in use), `CONMCX013-T.step`, `CONMCX013-LICENSE.txt`; plus the
retained-but-unused `MCX_CONMCX013_EdgeMount.kicad_mod` + `CONMCX013.step`.
