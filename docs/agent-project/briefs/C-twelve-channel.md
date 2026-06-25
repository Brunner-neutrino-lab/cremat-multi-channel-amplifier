# Brief — `twelve-channel` final board (Phase C)

Multiply the **proven single channel ×12** and produce the **final fabricable PCB**.
Tracks: **C1 design** (primary), **C2 models-bom**, **C3 sim**. **Gate:** `single-channel`
must be **COMPLETE**. Read [00-CHARTER.md](../00-CHARTER.md) +
[01-CONVENTIONS.md](../01-CONVENTIONS.md) and the **single-channel `INTERFACE.md` +
reports** first. Work in `final-board/twelve-channel/<aspect>/`.

## What this phase is

Instantiate the Phase-B `channel` sheet **12×** and lay out the real board. The
single-channel design is **frozen** — Phase C composes and routes it, it does not redesign
the channel.

- **Schematic:** root sheet with **12 instances** of the `channel` sheet; shared
  `+12V/-12V/GND` (screw terminal + bulk); per-channel `BIAS_IN`/`SIPM`/`OUT_50` = **36 MCX
  `CONMCX013`**. Reuse the `gen_sch.py` generator pattern; ERC 0.
- **PCB:** per-channel rows, **4-layer** (GND plane + power plane(s)), inputs on one long
  edge / outputs on the other; place + **FreeRouting** autoroute + fill planes; **DRC 0**.
  The verified toolchain + recipe is already in the repo — reuse
  [hardware/gen_pcb.py](../../hardware/gen_pcb.py),
  [hardware/export_dsn.py / import_ses.py / fill_zones.py], and
  [docs/FREEROUTING.md](../../FREEROUTING.md).
- **Mechanical:** rack-mounted, **two 12-ch boards side-by-side in a ~482 × 244 mm 1U
  tray**, per-board outline ≈ 225 × 235 mm, open mounting (no bulkhead) — see
  [hardware/mechanical.md](../../hardware/mechanical.md). Restore the MCX `Edge.Cuts`
  cutouts at the board edges (they were parked on `Dwgs.User` for routing in the prototype).
- **Fab:** gerbers + drill + position + the fielded BOM; package for order.

## C1 — Design (primary)
**Do:** generate the 12× root schematic (ERC 0) → 4-layer PCB → place → FreeRouting → fill →
**DRC 0** → export fab outputs. **Success:** ERC 0, DRC 0, 0 unconnected; planes filled;
MCX cutouts on `Edge.Cuts` at the edges; fab package generated; routed render saved.
**Failure:** any DRC error/unconnected; channel altered from the COMPLETE single-channel;
power/GND not on planes.

## C2 — Models-BOM
**Do:** scale the single-channel BOM ×12 + add the shared board parts (screw terminal, bulk
caps, mounting), all real/in-stock Digi-Key; produce the **final BOM with per-line + total
cost** and the **DNP variants** (Full = bias filter + CR-210 fitted). **Success:** complete
priced BOM, every line in-stock, == the C1 board; build-variant DNP table. **Failure:**
unsourced/out-of-stock lines; BOM ≠ board.

## C3 — Simulation (system check)
**Do:** a system-level confidence pass — re-confirm one channel's response in the
multiplied context, and sanity-check shared-rail loading (12 channels' supply current vs.
the decoupling/bulk) and any obvious channel-to-channel concern. **Success:** one-channel
response unchanged from Phase B; supply/bulk adequate for 12×; documented. **Failure:**
shared-rail sag/instability with 12 channels; response regressed vs. single channel.

## PROJECT DONE when
C1 (DRC-clean fab package) + C2 (priced final BOM == board) + C3 (system check passes) meet
criteria and agree. Coordinator marks **PROJECT DONE** in [02-TRACKS.md](../02-TRACKS.md).
