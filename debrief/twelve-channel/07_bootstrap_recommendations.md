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
