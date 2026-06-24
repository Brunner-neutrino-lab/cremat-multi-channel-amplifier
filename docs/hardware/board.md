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
  (≤ 60 V → ~1.0 mm, [pcb-design-rules.md](pcb-design-rules.md)).

---

## Connectors

| Connector | Qty | Purpose | Part |
|---|---|---|---|
| `BIAS_IN` (per channel) | 12 | HV detector bias in (≤ 60 V), one per channel | **MCX edge-mount, TE Linx `CONMCX013`** (DK `343-CONMCX013-ND`) |
| `SIPM` (per channel) | 12 | Coax to each detector (DC bias + signal) | same `CONMCX013` |
| `OUT` (per channel) | 12 | 50 Ω shaped output to DAQ | same `CONMCX013` |
| Power (±Vs, GND) | 1 | Analog supply (shared) | Screw terminal / locking header |

- **All three per-channel jacks are the same MCX part — `CONMCX013` — so 36 MCX/board.**
  50 Ω, female, board-edge cutout, SMT. Track 1 pulls its datasheet/footprint/3D model
  ([component-libraries.md](component-libraries.md)).
- Group each channel's `BIAS_IN` + `SIPM` + `OUT` near its cell to keep the bias node and
  the output trace short. 36 edge jacks dominate the board outline and the panel layout.

---

## Layout intent

1. **Channel pitch = module height.** The Cremat SIP-8 modules stand vertically; lay the
   12 cells out on a regular pitch so the modules form neat rows (as on the reference
   board) and the coax jacks line the edges.
2. **Front-end node is the sensitive node.** Keep `BIAS_IN→filter→node→Cc→CSP` compact;
   minimize the high-impedance amplifier-input copper. Consider a guard around it
   (the reference and `ets-breakout` both guard sensitive analog nodes).
3. **Bias-net isolation.** Route each `BIAS_IN<n>` and its filtered bias as the `hv_bias`
   net class with extra clearance (≤ 60 V → ~1.0 mm); do not run signal traces under it.
4. **Output side is 50 Ω.** The `49.9R` + buffer drive coax; keep `OUT` traces short and
   reference them to ground (controlled impedance only if trace length warrants).
5. **Ground plane** continuous under the analog chain for low-noise return.

---

## Mechanical (D5 — rack-mounted, two boards per box)

- The board is **rack-mounted**, with **two 12-channel boards side-by-side** in one
  enclosure (user is sourcing a box sized for 2). Design each board to **≈ half the usable
  rack interior width** (19" rack ≈ 444 mm usable → budget **≈ 200–215 mm per board** after
  side margins, the inter-board gap, and card guides). **Confirm the exact internal width,
  depth, and mounting from the chosen box before fixing the outline.**
- **Put all 36 MCX on one edge** (the rack front panel) so cabling exits the front; the
  power connector goes on the opposite/rear edge. 36 front-edge MCX is the dominant
  placement constraint — expect to stack them in 2–3 rows or group by channel.
- Provide **M3 mounting holes / card-guide edges** compatible with the box's rails.
- This drives Track 4 (mechanical) and constrains Track 6 (layout).

> Board dimensions, exact jack placement, and the outline are defined in the KiCad PCB
> once implemented; this document is design intent, the PCB file is authoritative
> (same convention as `ets-breakout`).

---

## Bill of optional configurations (board build variants)

A given board is assembled in one configuration; the common ones:

| Build | Bias filter | CR-210 | Use case |
|---|---|---|---|
| **Full** | fitted | fitted | On-board bias + high-rate spectroscopy |
| **No-BLR** | fitted | bypassed | On-board bias, low rate / minimal latency |
| **External-bias** | bypassed | (either) | Clean external bias supply / external bias-tee |
| **Reference-equivalent** | bypassed | bypassed | Behaves like the original 6-ch board (×12) |

See the DNP tables in [bom.md](bom.md) for the exact populate/DNP set per variant.
