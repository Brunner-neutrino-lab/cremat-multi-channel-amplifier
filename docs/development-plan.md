# Development Plan — Tracks

How the build is divided into work tracks, what each owns, and what can run in parallel.
The integration track (Track 0) owns this document and the gates between tracks.

A **track** here is a self-contained unit of work with explicit inputs, deliverables, and a
definition-of-done — sized so it can be handed to one person (or one focused Claude
session) and progressed independently of its siblings.

---

## Track map at a glance

```
                 ┌──────────────────────────────────────────────────────────┐
   Track 0  ─────┤  COORDINATION & INTEGRATION (owns spec, gates, DNP truth)  │  (continuous)
                 └──────────────────────────────────────────────────────────┘
                                      │ feeds requirements ↓
   ── Phase 1 : parallel ────────────────────────────────────────────────────
        Track 1  Parts, Models & BOM ............ datasheets, symbols, footprints, 3D, BOM
        Track 2  Circuit & Front-End Eng. ....... R/C values, ratings, polarity, decoupling
        Track 3  Reference Integration .......... pinouts + per-channel "golden" topology
        Track 4  Mechanical, Connectors & I/O ... jacks, outline, pitch, mounting, enclosure
   ── Phase 2 : serial (each gated by the previous) ──────────────────────────
        Track 5  Schematic Capture .............. needs 1(symbols) 2(values) 3(topology)
        Track 6  PCB Layout ..................... needs 5(netlist) 1(footprints) 4(mech)
        Track 7  Fabrication & Assembly ......... needs 6(layout) 1(BOM)
```

### Dependency graph

```
        ┌─ Track 1 (parts/models/BOM) ─┬──────────────┬───────────────► Track 7 (BOM half)
        │                              │              │
 T0 ───►├─ Track 2 (circuit values) ──┤              ▼
        │                              ├──► Track 5 ──► Track 6 ──► Track 7 (fab)
        ├─ Track 3 (topology/pinouts) ─┘   (schem.)    (layout)
        │
        └─ Track 4 (mechanical) ───────────────────────► Track 6
```

Phase-1 tracks (1–4) have **no dependencies on each other** and start immediately. Phase-2
tracks (5→6→7) are serial. Track 0 runs throughout.

---

## Track 0 — Coordination & Integration  *(this track)*

- **Owns:** the spec (`docs/`), this plan, the cross-track decision list, and the
  **DNP / populate source-of-truth** ([hardware/bom.md](hardware/bom.md)).
- **Does:** resolve cross-track questions, gate each handoff (sign off a track's
  definition-of-done before the dependent track starts), keep the four reference
  submodules wired, merge work, run `git`/DRC/ERC gates.
- **Decisions to pull from the user** (these unblock Phase-1 tracks — D1–D6 now resolved,
  see [§ Decisions](#decisions--resolved-2026-06-24)).
- **Done when:** Track 7 produces a fab package that passes the gates and the build
  variants are documented.

---

## Phase 1 — parallel tracks

### Track 1 — Parts, Models & BOM
*The foundation track. Everything downstream consumes its outputs.*

- **Collect, for every part:** datasheet (PDF), KiCad **schematic symbol**, **footprint**
  (`.kicad_mod`), and **3D CAD** (STEP) where available.
- **Reuse the open-source Cremat sources** (now submodules) rather than redrawing:
  | Part | Source submodule | Asset |
  |---|---|---|
  | CR-11X CSP (CR-110/-111/-112/-113) | `reference/cremat-CR-150-R5` | symbol + 8-pin SIP footprint + BOM line |
  | CR-200-X shaper | `reference/cremat-CR-160-R7` | symbol + `8pinSIP` footprint |
  | **CR-210 BLR** | `reference/cremat-CR-160-R7` | symbol + `8pinSIP` footprint (pinout confirmed) |
  | EL5167 / buffer | `reference/cremat-CR-160-R7`, `reference/cremat-x6-board` | symbol |
  | passives, jumpers, coax | `reference/cremat-x6-board`, KiCad std libs | symbols |
- **New / to-source:** 0805 R/C footprints, 0R-jumper footprint, op-amp package, coax jack
  (MCX/SMA per Track 4), HV `BIAS_IN` connector, trimpots, 3D STEP for the SIP-8 module.
- **Produce the BOM:** fielded (`MPN`,`MFN`,`VPN`,`VN`,`DNP`), 0805 passive policy applied,
  with the **optional-population variants** ([hardware/bom.md](hardware/bom.md)).
- **Deliverables:** `hardware/lib/cremat.kicad_sym`, `hardware/lib/cremat.pretty/`,
  3D models, `sym-lib-table`/`fp-lib-table`, and the fielded BOM.
- **Definition of done:** every part on the golden channel + board has a symbol, a
  datasheet-verified footprint, a BOM line, and (where available) a 3D model.
- **Detail:** [hardware/component-libraries.md](hardware/component-libraries.md),
  [hardware/bom.md](hardware/bom.md).

### Track 2 — Circuit & Front-End Engineering

- **Bias filter:** choose `Rf1`,`Rf2`,`Cf` for the SiPM bias current + noise rejection;
  set corner freq, surge/current limit; voltage ratings.
- **AC coupling:** `Cc` value + voltage rating (≥ bias V).
- **Polarity:** SiPM terminal (cathode/anode-bias) vs CR-11X input polarity.
- **Power/decoupling:** per-module decoupling values, bulk caps, rail sizing.
- **Output:** buffer gain, `49.9R` termination, P/Z and gain-trim ranges.
- **Deliverable:** [hardware/circuit-design.md](hardware/circuit-design.md) — **done**:
  values + calculations + rationale for the **Hamamatsu VUV4** (Rf1=Rf2=10 kΩ, Cf=100 nF,
  Cc=0.22 µF; cathode-on-node +45–55 V; CR-112). Bench-verify items listed there.
- **Done when:** ~~every passive value fixed~~ ✅ done on paper; remaining items are
  bench-verify after first boards (CR-112 output sign, warm/cold OV offset, P/Z).
- **Had from user (2026-06-24):** VUV4 S13370, 45–55 V reverse, ≈ 220 fC/V OV, Cdet ≈ 1.28 nF.

### Track 3 — Reference Integration & Channel Topology

- Extract exact **pinouts + recommended integration** of the Cremat modules from the
  open-source boards (largely done — see [§ CR-210 integration](#cr-210-integration-confirmed)).
- Define the **golden per-channel topology**: bias front-end → `Cc` → CR-11X → CR-200-X →
  [CR-210] → buffer → `49.9R` → `OUT`, including the **two bypass jumpers** and their exact
  node connections.
- **Deliverable:** `docs/hardware/integration-notes.md` — authoritative per-channel netlist
  intent + confirmed pinouts, citing the reference boards.
- **Done when:** Track 5 can capture the channel sheet without further reference digging.
- **Detail:** [hardware/channel.md](hardware/channel.md), [modifications.md](modifications.md).

### Track 4 — Mechanical, Connectors & I/O

- Specified (D2/D3/D5): MCX `CONMCX013` I/O; **3-pos screw terminal** for ±Vs/GND;
  **1U open tray**, board ≈ 225 × 235 mm on M3 standoffs, tall parts < ~35 mm. Remaining:
  finalize jack placement + outline (a layout detail, handed to Track 6).
- **Jack placement:** inputs (24 `BIAS_IN`+`SIPM`) on one long edge, outputs (12 `OUT`) on
  the opposite long edge → channel flows input-edge → amplifier → output-edge
  ([hardware/board.md](hardware/board.md)). No bulkhead cutouts (open tray).
- **Deliverable:** `docs/hardware/mechanical.md` + an outline/placement constraint sketch.
- **Done when:** Track 6 has fixed connector parts, an outline, and a placement strategy.
- **Needs from user:** cabling standard (MCX/SMA), enclosure intent (see Decisions).

---

## Phase 2 — serial / final tracks

### Track 5 — Schematic Capture
- Build the **hierarchical channel sheet** from Track 3's topology, Track 1's symbols, and
  Track 2's values; instantiate **12×**; root sheet with `+VDC`/`-VDC`/`GND` + `BIAS_IN`
  distribution. ERC clean.
- **Gated by:** Tracks 1, 2, 3. **Deliverable:** `hardware/*.kicad_sch`, ERC 0, netlist.

### Track 6 — PCB Layout
- Place (channel pitch from Track 4), route (net classes incl. `hv_bias`, guard on the
  front-end node), pour zones, **DRC 0** (creepage as error).
- **Gated by:** Track 5 (netlist), Track 1 (footprints), Track 4 (mechanical).
- **Deliverable:** routed `hardware/*.kicad_pcb`, DRC 0/0.
- **Rules:** [hardware/pcb-design-rules.md](hardware/pcb-design-rules.md).

### Track 7 — Fabrication & Assembly
- Generate gerbers/drill/pos, finalize the BOM with **DNP variants**, build the fab
  package, write the assembly/bring-up steps.
- **Gated by:** Track 6 (layout), Track 1 (BOM).
- **Deliverable:** fab zip + [fabrication/fabrication-guide.md](fabrication/fabrication-guide.md) kept current.

---

## Phase 2 kickoff briefs (one line each)

- **Track 5 (Schematic):** Capture the per-channel cell from
  [hardware/channel.md](hardware/channel.md) + [hardware/circuit-design.md](hardware/circuit-design.md)
  — bias front-end (`Rf1=Rf2=10k`, `Cf=100n`, `JP_Rf` 0R bypass) → `Cc=0.22µF` → CR-112 →
  CR-200-1µs → optional CR-210 (`JP_BLR` 0R across it) → buffer → `49.9Ω` → `OUT` — using
  Track 1's re-homed Cremat symbols, instantiate it **12×** on a root sheet that fans the
  shared `±Vs`/`GND` (screw terminal) and per-channel `BIAS_IN`/`SIPM`/`OUT` (MCX) nets, and
  deliver an **ERC-clean netlist**.
- **Track 6 (Layout):** From the Track 5 netlist and Track 1 footprints, place the 12
  identical cells into the **≈225 × 235 mm, 1U** open-tray envelope (tall parts < ~35 mm) with
  inputs (`BIAS_IN`+`SIPM`) on one long edge and `OUT` on the other, apply the net classes
  (`hv_bias` ~1.0 mm creepage on the ≤60 V bias nets, guarded front-end node, 50 Ω `OUT`),
  pour/stitch grounds, and reach **DRC 0/0**.
- **Track 7 (Fab/Assembly):** From the DRC-clean board, generate the fab package
  (gerbers + Excellon drill + position CSV) and the fielded BOM with the **Full-variant DNP
  set** (bias filter + CR-210 fitted, all `JP_*` bypasses DNP), order as FR4/ENIG, and update
  [fabrication/fabrication-guide.md](fabrication/fabrication-guide.md) with the as-built
  assembly + bring-up steps.

---

## CR-210 integration (confirmed)

From Cremat's own open-source eval board
[`reference/cremat-CR-160-R7`](../reference/cremat-CR-160-R7/) (`U4`=CR-200, `U5`=CR-210,
`JU1`=bypass jumper):

**Pinout (8-pin SIP, footprint `8pinSIP`) — differs from CR-200 only at pin 2:**

| Pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| CR-210 | input | **GND** | GND | -Vs | +Vs | GND | GND | output |
| CR-200 | input | P/Z | GND | -Vs | +Vs | GND | GND | output |

**Optional-via-jumper (exactly the scheme this project uses for `JP_BLR`):**

```
CR-200 out (U4.8) ──┬──► CR-210 in (U5.1)        CR-210 out (U5.8) ──┬──► onward (R20 → buffer)
                    │                                                 │
                    └────────────── JU1 ──────────────────────────────┘   (jumper across the module)
```

- **BLR active:** populate CR-210, **leave JU1 open**.
- **BLR bypassed:** remove CR-210, **close JU1** → shaper output passes straight through.

In this design `JU1` becomes the 0805 `JP_BLR` 0R link, and the same pattern (a 0R across a
series block) is reused for the bias-filter bypass. The bias front-end and the 12× repeat
are this board's additions on top of the single-channel CR-160-R7 reference.

---

## Decisions — resolved 2026-06-24

| # | Decision | Answer | Gates |
|---|---|---|---|
| D1 | SiPM bias voltage range | **≤ 60 V**; keep all HV parts (`Cc`,`Cf`) rated **100 V** → `hv_bias` creepage from the ≤100 V row (~1.0 mm) | T2, T3, PCB rules |
| D2 | `SIPM`/`OUT` jack | **MCX edge-mount, TE Connectivity Linx `CONMCX013`** (DK `343-CONMCX013-ND`), 50 Ω SMT board-edge | T1, T4 |
| D3 | `BIAS_IN` connector | **Same MCX `CONMCX013`** — *not* SHV | T1, T4 |
| D4 | Modules to order | shaper **CR-200-1µs**; CSP **CR-112** (reference x6-board used CR-113) | T1 (BOM) |
| D5 | Enclosure | **1U rack tray ≈ 482 × 244 mm**; boards **open** (no enclosure / panel / bulkhead cutouts), mounted flat on standoffs → per-board outline **≈ 225 × 235 mm**, tall parts **< ~35 mm** (1U). See [hardware/board.md](hardware/board.md) | T4 |
| D6 | First-build variant | **Full (bias filter fitted + CR-210 fitted)** — confirmed; changeable per build | T7 |

### ⚠ Connector clarification (architecture-affecting)
**`SIPM`, `OUT`, and `BIAS_IN` are all per-channel** — three MCX `CONMCX013` jacks per
channel → **36 MCX per board**. `BIAS_IN` is **not** a single shared rail; each channel has
its own bias-input connector feeding its own (optional) bias filter. The bias supply is
fanned to the per-channel `BIAS_IN` jacks externally (e.g. an external splitter), or each
channel is biased independently.

### D6 explained (the one you flagged)
Each board is soldered in *one* fixed configuration, because the optional blocks are
populate-or-bypass (0R / DNP), not switchable. D6 just asks **what to populate on the first
batch**: bias filter fitted vs bypassed, and CR-210 fitted vs bypassed (the four variants in
[hardware/board.md](hardware/board.md)). **Decided: the first build is Full** (bias filter
+ CR-210 both fitted) — on-board biasing with baseline restoration. Later boards can use a
different variant at no design cost (just a DNP change).

Tracked alongside the open engineering items in [session-report.md](session-report.md).
