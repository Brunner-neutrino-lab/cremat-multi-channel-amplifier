# twelve-channel / design (C1) — tile-and-replicate pipeline

The **12-channel final board**, built by **TILE-AND-REPLICATE**: route ONE channel tile, clone
it ×12 (all channels byte-identical = matched parasitics), then route only the shared power.
Single source of truth (R1) + schematic-parity-clean (R2).

## Pipeline (regenerate the whole board)
```
cd final-board/twelve-channel/design
PY="C:/Program Files/KiCad/10.0/bin/python.exe"
CLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
JAVA="<tools>/jdk-25.0.3+9-jre/bin/java.exe" ; JAR="<tools>/freerouting-2.2.4.jar"

# --- schematic (×12 from the frozen cell) ---
$PY gen_sch.py                                                  # 12× schematic (imports the cell)
$CLI sch erc multi-channel-cremat-amplifier.kicad_sch          # ERC 0
$CLI sch export netlist --format kicadsexpr -o multi-channel-cremat-amplifier.net \
      multi-channel-cremat-amplifier.kicad_sch
# --- PHASE 1: build + route ONE channel tile ---
$PY gen_tile.py                                                # tile.kicad_pcb (channel ch01)
$PY -c "import pcbnew;b=pcbnew.LoadBoard('tile.kicad_pcb');pcbnew.ExportSpecctraDSN(b,'tile.dsn')"
$JAVA -jar $JAR -de tile.dsn -do tile.ses -mp 10              # ~2 s (just one channel!)
$PY -c "import pcbnew;b=pcbnew.LoadBoard('tile.kicad_pcb');pcbnew.ImportSpecctraSES(b,'tile.ses');\
        [z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL) for z in b.Zones()];\
        pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard('tile.kicad_pcb',b)"
# --- PHASE 2: clone the routed tile ×12 + place commons + planes ---
$PY replicate_tile.py                                          # 12 identical channel blocks
$PY fill_zones.py                                             # board-wide planes
$PY polish_silk.py                                            # cosmetic: dense refdes -> F.Fab
$PY fill_zones.py
$CLI pcb drc --schematic-parity multi-channel-cremat-amplifier.kicad_pcb   # 0/0/0 + 0 parity
```

## R1 — single source of truth
- **Schematic:** `gen_sch.py` imports `integration/single-channel/design/gen_sch.py` and emits
  `build_spec()` ×12 with a `_chNN` suffix. Edit the cell → regenerate → all 12 schematics update.
- **Layout:** the channel LAYOUT lives once in `gen_layout.py`; `gen_tile.py` routes ONE tile;
  `replicate_tile.py` clones it ×12 (translate + remap ch01→chNN). Edit the tile → re-run
  replicate → all 12 blocks update **identically** (verified: 0 geometry diffs, 173 tracks +
  29 vias per channel). Proof: `reports/propagation_demo.txt`.

## R2 — schematic-parity-clean
`gen_layout.set_fp_fields` writes lib-qualified FPIDs + copies MPN/Manufacturer/Distributor PN +
Value into every footprint; `gen_sch.py` gives mounting holes real symbols → 0 parity.
`lib_footprint_mismatch = 0` (the tile keeps the MCX cutouts on Edge.Cuts exactly as the library
footprint defines them — no footprint editing).

## MCX edge cutouts (the fab-blocker fix)
The 48 connector slots are ON Edge.Cuts by construction (the tile's 4 MCX cutouts × 12). The jack
rotation puts the slot OUTBOARD of the signal pad (left rot −90, right rot +90) so pad 1 escapes
inward — this is what makes the tile routable. A scoped rule (`*.kicad_dru`) exempts the MCX
shield pad (straddles its slot by design) from the board-edge-clearance check.

## Files
- `gen_sch.py` — 12× schematic generator (imports the frozen cell — R1).
- `gen_layout.py` — shared layout constants + the ONE channel LAYOUT + helpers.
- `gen_tile.py` — build the single channel tile (Phase 1).
- `replicate_tile.py` — clone the routed tile ×12 + commons + planes (Phase 2).
- `fill_zones.py` / `polish_silk.py` — plane fill + cosmetic silk declutter.
- `finalize_edges.py` — diagnostic (confirms 192 MCX cutout segs on Edge.Cuts).
- `tile.kicad_pcb` — the routed single-channel tile (the layout source).
- `multi-channel-cremat-amplifier.{kicad_sch,kicad_pcb,kicad_pro,net,kicad_dru}` — the board.
- `lib/` — project libs (cremat modules + MCX). `fab/` — order package. `reports/` — gates +
  routed-top.png + propagation_demo.txt.

See `../INTERFACE.md` for the contract.
