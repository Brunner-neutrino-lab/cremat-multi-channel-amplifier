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
