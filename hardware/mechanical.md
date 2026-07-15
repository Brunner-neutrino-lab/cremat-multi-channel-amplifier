# Mechanical Spec (Track 4 deliverable)

Outline, placement, and mounting for PCB layout (Track 6). Decisions D2/D3/D5 from
[../docs/development-plan.md](../docs/development-plan.md); intent in
[../docs/hardware/board.md](../docs/hardware/board.md).

## Enclosure

- **Hammond RM1U1908VBK** — 1U, **vented**, 19" rack; **one 12-channel board per case.**
  Usable interior **196.85 mm (D) × 40.09 mm (H) × 415.30 mm (W)** (1U outer nominal is
  44.45 mm; usable interior height is 40.09 mm).
- The board is **enclosed** (not an open tray): it mounts on standoffs off the case
  **bottom cover** and passes **slot-through** the front and rear panels (see Panel
  mounting below).
- **Multiple boards are daisy-chained**, each in its own 1U box — `J_DAISY` passes the raw
  supply rails box-to-box. Never two boards stacked or side-by-side in one case.

## Per-board outline

- **213.2 mm × 334.7 mm**, 4-layer (F.Cu / In1 = GND plane / In2 = −VDC plane /
  B.Cu = +VDC pour).
- The 334.7 mm **long edges** run parallel to the front/rear panels and carry the MCX. The
  board is deeper (213.2 mm) than the case interior depth (196.85 mm), so it **protrudes
  ~5 mm through a milled slot in each panel** and the MCX faces sit **~8.6 mm proud** for
  snap-on cables (see Panel mounting).
- **Component height < ~40 mm** above the board (1U usable interior 40.09 mm − standoff).
  Tallest parts: the **socketed** vertical Cremat SIP-8 modules, the THT trimpots, and the
  electrolytics. Use low-profile parts where there's a choice. Board-edge MCX with
  **horizontal** cable exit (no vertical jacks).

## Panel mounting (slot-through)

- The board passes **through a ~340 mm × 7 mm milled slot** in each front and rear panel
  (the 334.7 mm long edge in a ~340 mm slot). It **protrudes ~5 mm** beyond each panel and
  the edge-mount MCX faces sit **~8.6 mm proud** so snap-on cables mate in the open —
  **not** bulkhead-flush, **not** an open tray.
- Vertical support is the standoffs off the bottom cover; the panel slots locate the board
  fore/aft.

## Jack placement (48 × MCX `CONMCX013`)

**4 MCX per channel** (`BIAS`, `SIPM`, `TEST`, `OUT_50`) = 48 total, **24 per long
(~334.7 mm) edge**, following signal flow:

```
   ┌──────────────── INPUT edge (~334.7 mm) ────────────────┐
   │  BIAS1 SIPM1  BIAS2 SIPM2  ...  BIAS12 SIPM12           │   24 jacks (2/ch)
   │                                                         │
   │   ch1 → ch2 → ... → ch12   (12 identical cell rows,     │
   │   front-end → CR-112 → CR-200 → CR-210 → THS3491 buf)   │
   │                                                         │
   │  TEST1 OUT1  TEST2 OUT2  ...  TEST12 OUT12              │   24 jacks (2/ch)
   └──────────────── OUTPUT edge (~334.7 mm) ───────────────┘
     short edge: J_PWR (supply in) + J_DAISY (raw rails out)
                 — both 3-pos 5.08 mm Phoenix screw terminals
```

- **Input edge:** 24 jacks = each channel's `BIAS` + `SIPM`, paired by channel.
- **Output edge:** 24 jacks = each channel's `TEST` (charge-injection input) + `OUT_50`
  (50 Ω output), paired by channel.
- Keep each channel's front-end node (`BIAS`→filter→`FE`→`Cc`→CSP) compact and its
  `OUT_50` trace short; the channel flows straight across the board input-edge →
  output-edge.

## Mounting

- **4× M3** holes (`MountingHole:MountingHole_3.2mm_M3`), one near each corner, inset for
  standoffs to the case **bottom cover**. Keep ≥5 mm from board edge and clear of jack
  courtyards.
- Standoff height 5–10 mm (sets the height budget above; 1U usable interior 40.09 mm).

## Net-class / HV note for layout

- `hv_bias` (the per-channel `BIAS_IN`/`SIPM`/`FE` nets, ≤ 70 V) gets **0.6 mm
  clearance/creepage** (0.4 mm track); keep these off plane edges and don't run signals
  under them.
- `OUT` is `signal` class (≈50 Ω); short, ground-referenced.
- See [../docs/hardware/pcb-design-rules.md](../docs/hardware/pcb-design-rules.md).

## Open (confirm before fab)

- Standoff pattern / M3 hole coordinates against the RM1U1908VBK bottom cover; final panel
  slot position and height so the two MCX rows clear the ~340 × 7 mm cut-outs.
- `J_PWR` / `J_DAISY` exact positions; cable strain relief for the 48 MCX leads at the
  panels.
