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
| CR-11X CSP (CR-110/-111/-112/-113) | `reference/cremat-CR-150-R5` (`CR-150-R5-cache.lib`) | symbol + BOM (footprint = stock `PinSocket_1x08`, see below) |
| CR-200-X shaper | `reference/cremat-CR-160-R7` (`CR-160-R7-cache.lib`) | symbol (footprint = stock `PinSocket_1x08`, see below) |
| **CR-210 BLR** | `reference/cremat-CR-160-R7` (`CR-160-R7-cache.lib`) | symbol (pinout confirmed); footprint = stock `PinSocket_1x08` |
| Output buffer — **TI THS3491** (CFA) | *not from the Cremat refs* (replaces EL5163/EL5167) | new symbol + SOIC-8/PowerPAD footprint — see *New parts to add* |

The `reference/cremat-x6-board/` project also has these (as KiCad "rescue" symbols), plus
the passive/jumper/connector symbols below — fine to reuse, but re-home them into a clean
project lib and drop the rescue/absolute paths.

| Symbol (x6-board lib) | Part | Carried forward |
|---|---|---|
| `CR-11X` (`CR-150-R5-rescue`) | Cremat CR-110/-111/-112/-113 CSP (SIP-8) | yes |
| `CR-200` (`CR-160-R7-rescue`) | Cremat CR-200-X shaper (SIP-8) | yes |
| `EL5163`/`EL5167` | old output buffer — **replaced by TI THS3491** (new part, below) | no |
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
- **Footprint (module sites are *socketed*):** the CR-112, CR-200, and CR-210 all **plug into
  SIP-8 sockets and are never soldered.** Use the stock KiCad **`PinSocket_1x08_P2.54mm_Vertical`**
  footprint (0.1" pitch) populated with a **Samtec SS-108-TT-2** SIP-8 socket (alt Harwin
  D01-9970842) — **36 per board** (3 module sites × 12). One socket footprint serves all three
  module types. (The reference boards' `8pinSIP` / `PinHeader_1x08` footprints described
  *soldered* modules and are **not** used here.)

### Output buffer — TI THS3491 (NEW — replaces the EL5163/EL5167)
- **Symbol:** the buffer is now a **TI THS3491** current-feedback line driver — **not** the
  EL5163/EL5167/LM7321 the reference boards carried (that part could not run on the ±12 V
  rails). Use a KiCad standard op-amp/CFA symbol or a TI-provided symbol; verify pin mapping
  against the THS3491 datasheet.
- **Footprint:** **8-pin SOIC with PowerPAD** thermal pad (DK `296-49085-1-ND`, cut tape).
- **Populate option:** DNP by default with a 0R bypass link (see [bom.md](bom.md) /
  [channel.md](channel.md)).

### 0R bypass jumpers (0805)
- Use a standard **`R_0805_2012Metric`** footprint stuffed with a 0R link for
  `JP_Rf1`,`JP_Rf2`,`JP_BLR`, **or** a 2-pad solder-jumper footprint for the tightest
  spots. Symbol: a resistor (0R) or `SolderJumper_2`.

### 0805 passive footprints
- Standardize R/C on `R_0805_2012Metric` / `C_0805_2012Metric`. For the HV parts (`Cc`,
  `Cf`) use the same 0805 footprint but a voltage-rated MLCC part number in the BOM.

### Connectors
- One MCX part serves all **four** per-channel I/O jacks (`BIAS_IN`, `SIPM`, `TEST`, `OUT`)
  — **48 per board** (4 × 12): **TE Connectivity Linx `CONMCX013`** (DK `343-CONMCX013-ND`),
  50 Ω female board-edge SMT. Import a
  datasheet-verified footprint + 3D model (verify the edge cutout against the TE drawing),
  as `ets-breakout` did for its coax jacks. No separate HV connector — `BIAS_IN` uses the
  same MCX.

---

## Library files to create

```
hardware/
  lib/
    cremat.kicad_sym         CR-11X, CR-200, CR-210 symbols (re-homed) + THS3491 buffer
    cremat.pretty/           MCX coax jack + 0R jumper footprints (SIP-8 module sites use the
                             stock KiCad PinSocket_1x08 footprint, not a project-local one)
  fp-lib-table               registers cremat.pretty via ${KIPRJMOD}
  sym-lib-table              registers cremat.kicad_sym via ${KIPRJMOD}
```

Verify each footprint against the part drawing before routing — datasheet-verified
footprints are an iron rule inherited from both reference projects.
