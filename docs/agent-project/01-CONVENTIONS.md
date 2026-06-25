# Conventions — how every track works

Read this once before starting any track. It defines the directory layout, the
log/report protocol, interface contracts, the toolchain, and the success-criteria
philosophy that all 12 tracks share. Your track brief assumes you know this.

---

## 1. Directory layout

Each sub-component / phase has one directory; each of its three tracks owns a subdir:

```
chips-board/csp-cr112/            integration/single-channel/        final-board/twelve-channel/
  design/        <- Design track    design/                            design/
  sim/           <- Sim track        sim/                               sim/
  models-bom/    <- Models-BOM       models-bom/                        models-bom/
  INTERFACE.md   <- the contract (see §3), owned by Design, read by all
```

Inside each track subdir you maintain exactly two protocol files plus your work:
```
design/
  SESSION_LOG.md       append-only ground truth (see §2)
  SESSION_REPORT.md    concise current-state summary for other tracks (see §2)
  <your KiCad project / ngspice decks / BOM files / plots / scripts>
```

**Never** edit another track's subdir. Communicate via reports + `INTERFACE.md` only.
`reference/` (submodules) and the existing `hardware/`, `docs/` are **read-only prior art**.

## 2. Session log vs session report (the core protocol)

- **`SESSION_LOG.md` — ground truth, append-only, chronological.** Every working session
  appends a dated entry: what you did, the exact commands/tools, results (numbers, DRC/ERC
  counts, sim figures of merit), decisions **and why**, dead-ends, and what's next. This is
  the record a future session (or auditor) replays to understand *how* it was built. Do not
  rewrite history; append.
- **`SESSION_REPORT.md` — the summary other tracks read instead of your log.** Keep it
  current (overwrite): status vs. success criteria, the deliverables and where they are,
  the **interface** you expose or consume, open issues, and a one-line "how to use my
  output." Other tracks must be able to integrate by reading only this + `INTERFACE.md`.

Templates: [templates/SESSION_LOG.md](templates/SESSION_LOG.md),
[templates/SESSION_REPORT.md](templates/SESSION_REPORT.md). Both start present in each
subdir (copy the template). Update the [02-TRACKS.md](02-TRACKS.md) status line when your
state changes.

## 3. Interface contracts

A sub-component is a black box to downstream tracks. The **Design track** owns
`<subcomponent>/INTERFACE.md` and keeps it current; it declares everything a consumer needs:

- **Electrical I/O:** each port — name, direction, signal type, expected range
  (e.g. `IN: charge, 0–5 pC` · `OUT: voltage, ≤ ±2 V, Zout 50 Ω` · `±12 V, GND`).
- **Schematic handle:** the hierarchical sheet/symbol to instantiate and its pin names.
- **Mechanical:** connectors used, board edge/mounting if relevant.
- **Part list pointer:** link to the Models-BOM report (the real parts).
- **Verified-by:** link to the Sim report (the figures of merit that prove it works).

Downstream tracks integrate against `INTERFACE.md`, not by reading internals.

## 4. Toolchain (already in this repo)

- **KiCad 10** CLI + bundled Python at `C:/Program Files/KiCad/10.0/bin/` (not on PATH —
  call by full path). `kicad-cli.exe` (erc/drc/export/render/sim utilities) and
  `python.exe` (has `pcbnew`).
- **Schematic generation** (no eeschema API): write `.kicad_sch` as S-expression with the
  net-label-at-pin-coordinate method — see the working example
  [hardware/gen_sch.py](../../hardware/gen_sch.py) and
  [docs/KICAD_WITH_CLAUDE_CODE.md](../KICAD_WITH_CLAUDE_CODE.md). Validate with
  `kicad-cli sch erc`. **Reuse it.**
- **PCB:** `pcbnew` Python places footprints + assigns nets; see
  [hardware/gen_pcb.py](../../hardware/gen_pcb.py). Zones fill in a separate pass
  ([hardware/fill_zones.py](../../hardware/fill_zones.py)) — in-memory fill segfaults.
- **Routing = FreeRouting** (KiCad has no autorouter):
  `export_dsn.py` → `freerouting-2.2.4.jar` (needs **Java 25**) → `import_ses.py`. Full,
  verified recipe in [docs/FREEROUTING.md](../FREEROUTING.md). 4-layer with GND + power
  planes routes cleanly.
- **Gates:** [scripts/erc.sh](../../scripts/erc.sh), [scripts/drc.sh](../../scripts/drc.sh)
  (adapt the `SCH`/`PCB` paths to your subdir, or copy them locally).
- **Symbols/footprints already built:** [hardware/lib/cremat.kicad_sym](../../hardware/lib/cremat.kicad_sym)
  (CR-11X/CR-112, CR-200, CR-210, EL5167) and `hardware/lib/cremat.pretty/`
  (MCX `CONMCX013`). Reuse; extend in your own lib if needed.
- **SPICE = ngspice**, behavioral models (§5). If `ngspice` isn't on the machine, install a
  standalone Windows build (or use KiCad's) and **record the exact invocation in your log**.

## 5. SPICE / simulation rules

**Primary source = Cremat's official SPICE models. Use them; do not start from scratch.**
Cremat publishes **LTspice models** (downloadable ZIPs, each typically a schematic `.asc`
+ symbol `.asy`, built with LTspice XVII) and detailed **application guides / spec sheets**
for the CR-11X (CSP), CR-200, and CR-210. The Sim tracks **must solicit cremat.com first**:

- Models + docs hub: **https://www.cremat.com/specification-sheets/** ; module pages
  https://www.cremat.com/home/charge-sensitive-preamplifiers/ ,
  https://www.cremat.com/home/cr-200-x-shaper-modules/ , and the CR-210 page; application
  guides e.g. https://www.cremat.com/CR-110-R2.1.pdf , https://www.cremat.com/CR-200-R2.1.pdf .
- **Download the model ZIP for each chip** (CR-11X/CR-112, CR-200-1µs, CR-210) and the
  matching application guide; store under `sim/cremat-models/<part>/` and **cite the source
  URL + retrieval date in your log.** (If a model is gated/awkward to fetch, list the exact
  part + link in your report — the user has offered to help obtain them.)

Engine: the Cremat models are **LTspice** (`.asc`/`.asy`). Determine the right runner:
1. If the model exposes a portable SPICE **`.subckt`/`.lib`** (or you can extract the netlist
   from the `.asc`), run it in **ngspice** headless (preferred — scriptable, matches the
   rest of the toolchain). Document the extraction.
2. Otherwise run it in **LTspice** (install the free LTspice if needed; danger mode) and
   export the waveform data. Either way, the deck/inputs must be committed + reproducible.
- Keep a **behavioral model** (charge-gain + shaping-time approximation from the datasheet)
  as a **fallback and cross-check** — if the Cremat model and your behavioral model
  disagree on the figures of merit, investigate and record why.

**Stimulus:** an ideal **0.5 pC** charge impulse at the CSP input. The shaper track (no CSP
on its own board) injects the **CR-112 model's output waveform** as its stimulus — i.e. the
CSP model output is the shaper's input.

**Deliverable plots (saved in `sim/`, referenced from the report):** input charge and the
node response at every stage on your board. Report **figures of merit** (peak amplitude,
peaking time, undershoot, baseline behavior, noise if modeled) and judge them against the
success criteria.

## 6. Real-parts swap (the generic→real gate)

Design + Sim start with **generic** values ("10 kΩ 0805", "100 nF 100 V"). The Models-BOM
track finds the **real** part for each. When Models-BOM publishes its parts report:
1. Design swaps each generic for the chosen MPN/footprint, re-runs **ERC + DRC**, updates
   `INTERFACE.md` and its report.
2. Sim updates any **value-sensitive** model params (tolerances, real cap ESR, etc.) if they
   move a figure of merit; otherwise notes "no change."
3. Models-BOM ↔ Design BOM must then be **identical** (Coordinator checks at COMPLETE).

## 7. Models-BOM sourcing rules

For every part: find a **real, in-stock, economical** part on **Digi-Key** (use
WebSearch/WebFetch on digikey.com / octopart / the manufacturer; SnapEDA/Ultra-Librarian or
the KiCad libs for symbol+footprint+3D). Record in the BOM: **value, MPN, manufacturer,
Digi-Key PN, unit cost @ qty, stock qty, package, datasheet link, and the model/footprint
source**. Prefer well-stocked, low-cost, jellybean parts; justify any non-obvious choice in
the log. If a model must be downloaded behind a login (SnapEDA), list the exact part + link
in the report so a human can drop the zip (as has been done before), and integrate it when
it arrives.

## 8. Git & danger mode

- Sessions run in bypass/danger mode (no permission prompts). Be disciplined anyway.
- Commit your own subdir frequently with clear messages; **don't commit other tracks'
  dirs.** End commit messages with the Co-Authored-By trailer.
- Generated/regenerable artifacts (`reports/` dumps, `*.dsn`, `*.ses`, `fab/`, ngspice
  `*.raw`) are git-ignored per the root `.gitignore`; commit **source** (decks, gen
  scripts, `.kicad_*`, BOM CSVs, and committed plots used in reports).

## 9. Success / failure criteria (philosophy)

Every track **states its own** measurable criteria in its report before doing the work, then
evaluates against them. ERC/DRC clean = *legal*, not *correct*: correctness is judged
against the **module datasheets + Cremat eval-board reference circuits** (`reference/cremat-
CR-150-R5`, `reference/cremat-CR-160-R7`) and the **simulation figures of merit**. A track
that can't meet a criterion writes down *why* and what it would take — it does not silently
lower the bar.
