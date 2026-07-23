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
