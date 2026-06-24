# cremat.pretty — project-local footprints

Most parts use **KiCad stock footprint libraries** (see the footprint column in
[../../../docs/hardware/bom.md](../../../docs/hardware/bom.md)). This library is only for
parts that have no suitable stock footprint:

| Footprint | Part | Status |
|---|---|---|
| `MCX_CONMCX013_EdgeMount` | TE Connectivity Linx `CONMCX013` 50 Ω MCX board-edge jack (×36) | **TO CREATE — import datasheet-verified.** Pad/cutout geometry must come from the TE drawing (or a vetted SnapEDA/Ultra-Librarian part). Not auto-generated here to avoid shipping wrong pad geometry. |

To add it: in KiCad Footprint Editor create `MCX_CONMCX013_EdgeMount.kicad_mod` here, verify
against the TE `CONMCX013` mechanical drawing (signal pad, ground pads, board edge cutout,
courtyard), then assign it to `J_BIAS*`, `J_SIPM*`, `J_OUT*` in the schematic.
