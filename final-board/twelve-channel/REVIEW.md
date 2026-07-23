# REVIEW — 12-channel Cremat amplifier, engineer review pack

> Prepared **2026-07-23** for design review before ordering. This is the entry point: it answers
> the two questions raised in the last round, states exactly what is and is not verified, and
> lists the specific things that need a human's eyes rather than a script's.
>
> Board: **12-channel SiPM charge-sensitive preamp / Gaussian shaper**, 213.3 × 334.8 mm, 4-layer.
> Per channel: SiPM bias front-end → **CR-112** CSP → **CR-200-1µs** shaper → **CR-210** BLR
> (optional, 0R-bypassable) → **THS3491** buffer, 50 Ω back-terminated. All 36 Cremat module
> sites are **socketed**. 48 edge-mount MCX (24 per long edge).

---

## 1. Your two questions

### "There's no thermal relief on pins connected to the ground pour."

**Correct, and it was worse than it looked — thank you.** The zones were set to
`ZONE_CONNECTION_NONE`, which does not merely omit spokes: it **isolates the pour from every pad**.
The GND pour and the In1 GND plane were contributing *nothing* to the ground return — all GND was
being carried by tracks and vias. DRC still reported 0 unconnected (the tracks satisfied
connectivity), so no automated check ever flagged it.

**Fixed.** All four zones are now `THERMAL`, gap 0.5 mm, spoke 0.5 mm, refilled. Routing is
untouched (tracks 1920, vias 388, footprints 468 — all unchanged); only zone fill geometry changed.

Thermal spokes rather than solid (`FULL`) connections because **218 GND pads on this board are
hand-soldered** — 120 SIP-8 socket pins, 96 MCX shield pads, 2 screw-terminal pins. Soldering those
into a 65 000 mm² plane wicks heat faster than a hand iron replaces it. The cost of spokes here is
negligible: rail draw is milliamps per channel, and ~1–2 nH of spoke inductance against a ~350 kHz
knee is under 10 µΩ. **If you disagree — e.g. you want `FULL` on the MCX shields specifically for
return integrity and are willing to hand-solder into plane — that's a one-line change; say so.**

Details: [`docs/hardware/pcb-design-rules.md` § Copper zones and pad connection](../../docs/hardware/pcb-design-rules.md).

### "Why 4 layers? Is this for impedance control? 2-layer is faster and cheaper."

**It is explicitly *not* impedance control.** This board is ordered as a **normal, non-impedance
4-layer** build, and that is deliberate: the fastest signal is a ~1 µs Gaussian pulse (knee
≈ 350 kHz), so a quarter-wave in FR-4 is ~100 m — roughly 1000× any trace here. Transmission-line
behaviour is irrelevant, and you're right that a 50 Ω width on 2-layer would be an equally valid
non-answer. (The outer traces are grounded-coplanar anyway, not microstrip, so a "microstrip 50 Ω"
width would read low here regardless.)

The fourth layer buys **plane-based power and return distribution**. The routed board makes it
numerical:

> **464 of 1290 pads are `GND` / `+VDC` / `−VDC`** (364 / 50 / 50), and those three nets carry only
> **490 mm of track in total** across a 213 × 335 mm board — because every one of those pads drops
> through a via straight onto its plane (240 GND vias, 50 per rail).
> **A 2-layer build has to route all 464 of those as tracks**, in the same two layers that already
> carry 12 analog signal chains and 12 HV bias nets.

Three reasons that specifically matters here:

1. **The return path is the signal.** A CSP is a charge integrator — it sums *every* current
   arriving at its input. Return current from a neighbouring channel through shared ground metal
   shows up at that input as charge, indistinguishable from a real SiPM event. A solid GND plane
   directly beneath the analog chain gives each channel a low-impedance image return under its own
   trace. On 2 layers the bottom-side ground must be sliced by rail routing, and every slice
   re-introduces the shared impedance. With 12 channels on one board, inter-channel crosstalk is
   the dominant systematic risk.
2. **Bipolar rails to all 12 channels.** `+VDC` *and* `−VDC` are two more distribution networks on
   top of ground. There is no 2-layer arrangement that holds GND + two rails + 12 signal chains +
   12 HV bias nets and leaves the ground solid.
3. **HV bias competes for the same space.** The 12 bias nets run on a 0.6 mm-clearance class; their
   creepage keep-outs eat outer-layer routing channels, and clearance here is a safety rule.

Cost: at this size and quantity JLC's 4-layer adder is small, and well below one respin. The
4-layer version is already routed and DRC-clean, so 4→2 is a full re-layout, not a stackup swap.

Full write-up: [`docs/hardware/pcb-design-rules.md` § Why four layers](../../docs/hardware/pcb-design-rules.md).

---

## 2. Verified state (re-run it yourself)

```bash
"C:/Program Files/KiCad/10.0/bin/python.exe" final-board/twelve-channel/design/check_board.py
```

New this round: `check_board.py` is the acceptance gate as a **runnable tool** (it previously
existed only as throwaway code, so you couldn't reproduce it). Current output — all gates pass:

| Gate | Result |
|---|---|
| ERC | **0** |
| DRC (`--severity-all`, incl. `--schematic-parity`) | **0** violations / **0** unconnected / **0** parity |
| **Pad-net parity** (board pads vs schematic netlist) | **1290 / 1290** match |
| **Footprint ↔ symbol UUID bijection** | **464 ↔ 464**, no collisions (+4 mounting holes, board-only) |
| Copper zones | 4 zones, all **filled**, all **THERMAL** |
| Netclasses | all 4 carry their schematic fields; `hv_bias` measures 0.4 mm, `power` 0.5 mm in copper |
| CPL vs board | 246 / 246 designators, no DNP in CPL, positions current |

**Why a custom tool instead of the stock checks** — each of these has bitten this project:
`kicad-cli` **never reads `.kicad_pro`**, so ERC and netlist export are structurally blind to every
project-file defect; `kicad-cli pcb drc --schematic-parity` **does not compare pad nets** (it is
footprint-level only, and reported 0 while the GUI showed 199+); and "0 unconnected" says nothing
about whether the pours participate — which is exactly how the zone bug above survived. Each check
in the tool prints what it *cannot* see.

**Census:** 468 footprints (120 DNP), 1342 pads, 272 nets, 1920 tracks, 388 vias, 4 copper layers.

---

## 3. What I need your eyes on (no script can check these)

Ranked by how much a mistake would cost.

1. **Circuit correctness per channel.** Everything above proves *board == schematic*. Nothing
   proves the schematic is *right*. Please read one channel sheet end-to-end — the bias front-end
   topology, component values, the CR-210 bypass jumper arrangement, and the buffer feedback
   network. All 12 channels are byte-identical copies of this one cell, so an error here is an
   error ×12. Start: open `design/twelve-channel.kicad_pro` in the GUI (**not** a child sheet
   directly) and descend into `ch01`.
2. **HV creepage vs the actual SiPM bias voltage.** The board is built to **≤ 70 V bias with
   100 V-rated parts** (decision D1) → `hv_bias` 0.6 mm clearance / 0.4 mm track, confirmed in
   copper. **Please confirm ≤ 70 V still matches the SiPM you intend to run** — this is the one
   parameter that, if it moves upward, invalidates both the clearance rule and the `Cc`/`Cf`
   ratings. *Housekeeping done this round: the status docs disagreed (`session-report.md` and
   `CLAUDE.md` carried an older ≤ 60 V figure, and `CLAUDE.md` still called the range unresolved);
   both now match D1. No copper is affected — 0.6 mm covers either figure — but the disagreement
   is worth knowing about, since it's the number the HV rules hang off.*
3. **Polarised-part rotation, in JLC's own parts preview, before you click order.** Rotation
   convention differs between KiCad and JLC and no local check catches it. This is the classic way
   to scrap an assembly run.
4. **The `OUT_50` output runs.** Each channel's buffer output is 50 Ω back-terminated and then runs
   **~76 mm at 0.4 mm width** across the board to the right-edge MCX. My check initially flagged the
   width as inconsistent with the 0.33 mm `signal` class; on inspection it's simply wider (the class
   width is a default, not a cap) and wider is better on a long run. Worth your judgement on whether
   0.4 mm / that routing is what you'd want for a back-terminated output driving cable.
5. **Grounding strategy.** One continuous GND plane is shared by all 12 channels — no partitioning,
   no star point, no analog/digital split (there is no digital). Deliberate, but it's the kind of
   decision worth a second opinion on a 12-channel instrument.
6. **The empty right third of the board.** Not an oversight: board *width* is set by the rack
   enclosure (Hammond RM1U1908VBK, slot-through front/rear panels) so the MCX barrels reach both
   bulkheads. The area is spare by construction.
7. **The DNP / variant tables** in [`docs/hardware/bom.md`](../../docs/hardware/bom.md) — the single
   source of truth for what's fitted in each build. 120 of 468 footprints are DNP; please sanity-check
   the "Full" column against what you expect to be populated.

---

## 4. Open items (not blockers)

- **Bench-verify after first boards** (from the design log, unchanged): CR-112 output-step sign ·
  warm-vs-cold overvoltage offset from the 20 kΩ drop · single-p.e. amplitude and whether CR-112 vs
  CR-113 is the right gain · pole-zero trim.
- **Re-verify LCSC / DigiKey part numbers at order time** — last live-verified 2026-07-11; stock moves.
- **Build plan as documented:** JLC fab qty 5 (their 4-layer minimum; 3 free spare bare boards),
  assembly qty 2; DigiKey hand parts at 2-board quantities +20% spares.

## 5. Where things are

| | |
|---|---|
| Open this in KiCad | `final-board/twelve-channel/design/twelve-channel.kicad_pro` |
| Acceptance gate | `final-board/twelve-channel/design/check_board.py` |
| Fab package (JLC) | `final-board/twelve-channel/design/fab/jlc/` — gerber zip (2.72 MB, 28 files), BOM, CPL |
| ↳ note | The **BOM and CPL are committed**; the **gerber zip is gitignored** (regenerable, per `.gitignore`). It exists locally and is current. If you clone fresh, rebuild it — see below. |
| Ordering walkthrough | [`ORDERING.md`](ORDERING.md) |
| Board-level overview | [`INTERFACE.md`](INTERFACE.md) · resume notes [`HANDOFF.md`](HANDOFF.md) |
| Design rules / stackup | [`docs/hardware/pcb-design-rules.md`](../../docs/hardware/pcb-design-rules.md) |
| Full change history | `final-board/twelve-channel/design/SESSION_LOG.md` (this round = session 22) |
| SPICE results | `final-board/twelve-channel/sim/SESSION_REPORT.md` |

**Rebuilding the gerber package** (only needed after a fresh clone or a copper change):

```bash
cd "final-board/twelve-channel/design" && "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb export gerbers --output fab/_gerber/ twelve-channel.kicad_pcb && "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb export drill --output fab/_gerber/ twelve-channel.kicad_pcb
```

Then zip the contents of `fab/_gerber/` to `fab/jlc/gerber-twelve-channel-jlc.zip` (28 files).
**Do not pass `--excellon-separate-th`** — JLC's package expects one merged `twelve-channel.drl`,
and that flag splits it into PTH/NPTH.
