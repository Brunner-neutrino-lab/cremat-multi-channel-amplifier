# Component Libraries

Symbols and footprints the hardware track needs to provide. Keep project-local, datasheet-
verified libraries (the `ets-breakout` / reference-board convention), referenced with
`${KIPRJMOD}` so the project is portable.

---

## Canonical sources (reuse, don't redraw)

Four reference submodules carry verified symbols/footprints for the parts we keep. Prefer
the **upstream Cremat eval boards** (clean, authoritative) over the x6-board's rescue libs:

| Part | Canonical source | Asset to copy |
|---|---|---|
| CR-11X CSP (CR-110/-111/-112/-113) | `reference/cremat-CR-150-R5` (`CR-150-R5-cache.lib`) | symbol + 8-pin SIP footprint + BOM |
| CR-200-X shaper | `reference/cremat-CR-160-R7` (`CR-160-R7-cache.lib`) | symbol + `Cremat_footprints:8pinSIP` |
| **CR-210 BLR** | `reference/cremat-CR-160-R7` (`CR-160-R7-cache.lib`) | symbol (pinout confirmed) + `8pinSIP` |
| EL5163/EL5167 buffer | `reference/cremat-CR-160-R7`, `reference/cremat-x6-board` | symbol |

The `reference/cremat-x6-board/` project also has these (as KiCad "rescue" symbols), plus
the passive/jumper/connector symbols below — fine to reuse, but re-home them into a clean
project lib and drop the rescue/absolute paths.

| Symbol (x6-board lib) | Part | Carried forward |
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

### Cremat CR-210 baseline restorer (NEW — symbol available, pinout confirmed)
- **Symbol:** copy the `CR-210` symbol straight from `reference/cremat-CR-160-R7`
  (`CR-160-R7-cache.lib`). Confirmed pinout `1=input, 2=GND, 3=GND, 4=-Vs, 5=+Vs, 6=GND,
  7=GND, 8=output` — identical to the CR-200 except pin 2 (P/Z → GND), so don't reuse the
  CR-200 symbol as-is.
- **Footprint:** the same `Cremat_footprints:8pinSIP` used by the CR-200 on that board
  (0.1" pitch, pin 1 marked). One footprint serves CR-11X, CR-200, and CR-210.

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
