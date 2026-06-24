# Modifications vs. `cremat-x6-board`

This is the **authoritative change list**. Everything else in `docs/` elaborates on these
four points. The baseline is the Brunner-lab 6-channel board at
[`reference/cremat-x6-board/`](../reference/cremat-x6-board/) — specifically the
per-channel circuit in
[`channel.kicad_sch`](../reference/cremat-x6-board/channel.kicad_sch), instantiated 6×.

Reference per-channel circuit (what we start from):

```
coax IN ─► Cc ─► CR-113 (CSP) ─► CR-200-X (shaper, P/Z trim) ─► EL5167/LM7321 buffer ─► 49.9R ─► coax OUT
```

---

## Change 1 — 12 channels (was 6)

- Instantiate the channel cell **12 times** instead of 6.
- Power entry + bulk decoupling (the shared `±Vs`/`GND`) scale to 12 channels; bias is
  per-channel (no shared rail — see Change 4).
- Mechanical: ~2× the channel area; the outline is sized for **two boards side-by-side in
  a rack box** and must fit **36 MCX jacks** (12× `BIAS_IN` + `SIPM` + `OUT`) plus the
  ±Vs/GND entry. See [hardware/board.md](hardware/board.md).

**Rationale:** denser detector coverage per board; same per-channel electronics.

---

## Change 2 — 0805 passives wherever possible

- All discrete **R and C default to 0805** (1.27 mm) imperial.
- The **0R bypass jumpers** are 0805 `0R` (an 0805 resistor footprint stuffed with a
  zero-ohm link). Solder-jumper footprints remain an option for the smallest bypasses.
- **Not 0805** (physically can't be), keep as-is:
  - Cremat modules **CR-11X / CR-200-X / CR-210** — 8-pin SIP through-hole, 0.1" pitch.
  - Op-amps **EL5167** (SOT-23-5) / **LM7321** (SOT-23-5 / SO-8).
  - Trimpots (`RV*`), coax jacks (`SIPM`, `OUT`), power entry.
- Watch voltage rating when forcing 0805: the AC-coupling cap `Cc` and the bias-filter
  parts see the full SiPM bias — keep them in an 0805 part **rated ≥ the bias voltage**
  (the reference `Cc` is `0.22 µF 100 V X5R`). See [hardware/bom.md](hardware/bom.md).

**Rationale:** smaller, cheaper, machine-placeable; consistent BOM. The reference board
mixed sizes; standardizing on 0805 keeps assembly simple while staying hand-reworkable.

---

## Change 3 — Cremat CR-210 baseline restorer per channel (optional)

Insert a **CR-210 baseline restorer** between the CR-200-X shaper output and the output
buffer, on every channel. The CR-210 corrects baseline depression at medium/high count
rates and preserves the Gaussian shape; it is designed to follow any Cremat shaper.

This mirrors Cremat's own open-source eval board
[`reference/cremat-CR-160-R7`](../reference/cremat-CR-160-R7/), which carries the CR-200
(`U4`) and the **optional** CR-210 (`U5`) with a bypass jumper (`JU1`) across the module.

**Optional via 0R bypass** — `JU1` becomes our 0805 `JP_BLR`; exactly one is populated:

```
 CR-200 out ──┬──► CR-210 in (U5.1)      CR-210 out (U5.8) ──┬──► buffer in
   (U4.8)     │                                              │
              └──────────── JP_BLR (0R, was JU1) ────────────┘   across the module
```

| Variant | CR-210 (`U_BLR`) | `JP_BLR` 0R | Signal path |
|---|---|---|---|
| **BLR fitted** | populate | **open / DNP** | shaper → CR-210 → buffer |
| **BLR bypassed** | DNP | **close / 0R** | shaper → buffer (identical to reference) |

- **CR-210 pinout — confirmed from `cremat-CR-160-R7` (footprint `8pinSIP`).** Identical to
  the CR-200 *except pin 2*:

  | Pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
  |---|---|---|---|---|---|---|---|---|
  | **CR-210** | input | **GND** | GND | -Vs | +Vs | GND | GND | output |
  | CR-200 | input | P/Z | GND | -Vs | +Vs | GND | GND | output |

  Reuse the existing CR-200 SIP-8 footprint; the symbol/footprint live in the reference
  board's `CR-160-R7-cache.lib` ([hardware/component-libraries.md](hardware/component-libraries.md)).
- The CR-210 shares the `+VDC`/`-VDC`/`GND` rails and gets its own decoupling, like the
  other modules.

**Rationale:** lets the same board serve high-rate spectroscopy (BLR fitted) and
low-rate / minimal-latency use (bypassed) without a layout change.

---

## Change 4 — On-board SiPM bias front-end per channel (optional filter)

This is the largest topology change. The reference board had **one coax input** carrying
an already-biased signal. This board adds, **per channel**, its own **`BIAS_IN` jack and
`SIPM` jack** (both MCX `CONMCX013`, alongside the channel's `OUT` jack → 3 MCX/channel),
with an optional bias filter, arranged so the detector and the amplifier share one biased
node. **`BIAS_IN` is per-channel — there is no shared on-board bias rail** (bias ≤ 60 V):

```
                          bias filter (optional, 0R-bypassable)
 BIAS_IN ───►  Rf1 ──┬── Rf2 ──►──┐
                     │            │   FRONT-END NODE
                    Cf            ├──────────────────► SIPM   (DC-coupled)
                     │            │
                    GND           └─► Cc ─► CR-11X ...  (AC-coupled)
```

### Required routing
- **`BIAS_IN` → bias filter → front-end node.** The filter is **"RC in series with R"**:
  series `Rf1`, shunt `Cf` to GND, series `Rf2`.
- **Front-end node → `SIPM` connector: DC-coupled** (direct copper). The filtered bias
  reverse-biases the detector.
- **Front-end node → `Cc` → amplifier input: AC-coupled.** `Cc` blocks the DC bias and
  passes the SiPM current pulse into the CR-11X preamp.
- The SiPM and the amplifier are therefore **in parallel** on the front-end node, as is
  the (filtered) bias feed.

### Optional via 0R bypass — bias filter
Exactly one of these per build:

| Variant | `Rf1`,`Rf2` | `Cf` | `JP_Rf1`,`JP_Rf2` 0R | Result |
|---|---|---|---|---|
| **Filter fitted** | populate (filter R values) | populate | DNP | `BIAS_IN` low-pass filtered to the node |
| **Filter bypassed** | DNP | DNP | populate | `BIAS_IN` straight to the node (no filtering) |

> A 0R link sits across each series resistor (`Rf1`,`Rf2`); the shunt `Cf` is simply DNP
> when bypassed. This keeps the bypass a pure copper short and avoids a stranded RC.

### HV implications (do not skip)
- `BIAS_IN`, the filter nodes, the front-end node, the `SIPM` net, and `Cc` all sit at
  the **full SiPM bias voltage**. Use voltage-rated parts and HV creepage/clearance on
  these nets — see [hardware/pcb-design-rules.md](hardware/pcb-design-rules.md).
- `Cc` must be **rated ≥ bias voltage** (reference: 100 V). It is the single part that
  isolates the (grounded-referenced) amplifier from the HV node.

**Rationale:** one cable per detector, the filter sits at the detector node where it
suppresses bias-supply noise best, and the AC/DC split is the standard SiPM readout
topology. Making the filter optional lets a clean external bias supply skip it.

---

## Summary table

| # | Change | Optional? | Mechanism | Primary docs |
|---|---|---|---|---|
| 1 | 6 → 12 channels | no | instantiate cell 12× | [board.md](hardware/board.md) |
| 2 | 0805 passives | no | footprint choice (modules/op-amps excepted) | [bom.md](hardware/bom.md) |
| 3 | CR-210 BLR per channel | **yes** | `JP_BLR` 0R bypass / DNP | [channel.md](hardware/channel.md), [bom.md](hardware/bom.md) |
| 4 | SiPM bias front-end + filter | **filter yes** | RC+R filter, `JP_Rf*` 0R bypass; SiPM DC / amp AC | [channel.md](hardware/channel.md), [pcb-design-rules.md](hardware/pcb-design-rules.md) |
