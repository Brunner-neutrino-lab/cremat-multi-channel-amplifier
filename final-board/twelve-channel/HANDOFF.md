# HANDOFF — resume the 12-channel board on another machine

> Read this first when picking up on a new machine. Last worked: **2026-07-11** (session 14).
> Active focus: `final-board/twelve-channel/` (the final orderable board).

## Where we are (one paragraph)

The **12-channel board is design-complete and order-ready**: **213.2 × 334.7 mm**, 4-layer,
hierarchical schematic (channel sheet ×12) + tile-and-replicate layout, **ERC 0 · DRC
0/0/0** (incl. 0 unconnected), fab package regenerated. All 36 Cremat module sites are
**socketed** (Samtec SS-108-TT-2 SIP-8 strips — solder the socket, plug the module; the
modules are never soldered). Enclosure: **Hammond RM1U1908VBK 1U vented rack case, ONE
board per case** (daisy-chained power between boxes). The board uses the **SLOT-THROUGH**
scheme: a ~340 × 7 mm slot milled in each front/rear panel, board protrudes 5 mm past each
panel, MCX faces ~8.6 mm proud — full slot spec + machining notes in
`design/SESSION_LOG.md` **session 14**. Factory-drawing-verified case internals: depth
196.85 mm, height 40.09 mm (socketed module stack ~32 mm → fits). The **hv_bias 0.6 mm DRC
rule is genuinely enforced** (sessions 12+14: a netclass-pattern bug and two GUI-flattened
`.kicad_pro` incidents had silently disabled it; the pipeline now **self-heals** — gen_pcb
re-asserts netclasses after save, fill_zones refuses to fill blind). **SPICE** covers pulse response, rail budget,
crosstalk, **AC bandwidth, charge linearity/dynamic range, and ENC/noise** (all in `sim/`,
report in `sim/SESSION_REPORT.md`). A **purchase-ready BOM** with live-verified
DigiKey/Mouser links, Cremat-direct ordering, and the Hammond case is in
`models-bom/PURCHASING.md`. Nothing is blocked — remaining items are user decisions
(below), not engineering work.

## Get the code

- The working tree lives in **OneDrive** (`…/Desktop/multi-channel-cremat-amplifier`), so it
  syncs across the user's machines automatically. Otherwise clone/pull:
  **`origin/main` = https://github.com/Brunner-neutrino-lab/cremat-multi-channel-amplifier**
- Submodules under `reference/` are read-only: `git submodule update --init --recursive`.
- Latest commits: **`58d0945`** (SPICE AC/linearity/noise + purchasing BOM), **`ab68975`**
  (widen to 180 mm). `git log --oneline -5` to confirm you're current.

## Toolchain to install / verify on the new machine

| Tool | Version | Path on the last machine | Used for |
|---|---|---|---|
| **KiCad** | 10.0 | `C:/Program Files/KiCad/10.0/bin/` (`kicad-cli.exe`, `python.exe` = pcbnew) | schematic/PCB/DRC/fab, `gen_bom.py` |
| **LTspice** | ADI 24.x | `C:\Users\darro\AppData\Local\Programs\ADI\LTspice\LTspice.exe` | SPICE decks |
| **Python** | anaconda3 + numpy 1.26 + matplotlib | `C:\Users\darro\AppData\Local\anaconda3\python.exe` (as `python` on PATH) | sim analysis, `gen_purchasing.py` |
| **cadquery** | (+ `pyparsing>=3.1`) | anaconda python | only if regenerating 3D STEP models |
| **Java + FreeRouting** | Temurin JRE **25.0.3** + `freerouting-2.2.4.jar` | `C:\Users\darro\tools\` | only if **re-autorouting** (see `docs/FREEROUTING.md`) |

**Portability flags:**
- `sim/scripts/run_ltspice.ps1` (both the 12-ch and single-channel copies) **hard-codes the
  LTspice path** `C:\Users\darro\AppData\Local\Programs\ADI\LTspice\LTspice.exe`. If LTspice
  installs elsewhere on the new machine, edit that one `$lt` line.
- Analysis scripts call **`python`** (must be the anaconda one with numpy+matplotlib on PATH).
- The OneDrive folder path is identical across the user's machines, so the `C:\Users\darro\…`
  paths generally work **if it's the same Windows user** — otherwise update the two refs above.

## Gotchas (already solved — keep them)

- **Never commit a GUI-saved `.kicad_pro` over the generated one.** A KiCad GUI save
  flattens the generator's netclasses (hv_bias/power/signal → gone), which silently
  disables the 0.6 mm HV clearance rule — DRC then passes vacuously. Regen the project
  file with the gen scripts; check "hv_bias present in `.kicad_pro`" before trusting DRC.
- **Netclass patterns for local nets need a `*/` prefix** (`*/FE`, not `FE`) — local label
  nets are named `/FE` (flat) / `/chNN/FE` (hierarchical); a bare exact name matches nothing.

- **LTspice batch fails on the OneDrive space-path** → `run_ltspice.ps1` stages the whole
  `decks/` dir to `C:\Temp\ltspice_12ch`, runs there, copies the `.raw`/`.log` back.
- **3D render:** run `kicad-cli pcb render` from the real design dir with `--quality high`
  (the `${KIPRJMOD}` 3D-model paths don't resolve when rendering board copies elsewhere).
- **Headless `ZONE_FILLER.Fill()` segfaults** → fill pours as a separate pass (`fill_zones.py`).
- **FreeRouting hangs** on its version-check/analytics network calls → point Java at a dead
  proxy so they fail fast (exact invocation in `docs/FREEROUTING.md`).

## Regenerate anything (all scripted)

```
# --- PCB (from single source) ---  (KiCad python for pcbnew)
cd final-board/twelve-channel/design
"C:/Program Files/KiCad/10.0/bin/python.exe" gen_pcb.py        # W=180 is the one width knob
"C:/Program Files/KiCad/10.0/bin/python.exe" fill_zones.py
"C:/Program Files/KiCad/10.0/bin/python.exe" polish_silk.py
"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc --schematic-parity twelve-channel.kicad_pcb
# fab (gitignored): kicad-cli pcb export gerbers|drill|pos|step

# --- SPICE ---
cd ../sim
powershell -File scripts\run_all.ps1                           # 3-criterion system check
powershell -File scripts\run_ltspice.ps1 chain_ac              # + chain_linearity, chain_noise
python scripts\analyze_ac_lin.py                               # AC/linearity/ENC plots + FoM

# --- BOM ---
cd ../models-bom
"C:/Program Files/KiCad/10.0/bin/python.exe" gen_bom.py        # netlist -> twelve-channel-bom.csv
python gen_purchasing.py                                       # -> PURCHASING.md + purchasing.csv
```

## Open items (user decisions, not blockers)

1. **Mill the panel slots** (spec in `design/SESSION_LOG.md` session 14): ~340 × 7 mm per
   front/rear panel, position measured against the assembled case + real standoffs. The
   board (W = 213.2) passes through and protrudes 5 mm per side; MCX faces ~8.6 mm proud.
2. **Get a fresh PCB quote.** At 213.2 × 334.7 the board is ~714 cm² — ABOVE JLCPCB's
   650 cm² large-board threshold (was 603 cm² at W=180); expect a surcharge or use PCBWay.
3. **Output-buffer populate decision.** THS3491 block is DNP by default (0R bypass). Populated
   = 134 mV/pC (clips ~40 pC); bypassed = 67 mV/pC with ~2× charge headroom. Per-channel
   choice. Order **cut tape 296-49085-1-ND** (the -2-ND is a 250-pc reel).
4. **Mechanical mount:** board sits on **base standoffs**, not the optional RMP1908 chassis
   plate (only 152 mm deep).
5. *(optional, margin only)* a 2nd 100 µF bulk near the far channel rows — analysis says the
   single bulk is already adequate.

## Status snapshot

- **Board:** 213.2 × 334.7 mm, ERC 0, DRC 0/0/0 (hv_bias verified live), fab regenerated.
  Render `design/twelve-channel-3d.png`.
- **SPICE:** pulse 67 mV/0.5 pC · band-pass 1.6–130 kHz · linear to ~30 pC (buffer-clip 5.13 V)
  · ENC 7000 e⁻+30 e⁻/pF · rails +584/−536 mA · crosstalk 0.0002 % FS. See `sim/SESSION_REPORT.md`.
- **Ordering (chosen path): `ORDERING.md`** — JLCPCB fab + Economic SMT assembly of all
  246 FIT SMD parts (`design/fab/jlc/`: gerber zip + JLC BOM/CPL with LCSC C-numbers,
  live-verified 2026-07-11; ~$74/5 boards HASL + ~$22 assembly fees + parts) + a DigiKey
  hand-BOM (`models-bom/digikey-hand-bom.csv`: MCX/sockets/trimpots/terminals/case,
  ≈$399/board). Cremat modules already owned. HV cap primary is now **KEMET
  C0805C224K1RACTU** (Murata went DK 0-stock; retained as alt).
- **Full DigiKey-only reference BOM:** `models-bom/PURCHASING.md` — catalog $273 + modules
  $2,244 (2026-01 qty-12 tier) + buffer option $222 + case $169/board.
- **Per-track detail:** `design/SESSION_LOG.md`, `sim/SESSION_LOG.md`, `INTERFACE.md`.
