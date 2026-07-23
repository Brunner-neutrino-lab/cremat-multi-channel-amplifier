# EE Pipeline Debrief — session `twelve-channel`

**Single-file edition.** This is the complete debrief from one of the two Claude Code sessions
that carried a 12-channel SiPM preamplifier board from concept to fabrication-ready outputs. It is
self-contained: everything needed is inline, because you have no access to the repo it describes.

| | |
|---|---|
| **Date** | 2026-07-22 |
| **Role slug** | `twelve-channel` (the final-board session) |
| **Repo** | `multi-channel-cremat-amplifier` (private) |
| **Commit** | `42b380037f07de6acff862079fc07dfe6718b660` |
| **Toolchain** | Windows 11 · KiCad 10.0.3 · KiCad's bundled Python 3.11.5 · FreeRouting 2.2.4 |
| **Outcome** | Fab-ready: DRC 0/0, ERC 0, gerbers + JLCPCB BOM/CPL + DigiKey hand-BOM generated |

## How to read this

Eight sections, originally eight files, concatenated in order. Each is delimited by a
`FILE:` banner.

| section | what it gives the bootstrap |
|---|---|
| `00_overview` | context and scope boundaries |
| `01_pipeline` | the stages **as they actually ran**, loops included |
| `02_environment` | exact toolchain, and how Python binds to KiCad |
| `03_tools_inventory` | every tool built, with reuse ratings |
| **`04_kernel`** | **conventions + 4 full scripts + a blank template — the generative core** |
| `05_domain_knowledge` | the ECAD craft: schematic generation, placement, libraries, checks, fab |
| **`06_gotchas`** | **12 defects ranked by cost, and where the hours went** |
| `07_bootstrap_recommendations` | phase/gate structure + **the ten facts** |

**If you read only two sections, read `04_kernel` and `06_gotchas`.** The kernel is what lets a
future session *generate* tools instead of being handed descriptions of them. The gotchas are the
negative knowledge — the expensive, least-volunteered kind.

## Evidence tags

Applied to substantive claims, per the debrief protocol:

- `[verified-run]` — the command was executed during the debrief and behaved as documented
- `[verified-artifact]` — not re-run, but the output artifact was inspected on disk
- `[recalled]` — from session context only, unverified
- `[other-session]` — the other session's territory; reported only as boundary, not reconstructed
- `[shared]` — both sessions touched it; my side only

Heavy stages (routing, simulation, exports) were deliberately **not** re-run to upgrade a tag.

## Reusability ratings

- `G` — general to any KiCad board project
- `C:<class>` — general to a named class, e.g. `C:repeated-block`, `C:jlcpcb`, `C:edge-launch`
- `P` — this board only; included as a worked example

The bootstrap should be built from `G` and `C`. `P` is illustration.

## The one-sentence headline

Four independent automated gates (ERC, netlist export, `--schematic-parity`, and a custom pcbnew
pad-net check) all reported **green for weeks** while the board's schematic was, in the GUI,
visibly broken — because **`kicad-cli` never reads `.kicad_pro`**, and the defect was a netclass
missing its schematic fields. The most important thing this debrief transmits is *which checks are
structurally blind to what*.

## What is NOT here

The other session's debrief covers: the single-channel cell design, SPICE simulation, and
FreeRouting autorouting. Where those touch my work I mark the boundary and stop.


---

<!-- ============================================================ -->
<!-- FILE: 00_overview.md -->
<!-- ============================================================ -->

# 00 — Overview

| | |
|---|---|
| **Date** | 2026-07-22 |
| **Role slug** | `twelve-channel` |
| **Repo root** | `C:\Users\darro\OneDrive - Yale University\Desktop\multi-channel-cremat-amplifier` |
| **Git commit** | `42b380037f07de6acff862079fc07dfe6718b660` ("Fix schematic connectivity: netclasses were missing their SCHEMATIC fields") `[verified-run]` |
| **Host** | Windows 11 Home 10.0.26200, PowerShell 5.1 + git-bash `[verified-run]` |

---

## The project

A **12-channel SiPM charge-sensitive preamplifier / Gaussian shaper** board for a neutrino-physics
lab. Each channel is: MCX coax bias input → optional RC bias filter → AC-coupling cap → **Cremat
CR-112** charge-sensitive preamp (SIP-8 module) → **CR-200-1µs** Gaussian shaper → optional
**CR-210** baseline restorer → optional **THS3491** ×2 buffer → 49.9 Ω back-terminated MCX output.
Twelve of those, plus one shared bipolar (±12 V) power-entry section with PTC + Schottky
reverse-protection and bulk electrolytics.

What made it complex, in rough order of pain:

1. **Repetition at scale.** 12 identical channels → 468 footprints, 464 schematic symbols, 1290
   pads, 271 nets. Everything had to be *generated*, never hand-drawn, or it would never stay
   consistent. `[verified-run]`
2. **Mixed-technology parts.** Through-hole SIP-8 sockets (Cremat modules plug in), edge-mounted
   MCX jacks that straddle a routed slot in the board outline, 0805 SMD passives, and a
   SOIC-8-EP op-amp — in one board, one BOM, one assembly flow.
3. **48 edge-mount connectors.** The MCX footprint carries an edge notch; the board outline has
   to be *cut* by 24 notches per long edge, and DRC's edge-clearance rule has to be waived for
   exactly that footprint via a custom `.kicad_dru` rule.
4. **Populate-or-bypass variants.** Two optional blocks (CR-210 BLR, THS3491 buffer) are
   DNP-by-default with 0 Ω bypass jumpers. The BOM, the CPL and the DRC all have to agree about
   which of two mutually exclusive paths is fitted.
5. **Mechanical coupling.** The board width is a *function of* the rack enclosure's internal
   depth, because the MCX barrels must reach through front and rear bulkheads.

The board reached fabrication-ready: DRC 0 violations / 0 unconnected, ERC 0, gerbers + drill +
JLCPCB BOM/CPL generated, DigiKey hand-solder BOM priced, enclosure selected. `[verified-run]`

---

## The scope I owned

I was the **final-board session**: everything under `final-board/twelve-channel/`.

- `design/gen_sch.py` — generate the 12-channel hierarchical schematic (root + 12 child sheets)
- `design/gen_pcb.py` — generate the PCB by tiling the routed single-channel row ×12, plus the
  common power section, board outline with MCX notches, plane zones, mounting holes, `.kicad_dru`
- `design/fill_zones.py`, `design/polish_silk.py` — post-processing passes
- `models-bom/gen_bom.py`, `models-bom/gen_purchasing.py` — BOM + purchasing/sourcing documents
- Fab output generation (gerber/drill/CPL/BOM for JLCPCB), enclosure + ordering documentation
- The library work: local `cremat.pretty` footprints and `cremat.kicad_sym` symbols
- **All of the connectivity debugging** described in `06_gotchas.md` — the single most expensive
  episode of the project

I also **edited the single-channel generator** (`integration/single-channel/design/gen_sch.py`,
694 lines) extensively, because the 12-channel generator imports it as a module and reuses its
`layout_channel()` / `layout_power()` / symbol-emitter functions. That file is therefore
`[shared]` territory: I own the schematic-drawing internals I changed; the original single-channel
design intent is the other session's. `[verified-run]` on file sizes.

## The other session's territory

`[recalled]` — I did not verify these and should not be trusted on details:

- The **single-channel cell** itself: circuit topology, part selection, the reviewed
  `integration/single-channel/design/channel.kicad_pcb` that my tiler clones. It was routed and
  DRC-clean before I touched it.
- **SPICE simulation** under `sim/` — pole-zero cancellation, shaping-time verification, the
  trimpot P/Z procedure. I never ran it. `sim/netlists/` exists on disk. `[verified-artifact]`
- The **earlier sub-boards** under `chips-board/` (csp-cr112, shaper-cr200-cr210) which were the
  Phase-A proving grounds for the Cremat symbols and footprints.
- **FreeRouting autorouting** of the single channel (`docs/FREEROUTING.md`,
  `export_dsn.py`/`import_ses.py`). I inherited its routed output; I re-ran the DSN/SES round-trip
  only once and mostly worked from the already-routed row. `[shared]`

Separately: during the final debugging I consulted a **different Claude session working on a
different board** (`Desktop\low-frequency-amplifier`, a ramp-amp/AA-filter project). That session
served as a *known-good reference implementation* of a generated hierarchical KiCad project, and
diffing against it eliminated four wrong hypotheses in one pass. Its files are quoted in
`06_gotchas.md` where they were decisive. `[verified-artifact]` — I read its files directly.

---

## The pipeline from my seat, in one line

**Single-channel routed cell (given) → generate 12-ch hierarchical schematic → export netlist →
tile the routed cell ×12 + place/route the common power section → fill zones → DRC/ERC/parity
gates → 3D render + PDF for human review → fab outputs (gerber/drill/CPL/BOM) → purchasing docs.**

The loop that actually dominated wall-clock was not any of those stages. It was
**generate → human opens it in the KiCad GUI → human sees something the automated gates cannot
see → fix generator → regenerate**. Every gate I had (`kicad-cli sch erc`, `kicad-cli pcb drc`,
netlist export, pcbnew pad-net comparison) is blind to a whole class of defect, and the human
eye in the GUI was the only instrument that caught them. See `06_gotchas.md`.


---

<!-- ============================================================ -->
<!-- FILE: 01_pipeline.md -->
<!-- ============================================================ -->

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


---

<!-- ============================================================ -->
<!-- FILE: 02_environment.md -->
<!-- ============================================================ -->

# 02 — Environment

## OS

Windows 11 Home, **10.0.26200**. `[verified-run]`

Two shells were in play and they are **not** interchangeable:
- **PowerShell 5.1** (the user's default). No `&&` chaining (use `;`), no `grep`/`head`/`tail`
  (use `Select-String`, `-TotalCount`, `-Tail`), backtick escapes, `2>$null`.
- **git-bash** (what I mostly used). POSIX tools available, but **MSYS path translation** applies:
  a `/c/Program Files/...` argument passed to a *native* `.exe` is rewritten to `C:\Program
  Files\...`, while the same string embedded in a Python heredoc is **not** — Windows Python then
  cannot open it. Pass paths as `argv`, or write them as `C:/...`. This cost me a debugging cycle.
  `[verified-run]`

**Recommendation for the bootstrap:** state the shell explicitly in every command block, and
prefer full `C:/...` forward-slash paths, which both shells and Python accept.

## KiCad

**KiCad 10.0.3**, installed to `C:\Program Files\KiCad\10.0\`. `[verified-run]`

Nothing KiCad is on `PATH`. Every invocation uses a full path:

```
C:\Program Files\KiCad\10.0\bin\kicad-cli.exe     # CLI: erc, drc, export, render
C:\Program Files\KiCad\10.0\bin\python.exe        # the interpreter that can import pcbnew
C:\Program Files\KiCad\10.0\share\kicad\symbols\  # stock symbol libs (*.kicad_sym)
C:\Program Files\KiCad\10.0\share\kicad\footprints\ # stock footprint libs (*.pretty)
C:\Program Files\KiCad\10.0\share\kicad\demos\    # ← treat as a reference corpus, see below
```

**`share/kicad/demos/` is an underrated asset.** It is a corpus of KiCad-authored files you can
diff your generated output against — I used it to check what schema `(version ...)` KiCad actually
writes, how it formats `(wire ...)`/`(junction ...)`, and whether a 7-sheet hierarchical root
lists more than one path in `(sheet_instances)` (it does not). When you generate KiCad files, this
is your ground truth for "what does a real one look like". `[verified-run]`

## Python ↔ KiCad binding

**This is the single most important environment fact.** `[verified-run]`

- The `pcbnew` module is **only** importable from KiCad's own bundled interpreter,
  `C:\Program Files\KiCad\10.0\bin\python.exe` (Python **3.11.5**, `pcbnew.GetBuildVersion()` →
  `10.0.3`).
- There is **no system Python** on this machine at all (`python3` resolves to the Microsoft Store
  stub and fails). `[verified-run]`
- No venv, no `PYTHONPATH` tricks, no `pip install pcbnew`. **Do not try to make a venv see
  pcbnew.** Just call KiCad's interpreter by full path.

Consequence: every tool in this repo is written to run under that interpreter, and the dependency
set is *whatever KiCad ships*, not something you choose.

### What KiCad 10.0.3's interpreter ships (checked now) `[verified-run]`

| module | version | used for |
|---|---|---|
| `pcbnew` | 10.0.3 | all board manipulation |
| `fitz` (PyMuPDF) | 1.28.0 | rasterising schematic PDFs for zoomed visual inspection |
| `PIL` (Pillow) | 12.2.0 | image handling |
| `numpy` | 2.4.2 | available, unused by my tools |
| `requests` | 2.34.1 | available, unused by my tools |
| **`scipy`** | **absent** | — |
| **`matplotlib`** | **absent** | — |

### What my tools actually import `[verified-run]`

Only the standard library plus `pcbnew`:

```
pcbnew, os, sys, re, csv, json, math, uuid, importlib.util
```

**There is no `requirements.txt` and none is needed.** A filtered `pip freeze` would be
misleading: the tools have *zero* third-party dependencies beyond what KiCad bundles. That is a
deliberate property worth preserving — it means a fresh machine needs only a KiCad install.

The one exception is my visual-inspection helper, which uses the **bundled** `fitz`/`PIL`. Still no
install step.

## External binaries

**FreeRouting 2.2.4** (autorouter) + a Temurin JRE, under `C:\Users\darro\tools\`: `[verified-run]`

```
C:\Users\darro\tools\freerouting-2.2.4.jar
C:\Users\darro\tools\jdk-21.0.11+10-jre\
C:\Users\darro\tools\jdk-25.0.3+9-jre\
```

Both JRE 21 and 25 are present; recipe is in `docs/FREEROUTING.md`. Headless invocation needed a
**dead-proxy workaround** (FreeRouting tries to phone home; the documented fix points it at a
non-routable proxy so it fails fast instead of hanging). `[recalled]` — the autoroute stage was
mostly the other session's; I inherited the routed cell. Treat FreeRouting details as
`[other-session]`.

**No SPICE engine in my scope.** Simulation was the other session's (`sim/`). `[other-session]`

## Environment variables / path setup

Effectively none. No `KICAD*` env vars were set by my tools. Two path-ish conventions matter
*inside* KiCad files:

- **`${KIPRJMOD}`** — expands to the directory of the `.kicad_pro`. Used for project-local library
  and 3D-model references, e.g.
  `(model "${KIPRJMOD}/lib/cremat.pretty/CONMCX013-T.step" ...)`. If a 3D model path is wrong,
  the model **silently vanishes from renders** with no error. `[recalled]`
- **`${KICAD10_3DMODEL_DIR}`** — stock 3D model root, e.g.
  `${KICAD10_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_1812_4532Metric.step`. Note the version number
  is baked into the variable name; it changes between KiCad majors. `[verified-artifact]`

Project-local libraries are wired up with two table files next to the `.kicad_pro`:

```
sym-lib-table    (lib (name "cremat")(type "KiCad")(uri "${KIPRJMOD}/lib/cremat.kicad_sym"))
fp-lib-table     (lib (name "cremat")(type "KiCad")(uri "${KIPRJMOD}/lib/cremat.pretty"))
```

Both are required for the GUI to resolve `cremat:` items when the project is opened. `[verified-run]`

## Known-good combination

```
Windows 11 (10.0.26200) + KiCad 10.0.3 + its bundled Python 3.11.5 + FreeRouting 2.2.4 on Temurin JRE 21/25
```

## Known-bad / version sensitivities

1. **Schema version strings must be real.** `gen_sch.py` at one point emitted
   `(version 20260306)` — a date-stamp that exists nowhere in KiCad. Real KiCad-10 values observed
   in the demo corpus: `20241229`, `20250114`, `20250513`, `20250610`. I settled on **`20250610`**,
   matching a known-good generated project. A fictional/future version invites KiCad to treat the
   file as "newer than me". `[verified-run]`
2. **Headless `ZONE_FILLER.Fill()` segfaults** when called in the same process that built the
   board. Fill zones in a **separate process** on the saved file. `[recalled]`
3. **`kicad-cli pcb drc --schematic-parity` is not the GUI's parity check** — see `06_gotchas.md`.
   `[verified-run]`
4. **`kicad-cli` never reads `.kicad_pro`.** Any defect that lives in the project file is
   invisible to every CLI gate. This is the root of the project's worst bug. `[verified-run]`


---

<!-- ============================================================ -->
<!-- FILE: 03_tools_inventory.md -->
<!-- ============================================================ -->

# 03 — Tools inventory

All run under `C:\Program Files\KiCad\10.0\bin\python.exe`. All take **no CLI arguments** — paths
are module constants resolved relative to `HERE = os.path.dirname(os.path.abspath(__file__))`.
That is a real convention of this repo, discussed critically in `04_kernel.md`.

## Summary

| path | purpose | reuse | state |
|---|---|---|---|
| `integration/single-channel/design/gen_sch.py` (694 L) | Draw one channel + power entry as a real wired schematic; **also the shared drawing library** the 12-ch generator imports | `C:analog-signal-chain` | alive `[shared]` |
| `final-board/twelve-channel/design/gen_sch.py` (324 L) | 12-ch hierarchical schematic: 12 child sheets + root + `.kicad_pro` | `C:repeated-block` | alive |
| `final-board/twelve-channel/design/gen_pcb.py` (349 L) | Tile the routed cell ×12, place/route common section, outline+notches, zones, DRU | `C:repeated-block` | alive |
| `integration/single-channel/design/gen_pcb.py` (327 L) | Single-channel board generator | `C:analog-signal-chain` | alive `[other-session]` |
| `final-board/twelve-channel/design/fill_zones.py` (53 L) | Separate-process zone fill (+ netclass self-heal) | `G` | alive |
| `integration/single-channel/design/fill_zones.py` (44 L) | same, single-channel | `G` | alive `[shared]` |
| `final-board/twelve-channel/design/polish_silk.py` (24 L) | Move refdes silkscreen → F.Fab to clear silk-overlap warnings | `G` | alive |
| `final-board/twelve-channel/models-bom/gen_bom.py` (149 L) | Project BOM from the netlist, DNP-aware, qty-tiered pricing | `G` | alive |
| `final-board/twelve-channel/models-bom/gen_purchasing.py` (220 L) | Purchasing/sourcing doc: per-vendor line items, spares, enclosure | `C:ordering` | alive |
| `integration/single-channel/design/export_dsn.py` (19 L) | Board → Specctra `.dsn` for FreeRouting | `G` | alive `[other-session]` |
| `integration/single-channel/design/import_ses.py` (18 L) | FreeRouting `.ses` → board | `G` | alive `[other-session]` |
| `chips-board/*/gen_sch.py`, `hardware/gen_sch.py` | Phase-A sub-board generators (CSP, shaper) | `P` | superseded |
| — `gen_mcx_step.py` | generated an MCX 3D model | `P` | **dead** — deleted once the vendor's real STEP was obtained `[recalled]` |

Line counts `[verified-run]`. Below, only the tools I owned are detailed.

---

## `final-board/twelve-channel/design/gen_sch.py` — 12-ch hierarchical schematic

**Interface:** `PY gen_sch.py`, no args. Writes into its own directory.

**Inputs:** imports `integration/single-channel/design/gen_sch.py` as a module (via
`importlib.util.spec_from_file_location`) and **monkey-patches its emitter functions** to switch
from single-instance to per-channel output. Also reads
`integration/single-channel/design/channel.kicad_pro` as the template for the project file.

**Outputs:** `channel_ch01..ch12.kicad_sch`, `twelve-channel.kicad_sch`, `twelve-channel.kicad_pro`.

**Format/API touched:** writes `.kicad_sch` **as text** (no KiCad API for schematics — see
`05_domain_knowledge.md`), and `.kicad_pro` as JSON.

**Key internals worth carrying forward:**

- `BOARD_ROLES` — the roles that belong to the *root* (power entry) rather than a channel. The
  child is "the single channel minus these".
- `stride_ref(ref, n)` — turns ch1's `R6` into chN's `R{6 + (n-1)*18}`, using a per-prefix count
  computed once from the role list. Reference numbering must be *derived*, never hand-maintained.
- `CH[0]` — a module-level "current channel" the patched emitters read. Crude but effective.
- `remap_uuids(text, n)` — after generating a child's text, rewrite every `(uuid "...")` to a
  per-channel value via `uuid5`, while leaving `(path ...)` references untouched. This is what
  makes 12 structurally identical sheets have unique element identities.
- `build_pro()` — copies the single-channel `.kicad_pro`, then fixes: netclass patterns for
  hierarchical net names, `top_level_sheets` (else the GUI opens the *child*), the sheet list, and
  — critically — **fills the schematic fields on every netclass** (`06_gotchas.md` #1).

**Side effects / idempotency:** fully idempotent. Deterministic `uuid5` from a fixed namespace
means re-running produces byte-identical files. **This is a deliberate and load-bearing property**
— it makes "regenerate and diff" a safe, meaningful operation, and it lets `git status` answer
"did my change do anything unexpected?"

**Limitations:** the geometry of the channel is entirely inherited from the single-channel module;
this file only handles replication and the root. Sheet placement on the root (2 columns × 6 rows)
is hardcoded.

**To generalise:** parameterise `NCH`, the role split, and the sheet grid. The multi-instance ↔
per-file decision (below) should be a flag.

---

## `final-board/twelve-channel/design/gen_pcb.py` — tiling board generator

**Interface:** `PY gen_pcb.py`, no args.

**Inputs:** `integration/single-channel/design/channel.kicad_pcb` (routed cell),
`twelve-channel.net`. **Outputs:** `twelve-channel.kicad_pcb`, `twelve-channel.kicad_dru`.

**API touched:** `pcbnew` — `LoadBoard`, `Duplicate`, `Move`, `SetReference`, `SetPath`,
`SetNetCode`/`GetNetsByName`, `FootprintLoad`, zone + track + via construction, `Edge_Cuts`
shapes, `Save`.

**Notable internals:**

- `parse_netlist()` — regex parser producing `{ref: (fpid, sym_path, value, fields)}` and
  `{(ref,pad): net}`. **`sym_path` must be `sheetpath.tstamps + component.tstamps`** — building it
  from the component tstamp alone silently collapses all 12 instances onto one path
  (`06_gotchas.md` #2).
- `dup(item)` — `Duplicate(False)` with a `TypeError` fallback to `Duplicate()`, papering over an
  API signature difference.
- The channel/common split by Y coordinate, with an assertion that nothing straddles.
- Outline builder that reads each placed MCX's `Dwgs.User` notch and subtracts it from the
  rectangle.
- Emits a `.kicad_dru` rule waiving `edge_clearance` for the MCX library link.

**Side effects:** overwrites the board wholesale. **Not** safe to run against a board a human has
hand-edited — it regenerates from the cell. Idempotent given the same inputs.

**Limitations:** the common power section's placement and routing are hardcoded coordinates. Row
pitch, board width and the notch geometry are constants. Widening the board for the enclosure was
a one-parameter change (`W`), which was the payoff of generating rather than drawing.

---

## `fill_zones.py` — separate-process zone fill  `G`

Loads the saved board, `ZONE_FILLER(board).Fill(board.Zones())`, saves. Exists as a separate
process **because doing it in-process segfaults headlessly**.

The 12-ch copy also **self-heals the netclass patterns**: it checks that the `hv_bias` class is
still present/assigned and restores it with a warning if the GUI has flattened the `.kicad_pro`.
That defensive check exists because opening the project in the GUI could rewrite the project file
and silently drop netclass patterns. `[recalled]`

## `polish_silk.py`  `G`

Moves reference designators from `F.SilkS` to `F.Fab` to clear silk-overlap warnings on a dense
board. 24 lines. Cosmetic but it is the difference between a DRC report you read and one you
ignore.

## `models-bom/gen_bom.py`  `G`

Reads `twelve-channel.net`, groups by MPN, applies DNP rules, emits the project BOM with
`MPN`/`Manufacturer`/`Distributor PN` columns. Handles the **up-rated common parts** (the 12-ch
power entry uses higher-current PTCs/diodes/bulk caps than the single channel) by overriding
values per role, and appends non-schematic line items (the SIP-8 sockets — real BOM lines that
exist nowhere in the netlist, because the schematic has module symbols, not sockets).

**Generalisable lesson:** a BOM is *not* a projection of the netlist. It needs (a) DNP variants,
(b) parts that exist mechanically but not electrically, (c) quantity tiers, (d) spares.

## `models-bom/gen_purchasing.py`  `C:ordering`

Emits the purchasing document: per-vendor grouped line items, quantity = `ceil(per_board × boards
× 1.2)` for hand-soldered parts (spares) but exact for the enclosure, distributor part numbers,
prices, and the JLC/DigiKey split. Encodes which parts the assembler places vs which the human
solders.


---

<!-- ============================================================ -->
<!-- FILE: 04_kernel.md -->
<!-- ============================================================ -->

# 04 — The kernel: how to generate new tools

This is the reusable core. A future bootstrap should ship these conventions + exemplars so a
session can *write* the tool it needs, rather than looking one up.

---

## The shared skeleton

**Interpreter.** Every tool runs under `C:\Program Files\KiCad\10.0\bin\python.exe`. Shebang is
cosmetic on Windows; the docstring carries the real invocation.

**Paths are module constants, not CLI args.**
```python
HERE = os.path.dirname(os.path.abspath(__file__))
PCB  = os.path.join(HERE, "twelve-channel.kicad_pcb")
```
Every tool lives *next to* the artifact it operates on. This is deliberate: it removes an entire
class of "ran it on the wrong board" errors, and it makes the tools self-locating when a session
resumes weeks later. **Trade-off, stated honestly:** it also makes them un-reusable across
projects without editing. For a one-board repo this was right. A bootstrap shipping *generic*
tools should accept `argv[1]` with these constants as defaults.

**Load → mutate → save, one task per file.** No tool does two stages. `gen_pcb` builds,
`fill_zones` fills, `polish_silk` polishes. Chaining is the human's (or the doc's) job. This is
what made the pipeline debuggable — when something broke, one script owned it.

**Units.** `pcbnew` internal units are **nanometres**, integers. Always convert explicitly:
```python
pcbnew.FromMM(0.6)              # mm -> nm  (use for every literal dimension)
t.GetWidth() / 1e6              # nm -> mm  (use for every report)
pcbnew.VECTOR2I(x_nm, y_nm)     # points are nm
```
Never write a bare number into a pcbnew setter. Schematic files, by contrast, are **millimetres as
text**, and the schematic connection grid is **1.27 mm (50 mil)** — snap every coordinate:
```python
def G(v): return round(round(float(v) / 1.27) * 1.27, 4)
```

**Determinism.** Identity comes from `uuid5` over a fixed namespace and a semantic key, never
`uuid4`:
```python
NS = uuid.UUID("b1c2d3e4-0000-4000-8000-000000000000")
def uid(*p): return str(uuid.uuid5(NS, ":".join(str(x) for x in p)))
```
So re-running a generator produces a **byte-identical** file. This is worth more than it sounds:
`git status` becomes a regression test, and "regenerate and diff" is a safe operation you can do
constantly. The other reference project used `uuid4` and lost this.

**Reporting and exit.** Tools `print()` a one-line summary of what they changed
(`"filled 4 zone(s)"`, `"moved 468 footprint text fields"`). Long-form reports go to files that
the CLI writes (`erc.rpt`, `drc.rpt`). Exit codes were **not** used systematically — that is a
weakness; see the template below, which fixes it.

**Idempotency.** Every tool is safe to re-run. Generators overwrite from source; mutators check
before acting (`if f.GetLayer() == pcbnew.F_SilkS`).

**Proving it worked.** Every stage has an *executable* check, not a claim. See "Acceptance
checks" below — this is the part I got wrong for most of the project and it is the most important
thing in this document.

---

## Exemplar 1 — `fill_zones.py` (in full)

Shows: separate-process pattern, the self-heal guard, zone construction, mm↔nm.

```python
#!/usr/bin/env python3
"""Fill copper zones on the saved 12-channel board (separate pass; in-memory Fill during
construction segfaults). Zones (from gen_pcb.py): In1=GND plane, In2=-VDC plane, B.Cu=+VDC
pour. Adds an F.Cu GND ground-fill (priority 2) so top-side GND ties around the cloned tracks.
FULL pad connection keeps the planes low-Z (no starved-thermal spokes).

  "C:/Program Files/KiCad/10.0/bin/python.exe" fill_zones.py
"""
import os, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "twelve-channel.kicad_pcb")
PRO = os.path.join(HERE, "twelve-channel.kicad_pro")

def ensure_netclasses():
    # Zone fill uses the project netclass clearances (hv_bias = 0.6 mm). A KiCad GUI save can
    # FLATTEN the .kicad_pro (netclasses gone) -> the fill silently violates the HV rule and a
    # subsequent DRC passes vacuously (bit us twice on 2026-07-11). Heal + warn loudly.
    if "hv_bias" in open(PRO, encoding="utf-8").read():
        return
    print("*" * 78)
    print("WARNING: twelve-channel.kicad_pro had NO netclasses (GUI save flattened it?).")
    print("         Restoring from gen_sch.build_pro() before filling. If KiCad has this")
    print("         project open, CLOSE IT WITHOUT SAVING or it will clobber it again.")
    print("*" * 78)
    import importlib.util
    spec = importlib.util.spec_from_file_location("tw_gen_sch", os.path.join(HERE, "gen_sch.py"))
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    g.build_pro()

def main():
    ensure_netclasses()
    b = pcbnew.LoadBoard(PCB)
    gnd = b.FindNet("GND")
    bb = b.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    m = pcbnew.FromMM(0.6)
    have = {(z.GetLayer(), z.GetNetname()) for z in b.Zones()}
    if gnd and (pcbnew.F_Cu, "GND") not in have:
        z = pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNetCode(gnd.GetNetCode())
        z.SetAssignedPriority(2)
        ch = z.Outline(); ch.NewOutline()
        for (px, py) in [(x0 + m, y0 + m), (x1 - m, y0 + m), (x1 - m, y1 - m), (x0 + m, y1 - m)]:
            ch.Append(px, py)
        b.Add(z)
    n = len(list(b.Zones()))
    for z in b.Zones():
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print("filled %d zone(s)" % n)

if __name__ == "__main__":
    main()
```

## Exemplar 2 — `polish_silk.py` (in full)

The minimal well-formed tool: 24 lines, one job, idempotent, reports a count.

```python
#!/usr/bin/env python3
"""Silk-screen polish for the dense 12-channel board: move every footprint's Reference (and any
Value) from F.Silkscreen to F.Fab. On a board this tightly tiled the refdes silk clips the board
edge / overlaps neighbours / sits over pads (all cosmetic DRC). The refs stay fully legible on the
F.Fab assembly layer. Run after gen_pcb.py, before the final DRC.

  "C:/Program Files/KiCad/10.0/bin/python.exe" polish_silk.py
"""
import os, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "twelve-channel.kicad_pcb")

def main():
    b = pcbnew.LoadBoard(PCB)
    n = 0
    for fp in b.GetFootprints():
        for f in fp.GetFields():                 # Reference, Value, MPN, Manufacturer, Distributor PN
            if f.GetLayer() == pcbnew.F_SilkS:
                f.SetLayer(pcbnew.F_Fab); n += 1
    pcbnew.SaveBoard(PCB, b)
    print("moved %d footprint text fields F.Silkscreen -> F.Fab" % n)

if __name__ == "__main__":
    main()
```

## Exemplar 3 — `check_parity.py` (the gate `kicad-cli` does not give you)

**Ship this in the bootstrap.** `kicad-cli pcb drc --schematic-parity` does *not* compare pad nets
(`06_gotchas.md` #3). This does, plus the footprint↔symbol path bijection. Both checks caught real
defects that every built-in gate reported as clean.

```python
#!/usr/bin/env python3
"""Real board<->schematic parity: (1) every pad's net matches the schematic netlist, and
(2) footprint UUID paths and symbol UUID paths are a bijection. Exits 1 on any mismatch.

  CLI sch export netlist --format kicadsexpr -o board.net board.kicad_sch
  "C:/Program Files/KiCad/10.0/bin/python.exe" check_parity.py board.kicad_pcb board.net
"""
import sys, re, pcbnew

def netlist_maps(path):
    t = open(path, encoding="utf-8").read()
    pad_net, sym_path = {}, {}
    for m in re.finditer(r'\(net\b(.*?)(?=\(net\b|\(libparts|\Z)', t, re.S):
        nm = re.search(r'\(name "([^"]*)"', m.group(1))
        if not nm: continue
        for r, p in re.findall(r'\(node\s+\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', m.group(1)):
            pad_net[(r, p)] = nm.group(1)
    comps = t[t.index('(components'):t.index('(libparts')]
    for m in re.finditer(r'\(comp\b(.*?)(?=\(comp\b|\Z)', comps, re.S):
        ref = re.search(r'\(ref "([^"]+)"\)', m.group(1))
        sp  = re.search(r'\(tstamps "(/[0-9a-fA-F/-]*)"\)', m.group(1))   # sheetpath (has slashes)
        ct  = re.search(r'\(tstamps "([0-9a-fA-F-]{36})"\)', m.group(1))  # component tstamp
        if ref and sp and ct:
            sym_path[ref.group(1)] = sp.group(1) + ct.group(1)
    return pad_net, sym_path

def main(pcb, net):
    pad_net, sym_path = netlist_maps(net)
    b = pcbnew.LoadBoard(pcb)
    bad = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.GetPadName(): continue
            want = pad_net.get((fp.GetReference(), p.GetPadName()))
            if want != p.GetNetname():
                bad.append("%s.%s PCB='%s' SCH='%s'" % (fp.GetReference(), p.GetPadName(),
                                                        p.GetNetname(), want))
    fps = [f.GetPath().AsString() for f in b.GetFootprints() if f.GetPath().AsString()]
    sch = set(sym_path.values())
    bij = (sch == set(fps)) and (len(fps) == len(set(fps)))
    print("pad-net mismatches : %d" % len(bad))
    for x in bad[:20]: print("   ", x)
    print("path bijection     : %s  (%d symbols <-> %d footprints, %d unique)"
          % (bij, len(sch), len(fps), len(set(fps))))
    if not bij:
        print("   symbols w/o footprint:", len(sch - set(fps)))
        print("   footprints w/o symbol:", len(set(fps) - sch))
    return 0 if (not bad and bij) else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
```

## Exemplar 4 — `render_crop.py` (visual inspection at zoom)

Schematic defects are invisible at full-page scale. Render a **millimetre-addressed crop** of any
page using KiCad's bundled PyMuPDF. This was the single most useful debugging tool I built.

```python
#!/usr/bin/env python3
"""Render a mm-addressed crop of a KiCad-exported PDF page (schematic or board).

  CLI sch export pdf -o sch.pdf board.kicad_sch
  PY render_crop.py sch.pdf 1 out.png 108 165 148 196 800     # x0 y0 x1 y1 (mm) [dpi]
"""
import sys, fitz                      # PyMuPDF ships inside KiCad's python
pdf, page, out = sys.argv[1], int(sys.argv[2]) - 1, sys.argv[3]
x0, y0, x1, y1 = (float(v) for v in sys.argv[4:8])
dpi = float(sys.argv[8]) if len(sys.argv) > 8 else 300.0
MM2PT = 72.0 / 25.4
pg = fitz.open(pdf)[page]
pix = pg.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0),
                    clip=fitz.Rect(x0 * MM2PT, y0 * MM2PT, x1 * MM2PT, y1 * MM2PT))
pix.save(out)
print("saved %s %dx%d px  clip(mm)=(%.1f,%.1f)-(%.1f,%.1f)" % (out, pix.width, pix.height, x0, y0, x1, y1))
```

---

## Blank template for a generated tool

```python
#!/usr/bin/env python3
"""<One line: what this does and when in the pipeline it runs.>

<Why it exists / any non-obvious constraint (e.g. "separate pass because X segfaults").>

  "C:/Program Files/KiCad/10.0/bin/python.exe" <name>.py [<artifact>]
"""
import os, sys, pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "<board>.kicad_pcb")

def check(board):
    """Executable acceptance check. Return (ok: bool, message: str). MUST NOT mutate."""
    return True, "…"

def main():
    b = pcbnew.LoadBoard(PCB)

    n = 0
    # … single, idempotent task. Guard every mutation so re-running is a no-op:
    #     if <not already done>: <do it>; n += 1

    ok, msg = check(b)
    if not ok:
        print("FAIL: %s" % msg); return 1
    pcbnew.SaveBoard(PCB, b)
    print("<verb> %d item(s); check: %s" % (n, msg))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Requirements the kernel assumes

- **Interpreter:** KiCad 10.0.3's bundled Python 3.11.5, by full path.
- **Third-party deps: none.** stdlib + `pcbnew`; `fitz`/`PIL` for rendering, both bundled. No
  `requirements.txt`, no venv. Preserve this.
- **External binaries:** only FreeRouting 2.2.4 + a Temurin JRE, and only for autorouting.

## Rules a generated tool must satisfy

1. **Headless.** No GUI, no interactive prompts.
2. **Single task.** If it needs "and then", it is two tools.
3. **Idempotent.** Re-running changes nothing the second time.
4. **Deterministic.** `uuid5`, sorted iteration, no `Math.random`-equivalent. Byte-identical
   re-runs.
5. **Carries its own executable acceptance check** — and the check must be capable of *failing*.
   A check that cannot fail is decoration.
6. **Explicit units** at every boundary (`FromMM` in, `/1e6` out).
7. **Prints what it changed**, and exits non-zero on failure.
8. **Never runs in the same process as a `ZONE_FILLER.Fill()`** it did not itself isolate.

## Acceptance checks: the hard-won part

The project's worst failure was not a bad tool; it was **a suite of green checks that were
structurally blind to the defect**. When designing a check, ask *what class of defect can this
never see?* For KiCad specifically:

| gate | blind to |
|---|---|
| `kicad-cli sch erc` | anything in `.kicad_pro` (never reads it); GUI-only connectivity |
| `kicad-cli sch export netlist` | same; it is *lenient* about wire taps the GUI rejects |
| `kicad-cli pcb drc --schematic-parity` | **pad-net comparison** — footprint checks only |
| `check_parity.py` (mine, by `(ref,pad)`) | UUID-path linkage; anything project-file-scoped |
| pcbnew geometry checks | whatever the GUI's connectivity engine does differently |
| **all of the above** | **anything that depends on `.kicad_pro`** |

The only gate that saw the final bug was **a human with the project open in the GUI**. Budget for
that; do not pretend it is optional.


---

<!-- ============================================================ -->
<!-- FILE: 05_domain_knowledge.md -->
<!-- ============================================================ -->

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


---

<!-- ============================================================ -->
<!-- FILE: 06_gotchas.md -->
<!-- ============================================================ -->

# 06 — Gotchas, ranked by cost

---

## #1 — A netclass without its SCHEMATIC fields breaks schematic connectivity  `G`

**Cost: days. The single most expensive defect of the project.** `[verified-run]`

**Symptom.** In the KiCad GUI, wire T-taps read as unconnected. Clicking a stub showed
`unconnected-(C4-Pad1)` instead of `+VS_F`. Dragging a component left its stub behind. Pins drew
hollow endpoint circles. DRC's schematic-parity tab showed **199+** warnings, and
`Tools → Update PCB from Schematic` **duplicated every component on the board** (then produced
500+ DRC errors).

**Meanwhile:** `kicad-cli sch erc --severity-all` → **0 violations**. `kicad-cli sch export
netlist` → every net correct, `C4.1 → /ch01/+VS_F`. My own pcbnew pad-net parity → **0 mismatches
across 1290 pads**. Path bijection → **464 ↔ 464, true**. Every automated gate green, for weeks.

**Root cause.** The four netclasses in `.kicad_pro` under `net_settings.classes` were **PCB-only**:

```json
{ "name": "hv_bias", "clearance": 0.6, "track_width": 0.4,
  "via_diameter": 0.8, "via_drill": 0.4, "pcb_color": "...", "schematic_color": "...",
  "priority": -1, "tuning_profile": "" }          // 9 keys
```

Missing, versus a known-good project's 14-key class:

```
wire_width, bus_width, line_style, diff_pair_gap, diff_pair_width,
microvia_diameter, microvia_drill
```

**A netclass with no `wire_width` breaks eeschema's connectivity for every net assigned to that
class.** Wires stop joining at T-taps.

**Fix.** Fill the schematic defaults on every class (KiCad's own values):

```python
SCH_DEFAULTS = {"wire_width": 6, "bus_width": 12, "line_style": 0,
                "diff_pair_gap": 0.25, "diff_pair_width": 0.2,
                "microvia_diameter": 0.3, "microvia_drill": 0.1}
for cls in pro["net_settings"]["classes"]:
    for k, v in SCH_DEFAULTS.items():
        cls.setdefault(k, v)
```

**Why it hid so well — and this is the transferable lesson:**

- **Netclasses only exist when the project is loaded.** Open the same `.kicad_sch` standalone
  (double-click from Explorer, no `.kicad_pro`) and it is perfectly connected.
- **`kicad-cli` never reads `.kicad_pro` at all.** So ERC, netlist export, and everything built on
  the exported netlist are *structurally incapable* of seeing any project-file defect.
- The PCB half of the netclass was fine, so the routed board was never affected — the 288 bias
  tracks measure 0.4 mm, proving `hv_bias` was applied during routing.

**Diagnostic procedure that finally worked** (after three wrong root causes):

1. Build a **minimal generated project** using the same emitters — root + one child + one T-tap.
   It worked, in both contexts.
2. Bisect toward the real design by swapping in one real component at a time: real child
   (with a minimal root), then real root (with minimal children). **Both failed** — which looked
   like two independent causes.
3. The trap: I had also copied the **real `.kicad_pro`** into both of those, an uncontrolled
   variable. Every *passing* variant had a minimal project file; every *failing* one had the real
   one. That was the actual common factor, sitting in plain sight.
4. Once isolated: drop one `net_settings` sub-key at a time. `classes` removed → works.
5. Diff my class dicts against a known-good project's → 7 missing keys.

**Rule to carry forward: when the GUI disagrees with the CLI, bisect the *project*, not just the
schematic — and hold the `.kicad_pro` fixed while you bisect the files.**

---

## #2 — Footprint↔symbol UUID paths collapsed (468 footprints, 47 distinct paths)  `C:repeated-block`

**Cost: high (caused the duplicate-on-update disaster).** `[verified-run]`

**Symptom.** `Update PCB from Schematic` added a duplicate of every component. GUI parity
complained. Ref-based checks all passed.

**Root cause.** KiCad links a footprint to its symbol by **UUID sheet-path**, not by reference.
`gen_pcb.parse_netlist` grabbed only the 36-char *component* tstamp:

```python
uid = re.search(r'\(tstamps "([0-9a-fA-F-]{36})"\)', body)   # component tstamp only
d.SetPath(pcbnew.KIID_PATH("/" + uid))                        # -> "/<symbol_uuid>"
```

But the netlist gives **two** tstamps per component:

```
(sheetpath (names "/ch08/") (tstamps "/559c5ed0-…/"))    <- per-instance sheet path
(tstamps "b615c419-…")                                   <- symbol uuid
```

The correct path is **`sheetpath.tstamps + component.tstamps`** = `/559c5ed0-…/b615c419-…`. The
36-char regex can't match the slash-bearing sheet path, so it silently used the symbol UUID alone
— and since one child sheet instantiated 12× shares one symbol UUID per role, all 12 instances
collapsed onto the same path.

Proof it's the right rule: on the **flat** single-channel board the sheet path is just `/`, so
`/symbol` is already correct — which is exactly why that board was never broken.

**Fix.** Build the full path; root-level parts collapse to `/symbol` automatically.

**Check that catches it:** the **bijection** — the set of footprint paths must equal the set of
symbol paths, 1:1, no orphans. A ref-based parity check reads "clean" while linkage is completely
broken, because the *nets* can be right while the *UUIDs* are wrong.

---

## #3 — `kicad-cli pcb drc --schematic-parity` does not compare pad nets  `G`

**Cost: high — it was the false all-clear underneath #1 and #2.** `[verified-run]`

It performs only *footprint-level* parity (courtyard, footprint filters, pad-type). It prints
`Found 0 schematic parity issues` while the GUI's "Test for parity between PCB and schematic"
reports hundreds on the same files.

**Mitigation:** write your own (`check_parity.py` in `04_kernel.md`) comparing every pad's net to
the exported netlist, **plus** the UUID-path bijection. Note even that pair is blind to #1, because
both consume the CLI-exported netlist.

---

## #4 — KiCad merges collinear wires and deletes "redundant" junctions  `G`

**Cost: medium-high; sent me down a long wrong path.** `[verified-run]`

Open a generated schematic in the GUI, make a trivial edit, save — and compare:

```
mine:        116 wires, 36 junctions
KiCad saved:  89 wires,  3 junctions
```

KiCad's cleanup merges touching collinear segments, and any junction that no longer sits where ≥3
wire *ends* meet is dropped as redundant. A wire that merely **ends part-way along** another wire
is therefore fragile: `kicad-cli`'s netlister accepts it, the GUI is stricter, and cleanup can
dissolve it.

**Fix:** pre-split every run at each attach point so all meetings are end-to-end; emit a junction
only where ≥3 endpoints coincide. Assert both invariants in the generator.

**Caveat learned the hard way:** this is *correct practice* but was **not** the cause of my
symptom (#1 was). Fixing it changed nothing visible, and I mistook that for "the fix didn't take".
Correct-but-not-causal fixes are their own trap.

---

## #5 — `top_level_sheets` in `.kicad_pro` decides which sheet the GUI opens  `G`

**Cost: medium.** `[verified-run]`

The 12-ch `.kicad_pro` was built by copying the single-channel one, whose top-level sheet is
legitimately `channel.kicad_sch`. Result: opening the 12-channel project opened the **child**.
`kicad-cli` ignores the key entirely (it picks the root by filename), so every headless check
passed while the GUI misbehaved.

```python
d.setdefault("schematic", {})["top_level_sheets"] = [
    {"filename": "twelve-channel.kicad_sch", "name": "twelve-channel", "uuid": ROOT_UUID}]
```

Related, same family: a hierarchical **child must not** carry `(sheet_instances ...)`. If it
declares itself root, the GUI opens it as the top sheet. Only the root has it, and it lists only
`(path "/" (page "1"))` even for 12 sheets — verified against KiCad's own 7-sheet demo.

---

## #6 — Fictitious schema version  `G`

`gen_sch.py` hardcoded `(version 20260306)`, a date that exists nowhere in KiCad. Real KiCad-10
values seen in `share/kicad/demos`: `20241229`, `20250114`, `20250513`, `20250610`. A future
version invites KiCad to treat the file as newer than itself. Settled on **`20250610`**.
`[verified-run]`

**General rule:** when generating any KiCad file, take the format version from a file KiCad itself
wrote — the demos directory is right there.

---

## #7 — Rotated symbols mangle their text  `G`

Two distinct traps, both cosmetic but both hit reviewers first: `[verified-run]`

- **Justify mirrors at 180°.** KiCad flips horizontal justify for a 180°-rotated symbol, so a
  right-stacked value renders leftward *over* the body. Pre-flip the justify at rot 180.
- **Text angle** must be compensated to stay upright:
  `tang = (180 - (rot % 180)) % 180`. I briefly "fixed" this to `tang = rot`, which rendered
  rot-180 text upside-down — a good example of changing a formula on a wrong theory and making
  things worse.

Also: **`Device:D_Schottky` has horizontal pins at rot 0**, unlike `R`/`C`/fuses. Any
"is this symbol vertical?" heuristic keyed on `rot % 180 == 0` is inverted for diodes.

---

## #8 — `ZONE_FILLER.Fill()` segfaults in the building process  `G`

Fill zones in a **separate process** against the saved board. Inherited lore, respected all
project. `[recalled]`

---

## #9 — 3D models vanish silently  `G`

A wrong `${KIPRJMOD}` model path produces **no error** — the part is simply absent from the
render. The render is the only check. Count what you expect to see. Edge-mount parts also need
`(rotate (xyz 270 0 0))` or they point through the board. `[recalled]`

---

## #10 — A GUI save can flatten `.kicad_pro` netclasses  `G`

Opening the project in the GUI and saving could drop the netclass patterns, after which zone fill
silently uses default clearances and a subsequent DRC **passes vacuously**. `fill_zones.py`
therefore checks for `hv_bias` in the project file and restores it with a loud warning.
Bit the project twice. `[verified-artifact]` (the guard is in the shipped script)

**Corollary:** never infer "the rule applied" from "DRC passed" — DRC uses the same possibly-broken
assignment. Measure the copper (`05_domain_knowledge.md`).

---

## #11 — `lib_footprint_mismatch`: as-built vs library drift  `G`

48 warnings, all one footprint. The library copy was legacy KiCad-6/7 format and kept the MCX edge
notch on **`Edge.Cuts`**, while every placed instance carries it on **`Dwgs.User`** (the deliberate
demotion so 48 footprints don't each cut the board edge). Orientation-normalised geometry diff
showed the *only* difference was that layer.

Fix without disturbing the routed board: export the **as-built** instance back to the library
(normalise to origin/0°/`REF**`, strip nets, `pcbnew.FootprintSave`). `[verified-run]`

---

## #12 — Environment papercuts  `G`

- **MSYS path translation:** in git-bash, `/c/Program Files/...` passed as `argv` to a native exe
  is rewritten to `C:\...`, but the same string embedded in a Python heredoc is **not**, and
  Windows Python cannot open it. Use `C:/...` forward-slash paths. `[verified-run]`
- **PowerShell 5.1 has no `&&`, no `grep`/`head`/`tail`.** Use `;`, `Select-String`,
  `-TotalCount`/`-Tail`. Give the user commands in *their* shell. `[verified-run]`
- **`pcb export pdf` ≠ `sch export pdf`.** Naming a PCB plot `board.pdf` and calling it the
  schematic confuses reviewers ("PCB artwork on a schematic page"). `[verified-artifact]`
- **KiCad does not reload files changed on disk.** When an AI session and a human share one
  working directory, the human must close/reopen (a plain `File → Revert` on the root does not
  reliably reload *child* sheets). We lost cycles to "I fixed it" / "it's still broken" where the
  GUI simply held a stale copy. `[recalled]`

---

# Where the hours actually went

| rank | sink | what would have avoided it |
|---|---|---|
| 1 | **Chasing #1 through three wrong root causes** (mid-span taps → multi-instantiation → `lib_symbols`) | Bisecting the **project file** as early as the schematic. The clue was present from the first report: *standalone works, through the `.pro` fails.* I had that fact for many rounds and kept re-verifying the schematic instead. |
| 2 | **Trusting green CLI gates over the human's GUI report** | Asking "what can this check *never* see?" before quoting it as evidence. Four independent green checks were all downstream of one blind spot. |
| 3 | **Uncontrolled variable during bisection** (copied the real `.kicad_pro` into both test variants) | Changing exactly one thing per variant. My "both fail → the common factor is `lib_symbols`" inference was wrong because two variables moved together. |
| 4 | **Declaring "fixed" before the human confirmed** | The fix is not done until the instrument that *saw* the bug says it's gone. Repeated premature "verified clean" cost trust and round-trips. |
| 5 | **#2 duplicate-on-update**, and the damaged board it produced | The bijection check, run from the start, catches it instantly. |
| 6 | Schematic legibility iterations | Render **zoomed crops** automatically after every regen and look, rather than reasoning about coordinates. |
| 7 | Sourcing churn (obsolete / wrong-package / fictional MPNs) | Verify every MPN against a live distributor page at specification time, not at order time. |

## The meta-lesson

An AI session's instruments are `kicad-cli` and file parsing. **Both are blind to `.kicad_pro`,
and the CLI netlister is more permissive than the GUI's connectivity engine.** The human at the
GUI is not a slower version of your checks — they are a *different instrument that sees a
different failure class*. When they contradict you, they are probably right, and the productive
question is "which of my checks structurally cannot see what they're seeing?"


---

<!-- ============================================================ -->
<!-- FILE: 07_bootstrap_recommendations.md -->
<!-- ============================================================ -->

# 07 — Recommendations for `EE_PROJECT_BOOTSTRAP.md`

My opinion, having lived it. Addressed to whoever writes the board-project bootstrap.

---

## The phase/gate structure I would impose

A board project is not a software project with different nouns. Its defining property is that
**final acceptance is physical and irreversible** — you spend real money and wait real weeks, and
a wrong board is scrap. Everything upstream should be organised around cheaply buying confidence
before that gate.

**Phase 0 — Environment proof.** Before any design: prove the toolchain end-to-end on a throwaway
2-resistor board. Generate → ERC → DRC → render → export gerbers. If `pcbnew` doesn't import or
`ZONE_FILLER` segfaults, learn it now, not at hour 200. *Gate: the throwaway board produces
gerbers.*

**Phase 1 — One cell, done properly.** For any repeated-block design, design/place/route **one**
channel to final quality. *Gate: DRC 0/0 on the cell, plus a human reading its schematic in the
GUI.*

**Phase 2 — Replicate.** Tile the cell programmatically; add the shared/common section.
*Gate: DRC 0/0, parity, bijection.*

**Phase 3 — Review artifacts.** Schematic PDF, zoomed crops, 3D render.
*Gate: a human opens the project in the KiCad GUI and reads it. Not a render — the GUI.*

**Phase 4 — Fab package.** Gerbers, drill, BOM, CPL, purchasing docs.
*Gate: the pre-fab checklist in `05_domain_knowledge.md`, plus live MPN re-verification.*

**Phase 5 — Order.** Human-only.

The loop is Phase 3 → Phase 1/2 and it will run many times. Treat it as the plan, not as rework.

## Which acceptance checks are genuinely executable

**Executable (make these hard gates, automate them, run them every regen):**

| check | command / method |
|---|---|
| ERC 0 | `kicad-cli sch erc --severity-all` — after confirming `erc_exclusions` is empty and `pin_not_connected` is `error` |
| DRC 0 violations / 0 unconnected | `kicad-cli pcb drc --severity-all` |
| **pad-net parity** | own tool (`check_parity.py`) — **not** `--schematic-parity` |
| **footprint↔symbol path bijection** | own tool, same script |
| no wire endpoint mid-span on another wire | own invariant over the `.kicad_sch` |
| every ≥3-way wire point has a junction | own invariant |
| **netclass really applied** | measure track widths on the class's nets; do not infer from DRC |
| footprint/pad census | count expected instances |
| BOM/CPL consistency | fitted-SMD count == CPL rows |

**Eyeball-only (name them as such; do not let a session claim them):**
schematic legibility · mechanical sanity in 3D · polarised-part rotation in the fab's preview ·
"does this circuit do what we intended" · **anything that depends on `.kicad_pro`**.

## Where the human must sit

Three places, non-negotiable:

1. **Opening the project in the KiCad GUI** at least once per review cycle. This is the only
   instrument that sees project-file-scoped defects, GUI-strict connectivity, and legibility. My
   entire worst bug lived exclusively in this gap.
2. **The fab's own parts-review screen**, for polarity/rotation of polarised parts.
3. **The order button.**

## What the generic bootstrap was missing for ECAD

1. **A concept of blind instruments.** Software bootstraps assume tests see failures. Here, four
   independent green checks were all downstream of one blind spot for weeks. The bootstrap must
   force each check to declare *what it cannot see*, and must state that `kicad-cli` never reads
   `.kicad_pro`.
2. **"Verified" discipline.** Add the debrief's own `[verified-run]` / `[verified-artifact]` /
   `[recalled]` tagging to *working* sessions, not just debriefs. I repeatedly said "verified
   clean" meaning "a command exited 0", to a user who could see it was not.
3. **The human as an instrument, with a protocol.** Not "ask for approval" but: *what to open,
   what to click, what to report back.* "Click the stub and tell me the net name" resolved in one
   round what days of my own checks could not.
4. **Shared-working-directory protocol.** When the session and the human edit the same directory,
   KiCad will hold stale copies. State the reload ritual explicitly; several rounds were lost to
   both of us looking at different bytes.
5. **Bisection as a first-class technique.** The bootstrap should ship the *method*: generate a
   minimal artifact that reproduces, then change exactly one variable at a time. And warn about
   the failure mode I hit — an uncontrolled variable riding along, producing a confident wrong
   inference.
6. **A known-good reference project.** Diffing against an independently-generated working project
   eliminated four hypotheses in one pass. The bootstrap should ship (or tell the session to
   create) a minimal working hierarchical project as a permanent diff target.
7. **Generated-file provenance.** Any file you emit should be compared against one the tool itself
   wrote — `share/kicad/demos` is the corpus. This would have caught the fictitious schema version
   immediately.

## What it should drop for this domain

- **"Tests pass ⇒ done."** Replace with "checks pass **and** the named human gate cleared."
- **Coverage-style completeness metrics.** Meaningless here; the invariants above are the analogue.
- **Rapid-iteration-on-main instincts.** Regeneration is cheap, but a board's *review* is a human
  round-trip. Batch changes, then ask for one review — do not ping per tweak.
- **Any assumption of a package manager / venv.** There is one interpreter, KiCad's, with no
  third-party deps. Preserve that.

---

# The ten facts

If I could transmit only ten things to a session starting a board tomorrow:

1. **`kicad-cli` never reads `.kicad_pro`.** ERC, netlist export, and everything derived from them
   are structurally blind to every project-file defect. If the GUI disagrees with your checks,
   bisect the **project file**.

2. **A netclass must carry its schematic fields** (`wire_width`, `bus_width`, `line_style`, +
   diff-pair/microvia). A PCB-only class **breaks eeschema connectivity for every net in it** —
   silently, and only when the project is loaded.

3. **`kicad-cli pcb drc --schematic-parity` does not compare pad nets.** It is footprint-level
   only and will report 0 while the GUI reports hundreds. Write your own parity check.

4. **Footprints link to symbols by UUID sheet-path, not reference.** The path is
   `sheetpath.tstamps + component.tstamps`. Get it wrong and paths collide, parity explodes, and
   "Update PCB from Schematic" duplicates the whole board. **Check the bijection.**

5. **`pcbnew` runs only in KiCad's bundled Python** (`C:\Program Files\KiCad\10.0\bin\python.exe`),
   there is no schematic API — `.kicad_sch` is written as text — and internal PCB units are
   **nanometres**.

6. **Generate everything deterministically** (`uuid5`, fixed namespace) so re-running is
   byte-identical. Then "regenerate and `git diff`" becomes a free regression test.

7. **Wire T-taps must be end-to-end.** Pre-split every run at each attach point; emit a junction
   only where ≥3 wire *endpoints* coincide. KiCad's cleanup merges collinear wires and deletes
   junctions, dissolving mid-span taps.

8. **Route one cell properly, then replicate programmatically.** An N-channel board is 1× the
   routing plus a tiler — and mechanical changes (board width to fit an enclosure) become
   one-constant edits instead of re-layouts.

9. **Never infer that a rule applied from "the check passed."** DRC uses the same possibly-broken
   netclass assignment. Measure the copper: read back actual track widths on the class's nets.

10. **The human at the GUI is a different instrument, not a slower one.** Give them a concrete
    protocol ("click this, tell me the net"), and when they contradict your green checks, assume
    they are right and ask which of your checks cannot see what they see.

