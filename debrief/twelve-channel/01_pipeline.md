# 01 — The pipeline as it actually ran

`CLI` below means `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`; `PY` means
`C:\Program Files\KiCad\10.0\bin\python.exe`. Both are called by **full path** — neither is on
`PATH`. All commands are run from the directory containing the project files unless stated.

---

## Stage 0 — Inherited input (not mine)

**Input:** `integration/single-channel/design/channel.kicad_pcb` — one fully routed, DRC-clean
channel row, plus `channel.kicad_sch` and `channel.kicad_pro`. `[verified-artifact]`

This is the single most important architectural decision in the project and it is **`C:repeated-block`**:
*route one cell by hand (or by autorouter) once, to a high standard, then replicate it
programmatically.* A 12-channel board is not 12× the routing work; it is 1× the routing work plus
a tiling script. Everything downstream depends on that cell being genuinely finished.

---

## Stage 1 — Generate the hierarchical schematic  `G`

**Purpose:** produce a KiCad schematic that a human can review, from a single source of truth.

**Inputs:** `integration/single-channel/design/gen_sch.py` (imported as a module — it owns the
per-channel drawing), stock KiCad symbol libraries, local `lib/cremat.kicad_sym`.
**Outputs:** `channel_ch01..ch12.kicad_sch` (12 child sheets), `twelve-channel.kicad_sch` (root:
12 sheet blocks + the common power section), `twelve-channel.kicad_pro`.

```
PY gen_sch.py
```

**Acceptance check (executable):**
```
CLI sch erc --severity-all -o erc.rpt twelve-channel.kicad_sch      # must print "Found 0 violations"
```
plus two home-grown invariants that KiCad will not check for you (both in `04_kernel.md`):
- **no wire endpoint lands mid-span on another wire** (every T-tap is end-to-end), and
- **every point where ≥3 wire ends meet has a junction**.

**Human gate:** yes, and it is the real gate. A human opens the `.kicad_pro` in the KiCad GUI and
reads the schematic. Renders and ERC are not sufficient — see `06_gotchas.md` #1.

**Failure modes:**
- Text overlapping other text / symbols (cosmetic, but it is what a reviewer sees first).
- Rotated symbols placing their reference/value text upside-down or mirrored.
- Wire taps that ERC and the netlist call connected but the **GUI** does not.

**Cost:** generation is ~2 s. The review loop around it consumed days.

---

## Stage 2 — Export the netlist  `G`

```
CLI sch export netlist --format kicadsexpr -o twelve-channel.net twelve-channel.kicad_sch
```

**Output:** `twelve-channel.net` — the authoritative interface between schematic and board. It
carries, per component: `(ref)`, `(value)`, `(footprint)`, arbitrary `(field)`s (MPN,
Manufacturer, Distributor PN), `(sheetpath (names ...) (tstamps ...))` and `(tstamps ...)`.
`[verified-artifact]`

**This file is the contract.** `gen_pcb.py` reads it for footprint IDs, values, BOM fields, pad
nets *and* the footprint↔symbol UUID paths. Regenerate it whenever the schematic changes, before
running the PCB generator. It is gitignored as a build artifact.

**Cost:** ~3 s.

---

## Stage 3 — Generate the PCB by tiling  `C:repeated-block`

**Inputs:** the routed single-channel `.kicad_pcb`, `twelve-channel.net`.
**Output:** `twelve-channel.kicad_pcb`.

```
PY gen_pcb.py
```

What it does, in order (this ordering matters):
1. Load the routed single-channel board; classify its items into *channel-row* vs *common* by Y
   coordinate (a clean horizontal split — verified 0 items straddling the boundary).
2. For n in 1..12: `Duplicate()` every channel footprint/track/via, `Move()` by n × pitch,
   restride the reference (`R6` → `R18` → … `R132`), rewrite pad nets `/X` → `/chNN/X`, and
   **set the footprint's UUID path from the netlist** (see `06_gotchas.md` #2 — this is where a
   nasty bug lived).
3. Place the common power section from the netlist (footprints loaded from library by FPID) and
   route it with explicit track/via calls.
4. Build the board outline as a rectangle **with 48 MCX notches cut into it**, read back from
   each placed MCX footprint's `Dwgs.User` cutout.
5. Add plane zones (F.Cu GND, In1 GND, In2 −VDC, B.Cu +VDC), mounting holes, and write a
   `.kicad_dru` waiving `edge_clearance` for `A.Library_Link == 'cremat:MCX_CONMCX013-T'`.

**Acceptance check:** DRC, below. Also a footprint census (48 MCX, 468 total) and the
**path bijection** check (`04_kernel.md`).

**Failure modes seen:** bulk-cap pads open until plane vias were added; mask bridges in the
hand-routed common section; mounting holes colliding with edge MCX; common-part field mismatches
because the tiler pulled values from the board rather than the netlist.

**Cost:** ~20 s generation. `[recalled]`

---

## Stage 4 — Fill zones (separate pass — mandatory)  `G`

```
PY fill_zones.py
```

**Why it is a separate script:** calling `ZONE_FILLER.Fill()` inside the same process that just
built the board **segfaults headlessly**. The working pattern is: generator saves the board and
exits; a second process loads the saved file, fills, saves. This is inherited project lore and it
held for the whole project. `[recalled]` — I never re-provoked the segfault deliberately.

---

## Stage 5 — The check gates  `G`

```
CLI pcb drc --severity-all --schematic-parity -o drc.rpt twelve-channel.kicad_pcb
CLI sch erc --severity-all -o erc.rpt twelve-channel.kicad_sch
```

Final state: **DRC 0 violations / 0 unconnected; ERC 0**. `[verified-run]`

**Critical caveat, and the most valuable single fact in this debrief:**
`kicad-cli pcb drc --schematic-parity` does **not** do the pad-net-vs-schematic comparison that
the GUI's "Test for parity between PCB and schematic" does. It only performs footprint-level
checks (courtyard, footprint filters, pad-type). It will happily report *"Found 0 schematic parity
issues"* while the GUI reports hundreds. `[verified-run]` — confirmed by observing 0 from the CLI
and 199+ in the GUI on the same files.

So I wrote my own parity gate in `pcbnew` (full source in `04_kernel.md`): load the board, load the
exported netlist, and compare **every pad's net** against the schematic's net for that
`(ref, pad)`. Final: **0 mismatches across 1290 pads**. `[verified-run]`

And a second gate, the **path bijection**: the set of footprint UUID paths on the board must equal
the set of symbol UUID paths in the netlist, 1:1, no orphans either way. Final: **464 ↔ 464,
bijection true**. `[verified-run]`

---

## Stage 6 — Human-review artifacts  `G`

```
CLI sch export pdf -o twelve-channel.pdf twelve-channel.kicad_sch
CLI pcb render --side top --quality high --width 1600 --height 1100 -o board3d_top.png twelve-channel.kicad_pcb
```

For zoomed schematic inspection I rasterised the PDF with KiCad's **bundled PyMuPDF** and cropped
in millimetre coordinates — this turned out to be far more useful than full-page renders, because
schematic defects are only visible at high zoom. Script in `04_kernel.md` (`render_crop.py`).
`[verified-run]`

**Trap:** exporting the *PCB* to PDF and naming it `twelve-channel.pdf` produces a file that looks
like "PCB artwork on a schematic page" and confuses reviewers. The schematic PDF comes from
`sch export pdf`, not `pcb export pdf`. `[verified-artifact]`

---

## Stage 7 — Fab outputs  `C:jlcpcb`

Gerbers + Excellon drill, then two BOMs:
- **JLCPCB assembly**: `bom-…-jlc.csv` (`Comment,Designator,Footprint,JLCPCB Part #`) and
  `cpl-…-jlc.csv` (`Designator,Mid X,Mid Y,Layer,Rotation`) — 246 placements, **FIT SMD only**
  (DNP and through-hole excluded).
- **DigiKey hand-solder**: everything the assembler will not place (edge MCX, SIP-8 sockets,
  trimpots, screw terminals, enclosure).

Generated by `models-bom/gen_bom.py` and `models-bom/gen_purchasing.py`. `[verified-artifact]`

**Human gate:** yes — polarity/rotation of the two electrolytics and two Schottkys must be
eyeballed in JLC's parts-review screen, because KiCad→JLC rotation conventions differ for
polarised parts.

---

## The loops that actually happened

The idealised pipeline above ran maybe twice. What really happened:

**Loop A — schematic legibility (many iterations).**
generate → render/PDF → human reads → "labels overlap", "ground symbols point into the
connector", "this looks unconnected" → fix generator → regenerate. Each iteration is cheap
(seconds) but each *review* is a human round-trip. This loop is unavoidable and should be
**planned for**, not treated as rework.

**Loop B — placement/route/DRC (inherited, single-channel).** `[other-session]`

**Loop C — the connectivity hunt (the expensive one).** Documented fully in `06_gotchas.md`.
Roughly: human reports taps unconnected in GUI → I "verify" with ERC/netlist/parity → all clean →
I declare it fixed → human reports it still broken → repeat. Broken only when I stopped trusting
the automated gates and started bisecting minimal generated projects against a known-good one.
**Cost: the majority of the project's final phase.** Root cause was one missing field in a JSON
project file.

**Loop D — sourcing.** part chosen → check stock/price → out of stock or wrong package → respecify
→ update BOM → update docs. Ran with parallel sub-agents doing live vendor checks; several
"provisional" MPNs turned out to be obsolete, wrong-package, or outright fictional, so **every**
part number was re-verified against a live distributor page before ordering. `[recalled]`
