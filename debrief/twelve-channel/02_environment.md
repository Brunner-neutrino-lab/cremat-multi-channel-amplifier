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
