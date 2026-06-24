# Session report — Multi-channel Cremat amplifier (integration track)

Handoff from the **organizing / integrating / managing** track. This session set up the
repository, integrated the two reference projects as submodules, and authored the full
design-specification documentation set for the modified 12-channel board. It did **not**
implement the KiCad project — that is the hardware track's job, and this report is its
brief.

---

## 1. What this session produced

- **Two git submodules under `reference/`:**
  - `cremat-x6-board` (`Brunner-neutrino-lab/cremat-x6-board`) — *what we build*: the
    6-channel CR-110/CR-200 eval board this design derives from.
  - `ets-breakout` (`Brunner-neutrino-lab/ets-breakout`) — *how we build/document*: the
    single-source-of-truth KiCad pipeline + the docs structure imitated here.
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
  the standard SiPM readout. The new HV bias rail drove the addition of an `hv_bias` net
  class with voltage-derived creepage.
- **Single board, not a multi-board system.** Unlike the reference IV-mux systems, this is
  one 12-channel PCB with no controller/firmware.

---

## 4. Status — done vs. open

**Done (this track):** submodules wired; complete spec/docs; repo hygiene.

**Open — hardware track (implementation):**
1. Create `hardware/` KiCad project: re-home reference symbols, build the channel
   hierarchical sheet with the bias front-end + CR-210 + 0R jumpers, instantiate 12×, lay
   out, route, DRC-clean (0 errors), generate fab + BOM. Follow `ets-breakout`'s pipeline.
2. Build the project library (`lib/cremat.kicad_sym`, `cremat.pretty/`) incl. the CR-210
   and the SIP-8 footprint reuse — see [hardware/component-libraries.md](hardware/component-libraries.md).

**Open — verification (must close before fab):**
1. **CR-210 pin map.** Confirm the exact 8-pin SIP assignment against the **`CR-210-R0`
   spec sheet** (input/output/±Vs/GND). It is a distinct module — do **not** copy the
   CR-200 pinout. *(This session pulled the CR-210 datasheet but the PDF pinout could not
   be auto-extracted; needs a human read or a clean copy.)*
2. **SiPM bias voltage range.** Sets `hv_bias` creepage and the voltage rating of `Cc`/`Cf`
   (reference uses 100 V parts). Get the target detector's operating bias from the user.
3. **Bias filter R/C values.** Pick `Rf`,`Cf` for the detector's bias current + the noise
   to reject (docs give 10 kΩ / 100 nF as a *placeholder*, not a final value).
4. **SiPM terminal polarity** (cathode- vs anode-bias) and CR-11X input polarity.

**Open — product decisions (ask the user):**
- Coax jack type for `SIPM`/`OUT` (MCX vs SMA), and `BIAS_IN` connector (SHV?).
- CR-200-X shaping time and CR-11X gain grade to order.
- Whether per-channel bias trim is ever wanted (currently one shared `BIAS_IN`).

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
