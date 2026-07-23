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
