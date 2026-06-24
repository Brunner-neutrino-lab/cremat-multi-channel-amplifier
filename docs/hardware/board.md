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
| `BIAS_IN` (HV) | dedicated HV connector (e.g. SHV / isolated) | Single rail fanned to all 12 bias filters; widened creepage, no plane crossing under it |

- Decoupling values follow the reference (per-rail 0.1 µF / 1 µF / 10 µF near modules),
  resized to 0805 where the voltage rating allows.
- Keep the **bias rail away from the ground plane edges** and honor HV creepage
  ([pcb-design-rules.md](pcb-design-rules.md)).

---

## Connectors

| Connector | Qty | Purpose | Candidate part |
|---|---|---|---|
| `SIPM` (per channel) | 12 | Coax to each detector (DC bias + signal) | MCX / SMA edge jack (match reference `Conn_Coaxial`) |
| `OUT` (per channel) | 12 | 50 Ω shaped output to DAQ | MCX / SMA edge jack |
| `BIAS_IN` | 1 | HV detector bias in | SHV or isolated HV connector |
| Power (±Vs, GND) | 1 | Analog supply | Screw terminal / locking header |

- The reference uses generic `Conn_Coaxial` symbols for in/out; pick the physical jack
  (MCX vs SMA) to match the lab's cabling, as `ets-breakout` did (it offered MCX/SMA/U.FL
  variants). 24 coax jacks (12 `SIPM` + 12 `OUT`) drive the board outline.
- Group each channel's `SIPM` and `OUT` near its cell to keep the bias node and the
  output trace short.

---

## Layout intent

1. **Channel pitch = module height.** The Cremat SIP-8 modules stand vertically; lay the
   12 cells out on a regular pitch so the modules form neat rows (as on the reference
   board) and the coax jacks line the edges.
2. **Front-end node is the sensitive node.** Keep `BIAS_IN→filter→node→Cc→CSP` compact;
   minimize the high-impedance amplifier-input copper. Consider a guard around it
   (the reference and `ets-breakout` both guard sensitive analog nodes).
3. **Bias rail isolation.** Route `BIAS_IN` and the per-channel filtered bias as an HV
   net class with extra clearance; do not run signal traces under it.
4. **Output side is 50 Ω.** The `49.9R` + buffer drive coax; keep `OUT` traces short and
   reference them to ground (controlled impedance only if trace length warrants).
5. **Ground plane** continuous under the analog chain for low-noise return.

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
