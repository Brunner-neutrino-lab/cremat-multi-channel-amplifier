# Session report — Multi-channel Cremat amplifier (integration track)

> **Superseded 2026-07-11 (historical setup-phase handoff).** The board is now BUILT and
> order-ready: 213.2 × 334.7 mm, 4-layer, one per Hammond RM1U1908VBK 1U case (slot-through,
> daisy-chained), THS3491 output buffer (DNP-by-default), socketed Cremat modules (Samtec
> SS-108-TT-2). The mechanical/part figures below (e.g. 225 × 235 mm, two boards side-by-side,
> EL5167) reflect the initial plan, not the final board. Current truth: `final-board/twelve-channel/`
> (INTERFACE.md, HANDOFF.md, ORDERING.md, SESSION_LOG sessions 12–15).

Handoff from the **organizing / integrating / managing** track. This session set up the
repository, integrated the two reference projects as submodules, and authored the full
design-specification documentation set for the modified 12-channel board. It did **not**
implement the KiCad project — that is the hardware track's job, and this report is its
brief.

---

## 1. What this session produced

- **Four git submodules under `reference/`:**
  - `cremat-x6-board` (`Brunner-neutrino-lab/cremat-x6-board`) — *what we build*: the
    6-channel CR-110/CR-200 eval board this design derives from.
  - `ets-breakout` (`Brunner-neutrino-lab/ets-breakout`) — *how we build/document*: the
    single-source-of-truth KiCad pipeline + the docs structure imitated here.
  - `cremat-CR-160-R7` (`CrematInc/CR-160-R7`) — *CR-210 reference*: Cremat's open-source
    CR-200/CR-210 eval board; the authority for the CR-210 pinout + bypass-jumper scheme.
  - `cremat-CR-150-R5` (`CrematInc/CR-150-R5`) — *CR-11X reference*: Cremat's open-source
    CSP eval board (origin of the CR-11X symbol).
- **A track breakdown** ([development-plan.md](development-plan.md)): one foundation track
  for parts/models/BOM, parallel tracks for circuit / integration / mechanical, then serial
  schematic → layout → fab tracks, with a dependency graph and the decision list.
- **A complete documentation set** (`README.md`, `CLAUDE.md`, `docs/…`) specifying the
  modified board, with the change list, per-channel circuit, board plan, BOM/DNP logic,
  PCB rules, library plan, fabrication, and operation.
- **Repo hygiene:** `.gitignore` for KiCad/Python/fab cruft.

The documentation is structured so a hardware track (or a future Claude session) can
implement the KiCad project directly from `docs/modifications.md` + the reference channel
sheet.

---

## 2. The design in one paragraph

Take the reference per-channel chain
(`coax → Cc → CR-113 → CR-200-X → buffer → 49.9R → coax`), and: (1) replicate it **12×**;
(2) move all passives to **0805**; (3) insert an **optional CR-210** baseline restorer
between shaper and buffer (0R-bypassable); (4) add an **on-board SiPM bias front-end** —
`BIAS_IN` through an optional RC-in-series-with-R filter to a node that feeds the **SiPM
DC-coupled** and the **amplifier AC-coupled** (via `Cc`). Both detector and amplifier hang
off the one biased node. Full detail in [modifications.md](modifications.md) and
[hardware/channel.md](hardware/channel.md).

---

## 3. Key decisions (with rationale)

- **Documentation-first, mirroring `ets-breakout`.** The user named `ets-breakout` as the
  "how to build" reference; it is fundamentally a markdown doc set + a generated KiCad
  project with a DRC gate. This repo reproduces the doc set now and leaves a clean slot
  (`hardware/`) for the generated project.
- **"Optional" = populate-or-bypass via 0R, resolved by DNP.** No switches/relays. The
  reference board already uses solder/2-pin/3-pin jumpers, so this is idiomatic. The
  mutual-exclusivity of a block and its 0R is the board's one assembly invariant.
- **0805 applies to passives only.** Cremat modules are SIP-8 through-hole; op-amps and
  jacks are their own packages. The docs say so explicitly to avoid an impossible BOM.
- **Bias front-end is the real design work.** Drawn terminal-agnostic; the AC/DC split is
  the standard SiPM readout. The new per-channel HV bias nets drove the addition of an `hv_bias` net
  class with voltage-derived creepage.
- **Single board, not a multi-board system.** Unlike the reference IV-mux systems, this is
  one 12-channel PCB with no controller/firmware.

---

## 4. Status — done vs. open

**Done (this track):** submodules wired; complete spec/docs; repo hygiene.

**Built (Tracks 1, 3, 4 — real, `kicad-cli`-validated artifacts under `hardware/`):**
- `lib/cremat.kicad_sym` (CR-11X/CR-112, CR-200, CR-210, EL5167) — validated with
  `kicad-cli sym upgrade` on KiCad 10. `sym-lib-table`/`fp-lib-table`, the
  `.kicad_pro` with net classes (Default/power/hv_bias/signal + pattern assignment),
  `bom/` (fielded Full-variant BOM + CSV), `integration-notes.md` (golden netlist),
  `mechanical.md`. See [hardware/BUILD-IN-KICAD.md](../hardware/BUILD-IN-KICAD.md).

**Track 5 — schematic: DONE headless (ERC 0 errors).** The earlier "GUI boundary" call was
wrong (corrected per [KICAD_WITH_CLAUDE_CODE.md](KICAD_WITH_CLAUDE_CODE.md)): a generator
[hardware/gen_sch.py](../hardware/gen_sch.py) writes `channel.kicad_sch` + the 12× root by
placing symbols at rotation 0 and dropping net-labels (local) / global-labels (rails) at
exact pin coordinates. `kicad-cli sch erc` → **0 errors** (4 warnings = MCX + screw-terminal
footprint links, expected); exported netlist matches integration-notes.md node-by-node
(217 unique refs, 12 independent `/chN/FE`, global `+VDC/-VDC/GND`).

**Open — Tracks 6/7 (KiCad; toolchain ready):**
1. **MCX footprint** `MCX_CONMCX013_EdgeMount` (datasheet-verified) — the one to-create part.
2. **Layout** (placement via `pcbnew` Python API or file-authoring; dense routing in GUI;
   DRC 0) and **fab** (gerbers/drill/pos + BOM). Guide: `hardware/BUILD-IN-KICAD.md`.

**Resolved this session:**
- ✅ **CR-210 pin map.** Confirmed from `reference/cremat-CR-160-R7` (`CR-160-R7-cache.lib`
  + netlist): `1=input, 2=GND, 3=GND, 4=-Vs, 5=+Vs, 6=GND, 7=GND, 8=output` — identical to
  the CR-200 except pin 2 (P/Z → GND). The CR-160-R7 also confirms the **optional**
  integration: a jumper (`JU1`) across the module's input/output nodes — exactly our
  `JP_BLR` 0R scheme.

**Resolved — Track 2 front-end design** (target = Hamamatsu VUV4 S13370, 6 mm/75 µm;
45–55 V reverse, ≈ 220 fC/V OV, `Cdet` ≈ 1.28 nF — see
[hardware/circuit-design.md](hardware/circuit-design.md)):
- ✅ **Bias filter values:** `Rf1=Rf2=10 kΩ`, `Cf=100 nF/100 V` (`fc≈159 Hz`; cold-only
  boards may raise `Rf` to 100 kΩ–1 MΩ). `Cc=0.22 µF/100 V` (≫ `Cdet` → ~99 % charge transfer).
- ✅ **Polarity:** cathode on the front-end node, **+45…55 V**; anode → GND; positive bias
  supply. CR-112 (13 mV/pC) confirmed appropriate for the VUV4 charge.

**Open — bench-verify (Track 2 checklist, after first boards):** CR-112 output-step sign;
warm-vs-cold OV offset from the 20 kΩ drop; single-p.e. amplitude / CR-112-vs-CR-113 range;
pole-zero trim.

**Resolved — product decisions (D1–D6, 2026-06-24):** bias ≤ 60 V / 100 V parts; all
per-channel I/O is MCX `CONMCX013`; **`BIAS_IN` is per-channel** (architecture correction —
not a shared rail); modules CR-112 + CR-200-1µs (+ CR-210); **1U** open rack tray
≈ 482 × 244 mm, two boards side-by-side on standoffs (per-board ≈ 225 × 235 mm, tall parts
< ~35 mm, no panel/cutouts); first build = Full. Details + the D6 explanation in
[development-plan.md](development-plan.md#decisions--resolved-2026-06-24).

---

## 5. Notes for whoever picks this up

- `reference/` holds **submodules** — never edit inside them or commit into them. Do the
  new design at the top level / under `hardware/`.
- The reference channel sheet
  (`reference/cremat-x6-board/channel.kicad_sch`) is large (~5k lines of s-expr); the
  components and values were extracted into [hardware/channel.md](hardware/channel.md) /
  [hardware/bom.md](hardware/bom.md) so you don't have to re-parse it.
- `CLAUDE.md` carries the iron rules; keep the DNP tables in `hardware/bom.md` as the
  single source of truth for what's populated in each variant.
