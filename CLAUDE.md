# CLAUDE.md — Multi-channel Cremat amplifier

Working notes for Claude Code in this repo. Read [`README.md`](README.md) for the
user-facing overview and [`docs/session-report.md`](docs/session-report.md) for the
development history / open items.

## What this is

The **design spec + build documentation** for a **12-channel** SiPM charge-sensitive
preamplifier / Gaussian shaper board. It is a modified remake of the Brunner-lab
**6-channel Cremat CSP & Shaper board** (`reference/cremat-x6-board/`). Four changes:

1. 12 channels (was 6).
2. 0805 passives wherever possible.
3. A Cremat **CR-210** baseline restorer per channel — **optional**, 0R-jumper bypass.
4. An on-board SiPM **bias front-end** per channel — `BIAS_IN` → **optional** RC+R bias
   filter → node shared by the **SiPM (DC-coupled)** and the **amplifier (AC-coupled)`.

See [`docs/modifications.md`](docs/modifications.md) for the authoritative change list.

## Iron rules

1. **The reference channel is the starting point, not a thing to edit.**
   [`reference/cremat-x6-board/channel.kicad_sch`](reference/cremat-x6-board/channel.kicad_sch)
   is the per-channel circuit to derive from. `reference/` holds **git submodules** —
   never commit changes inside them; do the new design at the top level / in `hardware/`.
2. **"Optional" means a populate-or-bypass jumper pair, resolved by DNP** — not a DIP
   switch, not a relay. Every optional block (CR-210, bias filter) has 0R/solder jumpers
   so exactly one path is populated. See the DNP tables in
   [`docs/hardware/bom.md`](docs/hardware/bom.md) — keep them the single source of truth
   for which refs are fitted in each variant.
3. **0805 is the default passive size *where the part allows it*.** Cremat modules
   (CR-11X, CR-200, CR-210) are 8-pin SIP through-hole modules; op-amps and coax jacks
   are their own packages. Don't claim a part is 0805 when it physically can't be.
4. **The bias front-end carries HV.** Bias-side passives, the AC-coupling cap `Cc`, and
   the `SIPM`/`BIAS_IN` nets must be rated and spaced for the full SiPM bias voltage
   (the reference uses a 100 V X5R coupling cap). HV creepage is a DRC concern — see
   [`docs/hardware/pcb-design-rules.md`](docs/hardware/pcb-design-rules.md).
5. **CR-210 pinout + bypass are confirmed; the SiPM bias range is not.** The CR-210 map
   and the jumper-bypass scheme are taken from Cremat's own open-source board
   `reference/cremat-CR-160-R7` (pin 2 = GND, vs the CR-200's P/Z). The target SiPM **bias
   voltage** is still open and gates HV creepage + cap ratings — flag, don't guess. See
   [`docs/session-report.md`](docs/session-report.md) and the decision list in
   [`docs/development-plan.md`](docs/development-plan.md).

## Build philosophy (inherited from `ets-breakout`)

The reference `ets-breakout` project builds boards from a **single source of truth** with
a scripted KiCad pipeline (generate → finalize → fill zones → DRC → fab outputs), and
keeps **local, datasheet-verified footprints**. When the hardware track implements this
board, prefer that approach: a per-channel hierarchical sheet instantiated 12×, a project
BOM with `MPN`/`MFN`/`VPN`/`VN` fields and DNP flags, and a DRC gate before fab.

## Toolchain (when implementation starts)

- **KiCad 9/10**, CLI + bundled Python under `C:\Program Files\KiCad\<ver>\bin\` (not on
  PATH — call by full path). The reference board is KiCad `version 20230121` (KiCad 7);
  it will migrate forward on first open.
- Headless `ZONE_FILLER.Fill()` segfaults in the reference pipeline → fill zones as a
  separate pass on the saved file. Run `kicad-cli pcb drc` as the gate.

## Repo layout

```
README.md                     overview + documentation map
CLAUDE.md                     this file
docs/                         the build documentation set (see README map)
  development-plan.md          work-track breakdown + dependency graph + decisions
  architecture.md  modifications.md  session-report.md
  hardware/   channel.md board.md bom.md pcb-design-rules.md component-libraries.md
  fabrication/fabrication-guide.md
  operation/  user-guide.md
reference/                    git submodules (read-only)
  cremat-x6-board/            WHAT we build (6-ch CR-110/CR-200 eval board)
  ets-breakout/               HOW we build/document (pipeline + doc structure)
  cremat-CR-160-R7/           CR-210 pinout + bypass-jumper integration (Cremat OSHW)
  cremat-CR-150-R5/           CR-11X CSP reference (Cremat OSHW)
hardware/                     KiCad project (Phase 1 built; schematic/PCB = GUI step)
  multi-channel-cremat-amplifier.kicad_pro   net classes + DRC severities
  lib/cremat.kicad_sym         CR-11X/CR-112, CR-200, CR-210, EL5167 (kicad-cli-validated)
  lib/cremat.pretty/           project footprints (MCX CONMCX013 = to create)
  sym-lib-table  fp-lib-table  bom/  integration-notes.md  mechanical.md
  BUILD-IN-KICAD.md            Tracks 5-7 GUI build guide
```
