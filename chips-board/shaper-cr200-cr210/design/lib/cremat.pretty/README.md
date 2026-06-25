# cremat.pretty — project-local footprints

Most parts use **KiCad stock footprint libraries** (see the footprint column in
[../../../docs/hardware/bom.md](../../../docs/hardware/bom.md)). This library holds parts
with no suitable stock footprint:

| Footprint | Part | Source / status |
|---|---|---|
| `MCX_CONMCX013_EdgeMount` | TE Connectivity / Linx `CONMCX013` 50 Ω MCX board-edge jack (×36) | **Present.** From SnapMagic/SnapEDA (`CONMCX013.step` 3D model, license in `CONMCX013-LICENSE.txt`), migrated to KiCad 10. Pad 1 = signal; the two shell tabs merged to **pad 2 = shield/GND** to match the `Conn_Coaxial` symbol (pin 1 In, pin 2 Ext). Carries an `Edge.Cuts` cutout (±2.5 × 6.3 mm) — place at the board edge so the cutout merges with the outline. |

Files: `MCX_CONMCX013_EdgeMount.kicad_mod`, `CONMCX013.step`, `CONMCX013-LICENSE.txt`.
