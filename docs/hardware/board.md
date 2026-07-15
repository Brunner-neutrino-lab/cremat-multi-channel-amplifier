# Board

Board-level design of the 12-channel amplifier: how the channel cell is replicated, how
power and bias are distributed, and the connector / mechanical intent.

**KiCad project (to be created by the hardware track):** `hardware/multi-channel-cremat-amplifier.kicad_pro`
**Channels:** 12 (one hierarchical sheet, instantiated 12×)

---

## Schematic structure

Mirror the reference board's hierarchy:

```
root sheet  (power entry, bias distribution, 12× channel instances)
 └── channel.kicad_sch   ×12   (the cell documented in channel.md)
```

The reference root (`reference/cremat-x6-board/cremat-board.kicad_sch`) instantiates
`channel.kicad_sch` six times (`ch0…ch5`). Do the same with **twelve** instances
(`ch0…ch11`). Keep the per-channel `BIAS_IN`, `+VDC`, `-VDC`, `GND` as global nets so a
single distribution network on the root sheet feeds every channel.

---

## Power distribution

| Rail | Entry | Distribution |
|---|---|---|
| `+VDC` / `-VDC` (±Vs) | Power connector (screw terminal or header) | Star/bus to each module; **bulk** electrolytics at entry (e.g. 10 µF + 100 µF per rail), **local** decoupling at every Cremat module and op-amp |
| `GND` | same connector | Solid ground plane; common reference for supply and bias |

> **`BIAS_IN` is per-channel, not a shared rail.** Each channel has its own `BIAS_IN` MCX
> jack feeding only its own bias filter — see [Connectors](#connectors). There is no
> board-wide bias distribution net; the bias supply is fanned to the 12 jacks externally.

- The analog supply (`±Vs`, `GND`) **is** shared across all channels.
- Decoupling values follow the reference (per-rail 0.1 µF / 1 µF / 10 µF near modules),
  resized to 0805 where the voltage rating allows.
- Keep each **`BIAS_IN<n>` net away from the ground plane edges** and honor HV creepage
  (≤ 70 V → 0.6 mm, [pcb-design-rules.md](pcb-design-rules.md)).

---

## Connectors

| Connector | Qty | Purpose | Part |
|---|---|---|---|
| `BIAS_IN` (per channel) | 12 | HV detector bias in (≤ 70 V), one per channel | **MCX edge-mount, TE Linx `CONMCX013`** (DK `343-CONMCX013-ND`) |
| `SIPM` (per channel) | 12 | Coax to each detector (DC bias + signal) | same `CONMCX013` |
| `TEST` (per channel) | 12 | Per-channel test-pulse injection / monitor | same `CONMCX013` |
| `OUT_50` (per channel) | 12 | 50 Ω shaped output to DAQ | same `CONMCX013` |
| `J_PWR` (supply in) | 1 | Analog supply in (±Vs, GND) | **3-pos 5.08 mm Phoenix screw terminal** |
| `J_DAISY` (rails out) | 1 | Raw ±Vs / GND daisy-chained to the next 1U box | **3-pos 5.08 mm Phoenix screw terminal** |

- **All four per-channel jacks are the same MCX part — `CONMCX013` — so 48 MCX/board.**
  50 Ω, female, board-edge cutout, SMT. Track 1 pulls its datasheet/footprint/3D model
  ([component-libraries.md](component-libraries.md)).
- **Two power terminals, not one:** `J_PWR` takes the supply in and `J_DAISY` passes the raw
  rails out to the next 1U box — the power connector is not the only shared connector.
- Group each channel's `BIAS_IN` + `SIPM` + `TEST` + `OUT_50` near its cell to keep the bias
  node and the output trace short. 48 edge jacks dominate the board outline and the panel layout.

---

## Layout intent

1. **Channel pitch = module height.** The Cremat SIP-8 modules stand vertically; lay the
   12 cells out on a regular pitch so the modules form neat rows (as on the reference
   board) and the coax jacks line the edges.
2. **Front-end node is the sensitive node.** Keep `BIAS_IN→filter→node→Cc→CSP` compact;
   minimize the high-impedance amplifier-input copper. Consider a guard around it
   (the reference and `ets-breakout` both guard sensitive analog nodes).
3. **Bias-net isolation.** Route each `BIAS_IN<n>` and its filtered bias as the `hv_bias`
   net class with extra clearance (≤ 70 V → 0.6 mm); do not run signal traces under it.
4. **Output side is 50 Ω.** The `49.9R` (with the THS3491 buffer DNP-bypassed by default)
   drives the coax; keep `OUT` traces short and reference them to ground. The board is **not**
   ordered controlled-impedance — the ~1 µs pulse bandwidth makes transmission-line effects
   negligible (see [pcb-design-rules.md](pcb-design-rules.md)).
5. **Ground plane** continuous under the analog chain for low-noise return.

---

## Mechanical (D5 — 1U vented rack case, one board per case, slot-through panels)

- **Board outline:** **213.2 × 334.7 mm**, 4-layer — **one** 12-channel board per case.
- **Enclosure:** **Hammond RM1U1908VBK**, a **1U vented** rack case (1U outer ≈ 44.45 mm).
  Usable interior: **196.85 mm deep × 40.09 mm high × 415.30 mm wide**. **One board per
  case** — boards are never stacked or set side-by-side inside one box.
- **Slot-through panel mount.** Each long (334.7 mm) board edge passes **through a
  ~340 × 7 mm milled slot** in the front/rear panel and **protrudes ~5 mm**, so the
  edge-mount MCX faces sit **~8.6 mm proud** of the panel and mate in the open (snap-on MCX).
  This is **not** a bulkhead-flush mount and **not** an open tray — the board is captured by
  the two panel slots and stands off the case **bottom cover** on M3 standoffs.
- **Height (1U):** every part — the vertical socketed Cremat SIP-8 modules, the trimpots, the
  bulk electrolytics, and the MCX + its mated cable — must fit the **40.09 mm** usable
  interior height, minus standoff height.
- **Edge jacks:** the **48 MCX** split **24 per long edge / panel** — one panel presents the
  inputs (`BIAS_IN` + `SIPM`), the other presents `TEST` + `OUT_50` — so each channel lays out
  as **input-edge → amplifier chain → output-edge**.
- **Scaling: daisy-chain, don't widen.** More channels means more boards, each in its **own
  1U RM1U1908VBK box**; **`J_DAISY`** carries the raw ±Vs / GND rails from one box to the next,
  so supplies chain box-to-box instead of sharing a backplane. **Never** two boards in one
  case, never an open rack tray, never open-air.
- This drives Track 4 (mechanical) and constrains Track 6 (layout).

> Board dimensions, exact jack placement, and the outline are defined in the KiCad PCB
> once implemented; this document is design intent, the PCB file is authoritative
> (same convention as `ets-breakout`).

---

## Bill of optional configurations (board build variants)

A given board is assembled in one configuration; the common ones:

| Build | Bias filter | CR-210 | Use case |
|---|---|---|---|
| **Full** ← *first build (D6)* | fitted | fitted | On-board bias + high-rate spectroscopy |
| **No-BLR** | fitted | bypassed | On-board bias, low rate / minimal latency |
| **External-bias** | bypassed | (either) | Clean external bias supply / external bias-tee |
| **Reference-equivalent** | bypassed | bypassed | Behaves like the original 6-ch board (×12) |

See the DNP tables in [bom.md](bom.md) for the exact populate/DNP set per variant.
