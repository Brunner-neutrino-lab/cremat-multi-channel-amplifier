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
