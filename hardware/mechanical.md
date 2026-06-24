# Mechanical Spec (Track 4 deliverable)

Outline, placement, and mounting for PCB layout (Track 6). Decisions D2/D3/D5 from
[../docs/development-plan.md](../docs/development-plan.md); intent in
[../docs/hardware/board.md](../docs/hardware/board.md).

## Enclosure

- **1U rack tray ≈ 482 mm × 244 mm × 44.45 mm** (482 ≈ 19", 244 deep, 1U tall).
- Boards mounted **open** (not enclosed) on standoffs to the tray base; cables plug
  directly into the edge jacks. No front panel, no bulkhead cutouts.
- **Two 12-channel boards side-by-side** across the 482 mm width.

## Per-board outline

- **Budget ≈ 225 mm (W) × 235 mm (D).** (482 ÷ 2 = 241, minus tray walls + center gap +
  board-to-wall clearance.) **Confirm against the actual tray interior before fixing the
  edge cut.**
- **Component height < ~35 mm** above the board (1U interior 44.45 mm − standoff ~5–10 mm).
  Tallest parts: vertical Cremat SIP-8 modules, the THT trimpots, and the electrolytics —
  all clear ~35 mm. Use low-profile parts where there's a choice. Board-edge MCX with
  **horizontal** cable exit (no vertical jacks).

## Jack placement (36 × MCX `CONMCX013`)

Split across the two long (~235 mm) edges, following signal flow:

```
   ┌──────────────── INPUT edge (~235 mm) ─────────────────┐
   │  J_BIAS1 J_SIPM1  J_BIAS2 J_SIPM2 ... J_BIAS12 J_SIPM12 │   24 jacks, ~9.8 mm pitch
   │                                                         │
   │   ch1 → ch2 → ... → ch12   (12 identical cell rows,     │
   │   front-end → CR-112 → CR-200 → CR-210 → buffer)        │
   │                                                         │
   │  J_OUT1   J_OUT2   ...            J_OUT12               │   12 jacks, ~19.6 mm pitch
   └──────────────── OUTPUT edge (~235 mm) ─────────────────┘
        J_PWR (3-pos screw terminal) on a short edge
```

- **Input edge:** 24 jacks = each channel's `J_BIAS` + `J_SIPM`, paired by channel.
- **Output edge:** 12 jacks = each channel's `J_OUT`.
- Keep each channel's front-end node (`J_BIAS`→filter→`FE`→`Cc`→CSP) compact and its `OUT`
  trace short; the channel flows straight across the board input-edge → output-edge.

## Mounting

- **4× M3** holes (`MountingHole:MountingHole_3.2mm_M3`), one near each corner, inset for
  standoffs to the tray base. Keep ≥5 mm from board edge and clear of jack courtyards.
- Standoff height 5–10 mm (sets the height budget above).

## Net-class / HV note for layout

- `hv_bias` (the per-channel `BIAS_IN`/`SIPM`/`FE` nets, ≤ 60 V) gets **~1.0 mm
  clearance/creepage**; keep these off plane edges and don't run signals under them.
- `OUT` is `signal` class (≈50 Ω); short, ground-referenced.
- See [../docs/hardware/pcb-design-rules.md](../docs/hardware/pcb-design-rules.md).

## Open (confirm before fab)

- Exact tray **interior width/depth** and standoff pattern from the sourced box → finalize
  the 225 × 235 mm outline and M3 hole coordinates.
- `J_PWR` exact part/position; cable strain relief for the 36 MCX leads on an open tray.
