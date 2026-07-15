# twelve-channel — design (schematic + PCB)

12-channel SiPM CSP + shaper + BLR + buffer board, built from the reworked single channel
(`../../../integration/single-channel/design/`) as the single source of truth.

- **Schematic** = KiCad **hierarchical**: the single channel (minus board power entry)
  instantiated 12× as `channel.kicad_sch`, plus a root `twelve-channel.kicad_sch` with the 12
  sheet instances + one common power section (power in + board-to-board daisy + up-rated
  reverse-polarity/PTC block + 470 µF bulk). Per-channel nets auto-scope to `/chNN/<net>`.
- **PCB** = **tile-and-replicate**: the routed single-channel channel row is cloned 12× (offset
  25 mm in Y, refs re-mapped via role, nets re-mapped `/X`→`/chNN/X`); board-wide plane pours
  carry the rails so the router does no per-channel work; only the common section is routed.

## Pipeline (run in order; KiCad 10 bundled Python)

```
PY="C:/Program Files/KiCad/10.0/bin/python.exe"
CLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"

# --- schematic ---
"$PY" gen_sch.py                       # -> channel.kicad_sch, twelve-channel.kicad_sch, .kicad_pro
"$CLI" sch erc twelve-channel.kicad_sch
"$CLI" sch export netlist --format kicadsexpr -o twelve-channel.net twelve-channel.kicad_sch

# --- PCB (needs twelve-channel.net from the step above) ---
"$PY" gen_pcb.py                       # tile x12 + common section + planes + outline (+ .kicad_dru)
"$PY" fill_zones.py                    # fill the 4 plane zones (separate pass; in-memory fill segfaults)
"$PY" polish_silk.py                   # move dense refdes/fields F.Silkscreen -> F.Fab
"$CLI" pcb drc --schematic-parity twelve-channel.kicad_pcb    # gate: 0 / 0 / 0
```

Note: `gen_pcb.py` resets silk and adds visible common-part fields, so **`polish_silk.py` must
run after every `gen_pcb.py`**. The `twelve-channel.net` netlist is the authoritative source
for the PCB's per-pad nets, footprint values, and BOM fields (regenerate it after any schematic
change before re-running `gen_pcb.py`).

## Result

213.2 × 334.7 mm, 4-layer (widened 138 → 180 → 213.2 mm to span the Hammond RM1U1908VBK 1U case —
one board per case, slot-through the front/rear panels; the output/bias MCX row was shifted to the
far edge with F.Cu trace extensions). 468 footprints (464 refdes'd parts + 4 M3), 4 plane
zones. (The BOM lists 500 line-item parts = the 464 placed + the 36 SIP-8 sockets, which
share the module sites' PinSocket_1x08 footprints.)
**DRC 0 violations / 0 unconnected / 0 schematic-parity.** Render: `twelve-channel-3d.png`.
