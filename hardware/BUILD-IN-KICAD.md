# Building the board in KiCad (Tracks 5 → 6 → 7)

> **Superseded 2026-07-11.** The board was ultimately built via `integration/single-channel/`
> → `final-board/twelve-channel/` (213.2 × 334.7 mm, 4-layer, order-ready), not this `hardware/`
> skeleton. Use `final-board/twelve-channel/` (HANDOFF.md, ORDERING.md) as the source of truth;
> the steps below describe the earlier `hardware/`-track plan.

Everything up to schematic capture is done and validated: the symbol library
([lib/cremat.kicad_sym](lib/cremat.kicad_sym)), the project + net classes
([multi-channel-cremat-amplifier.kicad_pro](multi-channel-cremat-amplifier.kicad_pro)),
the lib tables, the fielded BOM ([bom/](bom/)), the per-channel netlist
([integration-notes.md](integration-notes.md)), and the mechanical envelope
([mechanical.md](mechanical.md)).

**Update — Track 5 is now generated headless and ERC-clean** (see
[../docs/KICAD_WITH_CLAUDE_CODE.md](../docs/KICAD_WITH_CLAUDE_CODE.md)). The schematic is
produced by [gen_sch.py](gen_sch.py):
```
python hardware/gen_sch.py          # writes channel.kicad_sch + multi-channel-cremat-amplifier.kicad_sch
bash scripts/erc.sh                 # ERC -> reports/erc_root.json (0 errors)
```
`kicad-cli sch erc` reports **0 errors** (4 warnings = MCX/screw-terminal footprint links).
The Track 5 steps below are now **optional GUI refinement** (e.g. swapping the unity-follower
buffer for the reference's exact gain/P-Z network, or tidying placement). **Tracks 6–7
(layout + fab) are the remaining work.** KiCad 10 is at `C:\Program Files\KiCad\10.0\`.

> Generator caveat: once you edit the schematic in the GUI, the `.kicad_sch` becomes the
> source of truth — don't re-run `gen_sch.py` (it overwrites). The generated buffer is a
> unity follower (clean + ERC-valid); the reference's gain/P-Z network is the documented
> GUI refinement.

---

## Track 5 — Schematic capture  *(done by gen_sch.py; below = optional GUI refinement)*

1. **Open the project** `multi-channel-cremat-amplifier.kicad_pro`. Confirm the `cremat`
   symbol lib resolves (Preferences → Manage Symbol Libraries → it's in the project table).
2. **Create `channel.kicad_sch`** (one hierarchical sheet) and capture **one channel** from
   [integration-notes.md](integration-notes.md):
   - Place: `J_BIAS`, `J_SIPM`, `J_OUT` (Conn_Coaxial), `Rf1`, `Rf2`, `Cf`, `JP_Rf1`,
     `JP_Rf2`, `Cc`, `U_CSP` (cremat:CR-11X), `U_SHAPER` (cremat:CR-200), `U_BLR`
     (cremat:CR-210), `JP_BLR`, `U_BUF` (cremat:THS3491xDDA, DNP by default), `R_OUT`, trimpots, decoupling.
   - Wire by the **net→pin table** in integration-notes.md. Internal nets (`BIAS_IN`,
     `N_filt`, `FE`, `CSP_IN`, `CSP_OUT`, `SH_OUT`, `PZ`, `BLR_OUT`, `BUF_OUT`, `OUT`) =
     local labels; `+VDC`/`-VDC`/`GND` = **hierarchical labels** (the only sheet ports).
   - **Bias filter** = `Rf1`+`Cf`+`Rf2`, with `JP_Rf1`∥`Rf1` and `JP_Rf2`∥`Rf2`.
   - **CR-210** between `SH_OUT` and `BLR_OUT`, with `JP_BLR`∥ the module.
   - **P/Z network + buffer**: copy the sub-circuit from
     `reference/cremat-x6-board/channel.kicad_sch` (open it side-by-side), resizing passives
     to 0805. That gives the exact gain/feedback/offset network.
   - Set `DNP` per the **Full** variant ([bom/bom.md](bom/bom.md)): `JP_Rf1/JP_Rf2/JP_BLR`
     DNP; everything else fitted.
3. **Root sheet** `multi-channel-cremat-amplifier.kicad_sch`: place **12 sheet instances**
   of `channel.kicad_sch` (`ch1..ch12`); wire all 12 sheets' `+VDC`/`-VDC`/`GND` pins to the
   rails; add `J_PWR` (3-pos screw terminal) and a **PWR_FLAG** on each of `+VDC`/`-VDC`/`GND`
   so ERC sees them driven.
4. **Annotate** → **assign footprints** per [bom/bom.md](bom/bom.md) (stock libs; create the
   one MCX footprint — see [lib/cremat.pretty/README.md](lib/cremat.pretty/README.md)).
5. **ERC** until 0 errors. Export the netlist + the BOM.

> Gate: ERC 0 errors. The net classes (`hv_bias` etc.) are already in the project.

---

## Track 6 — PCB layout

**The board is scaffolded headless** by [gen_pcb.py](gen_pcb.py) (KiCad bundled python):
```
"C:/Program Files/KiCad/10.0/bin/python.exe" hardware/gen_pcb.py   # 217 footprints + nets + outline + M3 + GND zone
bash scripts/drc.sh                                                # DRC -> reports/drc.json
```
That gives a `.kicad_pcb` with **every footprint placed and every net assigned** (from the
verified netlist), a 225×235 mm outline, 4× M3 holes, and an (unfilled) GND zone. **What it is
NOT:** routed, or arranged for manufacture — `pcbnew` has no autorouter, the parts sit on a
grid, and the edge-launch MCX cutouts must be moved to the board edge. So the GUI work is:

1. (Already done by gen_pcb.py: parts + nets imported.) Set the **stackup** (4-layer 1.6 mm
   recommended; ground plane under the analog chain).
2. **Outline ≈ 225 × 235 mm**, 4× M3 holes — per [mechanical.md](mechanical.md). Confirm
   against the real tray interior first.
3. **Placement:** 12 identical channel cells in rows; **inputs (`J_BIAS`+`J_SIPM`) on one
   long edge, `J_OUT` on the other** (signal flows across). Keep each front-end node compact.
4. **Net classes** apply automatically (`hv_bias` 0.6 mm clearance on `BIAS*`/`SIPM*`/`FE*`;
   `signal` 0.33 mm for `OUT*`; `power` 0.5 mm). Guard the front-end node.
5. **Route** — either the KiCad interactive router, or **autoroute with FreeRouting**:
   clean placement (no clearance/short DRC) → `export_dsn.py` (or GUI Specctra DSN export)
   → FreeRouting → `import_ses.py` (or GUI Specctra Session import). Full steps +
   FreeRouting download in [../docs/FREEROUTING.md](../docs/FREEROUTING.md).
6. Pour + stitch grounds (after routing). **DRC until 0 errors** (creepage is an error).

> Gotcha (from `reference/ets-breakout`): headless `ZONE_FILLER.Fill()` segfaults — fill
> zones as a separate pass / in the GUI. Run `kicad-cli pcb drc` as the gate.

---

## Track 7 — Fabrication & assembly

1. Generate fab outputs (a KiCad **job set** is easiest):
   ```
   "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb export gerbers <pcb> -o fab/gerber/
   "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb export drill   <pcb> -o fab/drill/
   "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb export pos      <pcb> -o fab/pos.csv --format csv --units mm
   ```
2. Export the **fielded BOM** with the **Full** DNP set (already drafted in
   [bom/bom.md](bom/bom.md)); reconcile against the schematic export.
3. Order FR4/ENIG, 1.6 mm. Assemble per
   [../docs/fabrication/fabrication-guide.md](../docs/fabrication/fabrication-guide.md);
   bench bring-up + the Track 2 checklist in
   [../docs/hardware/circuit-design.md](../docs/hardware/circuit-design.md).

> `fab/`, `gerber/`, etc. are git-ignored — regenerate before ordering.
