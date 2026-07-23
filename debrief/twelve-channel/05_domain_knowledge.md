# 05 — Domain knowledge (the ECAD craft)

Scoped to what I actually did. Simulation and autorouting are largely `[other-session]`.

---

## Human-readable schematics — generated, not drawn  `C:analog-signal-chain`

**There is no KiCad Python API for schematics.** `pcbnew` handles boards only. `.kicad_sch` must be
written as **s-expression text**. This is the central fact of schematic generation and it shapes
everything below.

### The method that worked

1. **Declare parts in a `SPEC` dict**, one entry per *role* (not per reference):
   `role -> (lib_id, footprint, dnp, {pin: net}, (x, y, rotation))`. Roles (`R_dvp`, `Cf`,
   `U_CSP`) are stable; reference designators are *derived* from role order. Never hardcode `R7`.
2. **Read pin geometry from the symbol library**, never guess it. Parse the `.kicad_sym`, extract
   the symbol block by balanced parens, pull each `(pin ... (at x y angle))`, then transform by
   the instance rotation (schematic Y is **down**, so the rotation is a CCW transform with a
   negated Y):
   ```python
   rx = px*cos(a) - py*sin(a);  ry = px*sin(a) + py*cos(a)
   pin = (G(x) + rx, G(y) - ry)          # G() snaps to the 1.27 mm grid
   ```
3. **Wire pin-to-pin** with an orthogonal-only helper that asserts each segment is H or V.
4. **Drop labels, power symbols and no-connects** at computed pin coordinates.
5. **Auto-place junctions** where ≥3 conductors meet.

### Making it legible (this is most of the work)

A netlist-correct schematic that a human cannot read is a failed deliverable. Concretely:

- **Left-to-right signal spine.** Place the chain along one row, generous spacing, decoupling in a
  top (+rail) / bottom (−rail) band. Reviewers follow signal flow horizontally.
- **Text placement is a solved-per-symbol-class problem.** A vertical 2-pin part wants its
  ref/value stacked to the *right* (pins are top/bottom); a horizontal one wants ref above / value
  below. **Watch out:** `Device:D_Schottky` has *horizontal* pins at rot 0, unlike `R`/`C`/fuses —
  so its text rule is rotated 90° relative to the others. I got this wrong and diodes rendered
  with text over their own wires.
- **Rotated symbols mangle text.** KiCad mirrors horizontal *justify* for a 180°-rotated symbol, so
  a right-stacked value renders *over* the body. Pre-flip the justify at rot 180. Keep the text
  *angle* upright with `tang = (180 - (rot % 180)) % 180`.
- **Ground symbols must point away from the part.** A `GND` dropped on a pin whose wire exits
  upward renders its bars *into* the body. Give each one a short stub in the away-direction and
  rotate it (`0`=down, `180`=up, `90`/`270`=right/left — verify by rendering; I had to flip one).
- **Long values collide across columns.** `"PTC 1.1A 24V"` is ~11 mm wide; two rails 12.7 mm apart
  will overlap. Either widen the column pitch or shorten the value.
- **Verify legibility by rendering a zoomed crop**, not by reasoning. See `render_crop.py`.

### Wire taps — the rule that matters

KiCad's GUI connects wires **end-to-end**. A wire that merely *ends part-way along* another wire is
a fragile construct: `kicad-cli`'s netlister accepts it, the GUI's connectivity is stricter, and
KiCad's own cleanup pass **merges collinear wires and deletes junctions it deems redundant** —
dissolving the tap. Observed directly: KiCad re-saved my 116 wires / 36 junctions as **89 / 3**.

**Therefore, generate T-taps like this:**
1. Never let a component pin sit *on* a run — give it its own perpendicular **stub**.
2. **Pre-split** the run at every attach point so all three wires meet **end-to-end**.
3. Emit a junction **only** where ≥3 wire *endpoints* coincide.

Two invariants worth asserting in the generator (both cheap, both caught real bugs):

```
# (a) no wire endpoint may land mid-span on another wire
# (b) every point where >=3 wire ends meet must have a junction
```

The independently-developed reference project converged on exactly this rule, which is good
evidence it is the correct general practice, not a local workaround.

### Hierarchy

For N identical channels: a **root** sheet with N `(sheet)` blocks + one child per channel.
- Only the **root** carries `(sheet_instances (path "/" (page "1")))`. A child that declares it
  makes the GUI open the *child* as the top sheet. (KiCad's own 7-sheet demo also lists only `/`.)
- The `.kicad_pro` needs `schematic.top_level_sheets` pointed at the root, or the GUI opens the
  child — **and `kicad-cli` ignores this key**, so every headless check passes while the GUI
  misbehaves.
- Symbol instance paths are `/<root-uuid>/<sheet-uuid>`; the sheet block's own instance path is
  `/<root-uuid>`.
- **Two valid designs for N channels:** one child file instantiated N times (symbols carry an
  N-path `(instances)` block, sharing one symbol UUID), or **N separate child files** each
  instantiated once. Both work — the other project verified the shared-instance case explicitly.
  I ended on N files because it makes footprint↔symbol paths unique *by construction*.

---

## Placement  `C:repeated-block`

"Properly placed" here meant: **route one channel well by hand, then replicate**. Ordering within
the cell: mechanical/connectors first (they are pinned by the enclosure), then the signal chain
left-to-right, then decoupling adjacent to its pin.

For the tiled board, placement is arithmetic: `Duplicate()` + `Move(0, n*pitch)`. Coordinates come
from the cell, not from a placement algorithm.

**Judging placement before routing:** run DRC with only courtyard/edge rules meaningful — courtyard
overlaps and board-edge clearance are the pre-route gate. Also a 3D render, which catches
mechanical nonsense (connectors facing inward, parts over mounting holes) far faster than reading
coordinates.

**Mechanical coupling is a first-class input.** Board width was derived from the rack enclosure's
internal depth so MCX barrels reach the bulkheads. Because the board was *generated*, changing it
was one constant (`W`). Had it been hand-drawn, it would have been a re-layout.

---

## Edge-mounted connectors (a genuinely hard case)  `C:edge-launch`

48 MCX jacks straddle the board edge. What this requires:

1. The footprint carries its cutout on **`Dwgs.User`**, *not* `Edge.Cuts` — otherwise each of the
   48 footprints tries to cut its own board edge.
2. The **outline builder reads back** each placed footprint's `Dwgs.User` notch and subtracts it
   from the board rectangle → 24 notches per long edge.
3. A custom **`.kicad_dru`** waives edge clearance for exactly that footprint:
   ```
   (rule "MCX edge-mount shield pad straddles its slot by design"
      (constraint edge_clearance (min 0mm))
      (condition "A.Library_Link == 'cremat:MCX_CONMCX013-T'"))
   ```
4. The 3D model needs `(rotate (xyz 270 0 0))` so the barrel faces off the edge rather than
   through the board.

---

## Libraries  `G`

- **Project-local libs** in `lib/cremat.kicad_sym` + `lib/cremat.pretty/`, wired up by
  `sym-lib-table` / `fp-lib-table` using `${KIPRJMOD}`. Both tables must exist beside the
  `.kicad_pro` or the GUI cannot resolve `cremat:` items.
- **Prefer stock footprints when pad geometry matches.** The SIP-8 socket became the stock
  `Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical` after verifying pads *and*
  courtyard were identical to the header it replaced — one less local file to maintain.
- **Verify against the datasheet, and against the distributor page, before ordering.** Several
  "provisional" MPNs proved obsolete, wrong-package, or fictional.
- **Library-vs-board drift is a real warning class.** `lib_footprint_mismatch` fires when the
  board's embedded copy differs from the library. The fix that preserves the routed board is to
  export the **as-built** footprint back into the library:
  ```python
  fp = <one placed instance>
  fp.SetPosition(pcbnew.VECTOR2I(0,0)); fp.SetOrientationDegrees(0)
  fp.SetReference("REF**"); [p.SetNetCode(0) for p in fp.Pads()]
  pcbnew.FootprintSave(lib_dir, fp)     # library copy now == as-built
  ```

---

## Checks  `G`

**ERC.** Severities live in `.kicad_pro` under `erc.rule_severities`. Confirm
`pin_not_connected` is at `error` and `erc.erc_exclusions` is empty before trusting a 0.
```
CLI sch erc --severity-all -o erc.rpt board.kicad_sch
```

**DRC + netclasses.** Netclasses are defined in `.kicad_pro` under `net_settings.classes`, assigned
by glob in `net_settings.netclass_patterns`. For hierarchical names, patterns need the sheet
wildcard: `*/FE`, `*/N_filt`, `*BIAS*`. A pattern without it matches nothing and the class is
silently never applied.

> **A netclass must carry its SCHEMATIC fields too** — `wire_width`, `bus_width`, `line_style`
> (plus `diff_pair_gap`, `diff_pair_width`, `microvia_diameter`, `microvia_drill`). A class with
> only PCB fields **breaks eeschema connectivity for every net in that class**. This cost more time
> than anything else in the project; full story in `06_gotchas.md`.

**What the automated checks miss** (needed eyeballs):
- Schematic legibility entirely.
- GUI-only connectivity failures (the whole `06_gotchas.md` #1 saga).
- Polarity/rotation of polarised parts in the fab's own preview.
- Whether the mechanical story is right — 3D render, every time.

**Verify the rule actually bit.** Do not infer from "DRC passed" that a netclass applied — DRC
would use the same broken assignment. Measure the copper:
```python
w = {round(t.GetWidth()/1e6,4) for t in b.GetTracks() if re.search(r'BIAS|/FE$', t.GetNetname())}
# -> {0.4}  matches the hv_bias track_width => the class really was applied
```

---

## 3D  `G`

Models attach per-footprint via `(model "path" (offset)(scale)(rotate))`. Sourcing: vendor STEP
when available, stock `${KICAD10_3DMODEL_DIR}/...` otherwise, and substitute a same-package stock
model when KiCad ships none (a 1812 PTC borrows the 1812 resistor model).

```
CLI pcb render --side top --quality high --width 1600 --height 1100 -o top.png board.kicad_pcb
```

**Missing models fail silently** — a wrong `${KIPRJMOD}` path yields no error, just an absent part.
The render *is* the check: count what you expect to see.

---

## Fab outputs  `C:jlcpcb`

Gerbers + Excellon drill from `kicad-cli pcb export gerbers` / `drill`. Then the fab-specific pair:
- **BOM** `Comment,Designator,Footprint,JLCPCB Part #` — LCSC part numbers, "Basic" parts preferred
  (Extended incur a per-line fee).
- **CPL** `Designator,Mid X,Mid Y,Layer,Rotation` — **fitted SMD only**; exclude DNP and
  through-hole.

Constraints encoded: 4-layer 1.6 mm standard stackup; **no controlled impedance** (justified: the
fastest signal is a ~1 µs pulse, knee ≈ 350 kHz, so a quarter-wave is ~100 m — transmission-line
effects are irrelevant, and outer traces are grounded-coplanar anyway, not microstrip); assembly
tier and quantity split (fab qty ≥ assembly qty is fine and cheap).

**Pre-fab checklist as practiced:** DRC 0/0 · ERC 0 · parity + path bijection · zones filled ·
3D render inspected · polarised-part rotation checked in the fab preview · BOM MPNs re-verified
live at the distributor · CPL count equals fitted-SMD count · board outline/slots within fab
capability · a human has opened the project in the GUI and read it.
