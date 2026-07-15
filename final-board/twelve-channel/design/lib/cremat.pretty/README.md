# cremat.pretty — project-local footprints

Most parts use **KiCad stock footprint libraries** (see the footprint column in
[../../../docs/hardware/bom.md](../../../docs/hardware/bom.md)). This library holds parts
with no suitable stock footprint:

| Footprint | Part | Source / status |
|---|---|---|
| `MCX_CONMCX013-T` | TE Connectivity / Linx `CONMCX013` 50 Ω MCX board-edge jack (×48) | **Present.** User-downloaded Linx `CONMCX013-T` footprint (`CONMCX013-T.step` 3D model, license in `CONMCX013-LICENSE.txt`), migrated to KiCad 10; shield tabs renumbered to pad 2, 3D `(rotate 270 0 0)` so the coax faces off the edge. Pad 1 = signal; the two shell tabs merged to **pad 2 = shield/GND** to match the `Conn_Coaxial` symbol (pin 1 In, pin 2 Ext). Carries an `Edge.Cuts` cutout (±2.5 × 6.3 mm) — place at the board edge so the cutout merges with the outline. |

Files: `MCX_CONMCX013-T.kicad_mod`, `CONMCX013-T.step`, `CONMCX013-LICENSE.txt`.
