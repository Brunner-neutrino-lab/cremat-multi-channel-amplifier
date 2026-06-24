# Component Libraries

Symbols and footprints the hardware track needs to provide. Keep project-local, datasheet-
verified libraries (the `ets-breakout` / reference-board convention), referenced with
`${KIPRJMOD}` so the project is portable.

---

## Reuse from the reference board

The reference project (`reference/cremat-x6-board/`) already contains verified symbols for
the parts carried forward. Copy these into the new project's library rather than
re-drawing:

| Symbol (reference lib) | Part | Carried forward |
|---|---|---|
| `CR-11X` (`CR-150-R5-rescue`) | Cremat CR-110/-111/-112/-113 CSP (SIP-8) | yes |
| `CR-200` (`CR-160-R7-rescue`) | Cremat CR-200-X shaper (SIP-8) | yes |
| `EL5163`/`EL5167` | output buffer (CFA) | yes |
| `Device:R_US`, `Device:C`, `Device:L` | passives | yes (footprints → 0805) |
| `Device:R_Potentiometer_Trim_US` | trimpots | yes |
| `Jumper:SolderJumper_2_Bridged`, `Jumper_2_Open`, `Jumper_3_Open` | jumpers | yes (for 0R bypass) |
| `Connector:Conn_Coaxial` | `SIPM` / `OUT` jacks | yes |
| `power:+VDC`, `power:-VDC`, `power:GND` | rails | yes |

> The reference symbols come from KiCad "rescue" libs with embedded definitions — they
> open fine, but re-home them into a clean project lib (`lib/cremat.kicad_sym`) and drop
> the absolute-path rescue references, the cleanup `ets-breakout` documents for its own
> rescue lib.

---

## New parts to add

### Cremat CR-210 baseline restorer (NEW)
- **Symbol:** 8-pin SIP. Easiest path — duplicate the `CR-200` symbol and re-label per the
  **`CR-210-R0` spec sheet**. ⚠️ The pin functions differ from the CR-200; do not ship the
  CR-200 map. Confirm `input` / `output` / `+Vs` / `-Vs` / `GND` from the datasheet
  (tracked in [session-report.md](../session-report.md)).
- **Footprint:** 8-pin SIP, 0.1" (2.54 mm) pitch — the **same physical footprint** as the
  CR-11X / CR-200 modules already on the board. Reuse that `.kicad_mod` (pin 1 marked).

### 0R bypass jumpers (0805)
- Use a standard **`R_0805_2012Metric`** footprint stuffed with a 0R link for
  `JP_Rf1`,`JP_Rf2`,`JP_BLR`, **or** a 2-pad solder-jumper footprint for the tightest
  spots. Symbol: a resistor (0R) or `SolderJumper_2`.

### 0805 passive footprints
- Standardize R/C on `R_0805_2012Metric` / `C_0805_2012Metric`. For the HV parts (`Cc`,
  `Cf`) use the same 0805 footprint but a voltage-rated MLCC part number in the BOM.

### Connectors
- Pick the physical coax jack (MCX or SMA) and import a datasheet-verified footprint, as
  `ets-breakout` did (it kept MCX/SMA/U.FL footprints, each checked against the maker's
  drawing). Add an SHV/HV footprint for `BIAS_IN`.

---

## Library files to create

```
hardware/
  lib/
    cremat.kicad_sym         CR-11X, CR-200, CR-210, buffer symbols (re-homed)
    cremat.pretty/           SIP-8 module footprint, coax jacks, HV connector, 0R jumper
  fp-lib-table               registers cremat.pretty via ${KIPRJMOD}
  sym-lib-table              registers cremat.kicad_sym via ${KIPRJMOD}
```

Verify each footprint against the part drawing before routing — datasheet-verified
footprints are an iron rule inherited from both reference projects.
