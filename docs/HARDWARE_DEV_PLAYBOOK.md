# Hardware development with Claude — a playbook

> A guide for starting a **new board** with Claude Code. Written after building the
> single-channel Cremat amplifier (schematic capture → parts sourcing → simulation →
> layout → autoroute → review) so the next board doesn't have to rediscover any of it.
>
> Companion docs: [KICAD_WITH_CLAUDE_CODE.md](KICAD_WITH_CLAUDE_CODE.md) (the file-as-text
> method), [FREEROUTING.md](FREEROUTING.md) (autoroute recipe),
> [development-plan.md](development-plan.md) (the track model in practice).

---

## 0. The loop

Everything below is a variation on one loop:

```
author the file as text  →  validate headless (kicad-cli)  →  render it  →  LOOK at it  →  fix
```

The three failure modes map exactly onto the three checks:

| Failure | Caught by |
|---|---|
| Wrong connectivity | `kicad-cli sch erc` + **netlist-membership diff** (§4.2) |
| Wrong geometry / clearance | `kicad-cli pcb drc` |
| Wrong-but-legal (unreadable, mislabeled, wrong part) | **render → rasterize → look**, and a human/adversarial review |

ERC will happily pass a wrong-but-legal schematic. DRC will happily pass an ugly-but-legal
board. **Never skip the "look at it" step** — and never trust a downscaled thumbnail; crop
and inspect at real resolution (§4.4).

---

## 1. Why this works

1. **Every KiCad file is plain-text S-expression.** `.kicad_sch`, `.kicad_pcb`, `.kicad_sym`,
   `.kicad_mod` — all readable/writable with ordinary file tools or a Python generator.
   `.kicad_pro` is JSON.
2. **`kicad-cli` is a headless test runner.** ERC, DRC, netlist export, BOM, SVG/PDF render,
   gerbers, STEP. This is your feedback loop; it replaces "look at the editor."
3. **`pcbnew` is a real Python API** (PCB only — Eeschema has none). Use it for placement,
   DSN/SES import-export, zone fills.

So: generate the schematic from a **single source of truth** script, gate it with `kicad-cli`,
and hand only the genuinely-human steps (placement aesthetics, dense routing, part choices) to
a person.

---

## 2. The parallel-development model

### 2.1 Tracks, owners, contracts

Split the board into **tracks**: self-contained units with explicit inputs, deliverables, and a
definition-of-done. Each track publishes an **`INTERFACE.md`** — the contract downstream tracks
integrate against *without reading the track's internals*.

A worked split (this repo's Phase 1 ran tracks 1–4 fully in parallel):

| Track | Owns | Parallel? | Deliverable |
|---|---|---|---|
| 0 · Coordinate | spec, iron rules, cross-track decisions, gates | throughout | `development-plan.md`, decision list |
| 1 · Parts / datasheets / BOM | `models-bom/` | ✅ | `*-bom.csv` + sourcing report |
| 2 · Circuit & simulation | `sim/` | ✅ | SPICE decks + figures-of-merit |
| 3 · Topology / reference integration | `docs/hardware/` | ✅ | channel topology |
| 4 · Mechanical / connectors | `mechanical.md` | ✅ | footprints, board outline |
| 5 · Schematic capture | `design/gen_sch.py`, `*.kicad_sch` | ← needs 1–4 | ERC-0 schematic |
| 6 · PCB layout + autoroute | `design/gen_pcb.py`, `*.kicad_pcb` | ← needs 5 | DRC-0 board |
| 7 · Fabrication | `fabrication/` | ← needs 6 | gerbers, BOM, CPL |

Phase-1 tracks have no dependencies on each other. Phase-2 (5→6→7) is strictly serial.

### 2.2 Running tracks as parallel Claude agents

This is the part that pays off. Launch a background agent per independent track. **The single
rule that makes it safe: strict file ownership.**

When you brief a parallel agent, give it:

1. **An explicit allowlist of files it may write.**
2. **An explicit denylist** — name the files another agent is actively editing.
   > *"DO NOT edit `design/gen_sch.py` or any `.kicad_sch` — another session is rewriting it.
   > If you find a part that must be swapped, RECORD the recommendation; don't change the design."*
3. **The context files to read first** (iron rules, the relevant `INTERFACE.md`).
4. **A self-contained deliverable spec** — its final message is the only thing you get back.
5. **Citation requirements** for anything factual: *"every lifecycle/stock claim MUST cite a URL
   you actually fetched; if a page is unreachable say so rather than guessing."*

**It works.** The parts-sourcing agent that ran alongside the schematic redraw found a latent
bug nobody had noticed: the 0.1 µF decoupling cap's Digi-Key PN was for an **0603** part sitting
in an **0805** footprint. Three other PNs were stale or malformed. That's exactly the kind of
tedious, high-value, embarrassingly-parallel work to farm out.

### 2.3 What parallelizes, and what doesn't

| Parallelize | Keep serial / single-author |
|---|---|
| Datasheet hunting, lifecycle/stock checks, BOM sourcing | Schematic layout (one coherent artifact) |
| Independent simulation decks | PCB placement (global consistency) |
| **Adversarial review** — fan out reviewers on different regions/lenses | Anything with a global invariant |
| Per-block research | |

Do **not** fan out "write the schematic in 5 pieces and merge." A schematic is one tightly
coupled artifact: seams, styling, and overlaps don't merge cleanly. Author it once; **fan out
the verification instead**.

### 2.4 Adversarial review (high value, cheap)

After the schematic renders cleanly, spawn independent reviewers — one per sheet region, plus
one design-fidelity checker reading the netlist against the circuit docs. Tell them:

> *"Connectivity is already proven identical (ERC 0, netlist diff clean). Do NOT re-check nets.
> Your only job is whether the DRAWING is readable. Be adversarial and specific. If a region is
> clean, say so — do NOT invent problems."*

That pass caught a **systemic** defect I'd missed: every decoupling cap's value string was drawn
straight through its GND symbol, because the generator placed `Value` at `(x+2, y+5.5)` — the
exact spot the GND symbol occupies. One generator fix, ~10 instances corrected.

---

## 3. Track playbooks

### 3.1 Parts, datasheets & BOM

- One row per reference designator; a `Populate_Default` column (`FIT`/`DNP`) is the **single
  source of truth** for build variants. Keep design source and BOM in sync — a DNP flag that
  disagrees with the schematic is a fab bug.
- Verify **lifecycle status** (Active / NRND / LTB / Obsolete) *and* orderability, with a cited
  URL per claim. Parts rot: this board's charter part (EL5167) was obsolete, and its bias cap
  went NRND mid-project.
- **Sanity-check physical size against the assembly philosophy.** If the board is deliberately
  0805-and-up for hand assembly, a SOD-123 diode (≈2.7×1.6 mm) is *smaller than an 0805* —
  wrong answer even though it's "a real part." Prefer SMA/DO-214AC or a leaded DO-41.
- Prefer parts you can still buy in the qty you need at the *scaled* count (×12 channels).

### 3.2 Simulation

Pattern used here (LTspice, batch mode):

```
sim/
  decks/    *.cir  (top-level decks) + vendor .sub/.lib models + models.inc
  models/   vendor SPICE downloads, kept with their source URL
  scripts/  ltspice_raw.py (raw parser) + analyze_*.py (FoM extraction)
  data/     *.raw, *.log, *_fom.json  (generated)
```

- **Use the vendor's official model** and record where it came from (e.g. TI SBOMAN4 for the
  THS3491, Cremat's own CR-200/CR-210 models). Don't hand-roll an op-amp macromodel if the
  vendor ships one.
- Run headless: `LTspice.exe -b -Run deck.cir` → parse the `.raw` → emit a **figures-of-merit
  JSON/CSV**, not just a plot. FoM files are diffable; plots aren't.
- Let the sim **pin component values** and record it in the design source. Here the CFA feedback
  resistor (`Rf = Rg = 976 Ω`) was validated against TI's model, and that provenance is a code
  comment in the generator.
- KiCad bundles `ngspice.dll` if you'd rather stay in-tree; LTspice was used here.

### 3.3 Schematic capture

Author it with a **generator script** (`gen_sch.py`) so it's reproducible. See §5 for the
gotchas that will otherwise cost you a day.

Structure that worked:

- `PARTS{}` — role → (value, MPN, manufacturer, distributor PN). Real-part metadata.
- `SPEC{}` — role → (lib_id, footprint, dnp, `{pin: net}`, `(x, y, rotation)`).
- `ROLES[]` — a fixed order that determines reference designators (`R1`, `C1`, …). Keep the order
  stable so refs don't churn on unrelated edits.
- `layout()` — places symbols, then wires them **by pin lookup** (`P(role, pin)`), never by
  hand-typed coordinates. Wires then always land exactly on pins.
- A **coverage self-check**: assert every declared pin has a net (wire endpoint, label, power
  symbol, or no-connect). Catches "I forgot to ground that cap" before ERC does.
- Deterministic `uuid5` UUIDs so re-runs reproduce the file byte-for-byte.

**Readability is a design requirement, not a nicety.** A netlist-correct schematic that a human
can't review is not done. Draw a left→right signal spine, bank the decoupling above (+rail) and
below (−rail), and wire the signal path pin-to-pin. Use net labels for rails and power symbols
for globals — don't route 12 V across the sheet.

### 3.4 PCB layout & autorouting

The verified recipe (from [FREEROUTING.md](FREEROUTING.md)):

```bash
PY="C:/Program Files/KiCad/10.0/bin/python.exe"
"$PY" design/gen_pcb.py        # board outline, stackup, footprint placement
# --- clean the placement FIRST: no overlapping copper (see below) ---
"$PY" design/export_dsn.py     # pcbnew.ExportSpecctraDSN -> .dsn
java -jar freerouting-2.2.4.jar -de board.dsn -do board.ses    # Java 21+ (25 verified)
"$PY" design/import_ses.py board.ses                            # tracks back into .kicad_pcb
"$PY" design/fill_zones.py     # separate pass — see below
bash scripts/drc.sh            # the gate: 0 errors
```

Hard-won constraints:

- **Placement is the human step.** `ExportSpecctraDSN` returns `False` if any copper overlaps.
  Autorouters route; they don't fix a bad floorplan. Spread parts until DRC shows no
  `clearance`/`shorting_items`, *then* export.
- **Give the router layers.** A 4-layer board with a GND plane and a −VDC plane routed all 480
  nets; the same board on 2 layers left ~9 nets unrouted. Buy the layers.
- **Fill zones as a separate pass on the saved file.** Headless `ZONE_FILLER.Fill()` segfaults
  if you call it inline — that's why `fill_zones.py` exists.
- Hand off dense/controlled-impedance routing to a human. Do placement + constraints
  programmatically, gate with DRC.

### 3.5 Review & handoff

Export a **PDF for the reviewer** into the repo (`design/reports/*.pdf`) and regenerate it every
time the design changes. An engineer reviewing a stale PDF is worse than no review.

---

## 4. The gates

### 4.1 ERC

```bash
KCLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
"$KCLI" sch erc --exit-code-violations board.kicad_sch -o reports/erc.rpt   # exit 0 == clean
```
Configure `pin_not_connected` and `label_dangling` as **errors**. A forgotten connection then
becomes a build failure instead of a silent bug.

### 4.2 Netlist-membership diff — *the most valuable tool here*

**When you refactor, redraw, or move anything, prove the circuit didn't change.** Export the
netlist before and after, and diff **net membership** (the set of `(ref, pin)` per net),
*ignoring* net names — because auto-generated names (`Net-(R1-Pad2)`) legitimately churn.

This let a complete schematic redraw — every part moved, 99 wires added where there were zero —
land with total confidence: `IDENTICAL CONNECTIVITY: 26 nets`. It also instantly localized every
bug during the rewrite (a missing junction, a dangling rail label) to the exact net.

```python
# netcmp.py — usage:  python netcmp.py before.net [after.net]
import re, sys
def parse(path):
    t = open(path, encoding="utf-8").read(); nets = {}
    for m in re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s+\(name\s+"([^"]*)"\)', t):
        start, depth, i = m.start(), 0, m.start()
        while i < len(t):
            if t[i] == '(': depth += 1
            elif t[i] == ')':
                depth -= 1
                if depth == 0: break
            i += 1
        block = t[start:i+1]
        nets[m.group(1)] = {(n.group(1), n.group(2)) for n in
            re.finditer(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', block)}
    return nets

a = parse(sys.argv[1])
if len(sys.argv) < 3:
    for k in sorted(a): print("%-16s %s" % (k, sorted(a[k])))
    sys.exit(0)
b = parse(sys.argv[2])
ca, cb = {frozenset(v) for v in a.values() if v}, {frozenset(v) for v in b.values() if v}
name = lambda n, s: next((k for k, v in n.items() if frozenset(v) == s), "?")
if ca == cb:
    print("IDENTICAL CONNECTIVITY: %d nets" % len(ca)); sys.exit(0)
print("DIFFERENCES FOUND")
for s in ca - cb: print("  only in A (%s): %s" % (name(a, s), sorted(s)))
for s in cb - ca: print("  only in B (%s): %s" % (name(b, s), sorted(s)))
sys.exit(1)
```

When you *intend* to change the circuit, the diff is still the check — you read it and confirm
the delta is **exactly** what you meant (e.g. *"`TEST_IN` gained R5, `TEST_N` is gone"*).

### 4.3 DRC

```bash
"$KCLI" pcb drc --exit-code-violations board.kicad_pcb -o reports/drc.json
```
Refill zones before DRC. Never commit DRC **errors**.

### 4.4 Render → rasterize → look

```bash
"$KCLI" sch export pdf board.kicad_sch -o reports/review.pdf
pdftoppm -png -r 300 reports/review.pdf out          # MiKTeX ships pdftoppm
# then crop regions with PIL and actually inspect them
```
A full-sheet thumbnail hides everything. **Crop to a region at 200–400 DPI.** Text overlap,
strikethrough, merged labels, and missing junction dots are only visible at real resolution.

---

## 5. KiCad-as-text: empirically verified gotchas

Every one of these was confirmed by experiment (a throwaway probe schematic + netlist/render),
not guessed. Re-verify with a probe if you're on a different KiCad version.

**Geometry**
- **Pin transform under rotation** (schematic is Y-down, symbol libs are Y-up). For a symbol at
  `(at X Y θ)` and library pin `(px, py)`:
  ```
  sheet = ( X + px·cosθ − py·sinθ ,  Y − (px·sinθ + py·cosθ) )     # θ CCW
  ```
  Verified for θ ∈ {0, 90, 180, 270} — lands on the correct **pin number**, not just position.
- **Property text angle = symbol rotation + property angle.** To keep `Reference`/`Value`
  horizontal on a rotated part, set the property's own angle to `(180 − rot%180) % 180`.
  Property *position* is absolute (it is **not** rotated with the symbol).

**Connectivity**
- **A wire ending on another wire's interior (a T) does NOT connect without a junction.**
  Auto-place them: a junction is needed at `p` when
  `wire_ends(p) + 2·wires_passing_through(p) + pins(p) ≥ 3`.
- **`PWR_FLAG` and power symbols must sit on a wire *endpoint*, or coincide with a component
  pin.** Mid-wire they are silently unconnected → `pin_not_connected` + `power_pin_not_driven`.
- **A net label must be anchored *on* the wire.** `justify` only moves the text, not the
  attachment point. An off-wire label dangles and the net gets auto-named.
- **Power symbols contain a hidden `power_input` pin.** So any net carrying a power symbol needs
  a `PWR_FLAG` somewhere, or ERC reports "not driven." Connector pins are `passive` and need no
  flag. Filtered rails behind a series R each need their own flag.

**Rendering**
- **`(junction ... (diameter 0) ...)` exports as zero-size** — the connection dots vanish from
  `kicad-cli`'s PDF. Set an explicit diameter (`0.9144` = KiCad's classic 36 mil).
  *This is invisible until a reviewer asks "why aren't the connections shown?"*
- **Don't put `Value` below a vertical 2-pin part** — that's where its GND symbol lives. For
  `rot % 180 == 0` passives, stack `Reference`/`Value` to the **side** at mid-height; for
  horizontal ones, above/below is fine.
- **Hide verbose value text** on connectors and `PWR_FLAG`s. `"MCX edge jack 50R"` on four jacks
  is pure clutter; the refdes and net label already say it.

**Misc**
- `python` is usually **not on PATH** — use KiCad's bundled interpreter (§7).
- Deterministic `uuid5` over a fixed namespace → re-running the generator produces no spurious diff.

---

## 6. Working with the human

- **Restate the topology in ASCII and get a nod before you edit.** Two round-trips were burned on
  this board: "remove the 0.1 µF" (bias cap vs. power-rail bypass — I removed the wrong one), and
  the Zener protection (dead-end `rail→R→zener→GND` shunt vs. the intended
  `connector→R→rail`, `rail→zener→GND`). Both would have been caught by five lines of ASCII art.
- **`TBD` is a first-class value.** Place the part, wire it, mark the value `TBD`, leave it out of
  the BOM, and ask. Don't invent a resistor value to make a schematic look finished.
- **Surface part swaps, don't perform them silently.** An NRND part with an identical active
  drop-in is still the owner's call — recommend, then apply on a yes.
- **Say what changed and what you verified.** "ERC 0, netlist identical, PDF refreshed" beats
  "done."
- **Don't commit** unless asked. Leave changes in the working tree for review.

---

## 7. Toolchain reference (Windows, KiCad 10)

```bash
KCLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"   # not on PATH
PY="C:/Program Files/KiCad/10.0/bin/python.exe"        # bundled; has pcbnew + PIL
STOCK="C:/Program Files/KiCad/10.0/share/kicad/symbols"
FPS="C:/Program Files/KiCad/10.0/share/kicad/footprints"
pdftoppm                                              # from MiKTeX; rasterize PDFs
java -jar freerouting-2.2.4.jar                       # needs Java 21+ (25 verified)
```

| Need | Command |
|---|---|
| ERC | `"$KCLI" sch erc --exit-code-violations f.kicad_sch -o erc.rpt` |
| Netlist | `"$KCLI" sch export netlist f.kicad_sch -o f.net` |
| Review PDF | `"$KCLI" sch export pdf f.kicad_sch -o review.pdf` |
| DRC | `"$KCLI" pcb drc --exit-code-violations f.kicad_pcb -o drc.json` |
| Gerbers | `"$KCLI" pcb export gerbers --output fab/ f.kicad_pcb` |
| Inspect a stock symbol | `"$PY" -c "…"` — read `$STOCK/Device.kicad_sym`, grep the `(pin …)` blocks |

**Always introspect a symbol before using it** — pin numbers and names are not what you assume.
`Device:D_Zener` is pin 1 = **K** (cathode), pin 2 = **A** (anode). `Device:R` at rot 0 is pin 1
top, pin 2 bottom. Screw-terminal pins are `passive`.

---

## 8. Anti-patterns

- Trusting a downscaled render. Crop and look.
- "ERC passes, ship it." ERC does not check design intent.
- Fanning out schematic *authoring* across agents. Fan out review instead.
- Letting the BOM and the design source disagree on values, MPNs, or DNP flags.
- Hand-typing wire coordinates instead of looking up transformed pin positions.
- Adding a net label to name an internal node that's already defined by a wire — you'll either
  dangle it or collide with an existing net name.
- Renaming/removing a part from the middle of the `ROLES` list without expecting every
  downstream refdes to renumber.
