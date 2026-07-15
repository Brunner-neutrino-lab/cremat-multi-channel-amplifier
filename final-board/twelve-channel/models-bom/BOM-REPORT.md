# BOM report — twelve-channel

`twelve-channel-bom.csv` is generated from the board netlist + board by `gen_bom.py` (groups
the 500 placed parts by MPN/value/DNP into purchasing line items, enriches each from the
single-channel BOM by MPN; up-rated common-power parts from the sourcing verification).

Regenerate: `"C:/Program Files/KiCad/10.0/bin/python.exe" gen_bom.py` (after any schematic/PCB
change + `sch export netlist`).

## Summary

- **500 parts**, **24 line items** — **380 FIT** (default variant) + **120 DNP**. (The FIT count
  now includes the 36 socketed-Cremat SIP-8 sockets, Samtec `SS-108-TT-2`.)
- Default variant ≈ **$273** in passives/connectors/protection/sockets (incl. the 36 SIP-8
  sockets) **+ the 3 Cremat modules** (CR-112 $55, CR-200 $55, CR-210 $77 each × 12 =
  **$2,244**) ≈ **$2,517/board** (ex-case; matches `PURCHASING.md`). The Cremat
  SIP modules dominate cost and lead time — order early (made-to-order).

## Variants (populate options, per the single-channel scheme, × 12 channels)

- **Default**: CR-210 fitted, buffer **bypassed** (`JP_BUF` 0R fitted; THS3491 block DNP), bias
  filter fitted. → the 120 DNP parts are the buffer block (U_BUF/R_FB/R_GAIN + BVP/BVN decoupling
  ×12) and the bias/BLR bypass jumpers (JP_Rf1/JP_Rf2/JP_BLR ×12).
- **+2 gain buffer**: populate the THS3491 block (976 Rf/Rg, 4.7/10 µF BVP/BVN) and remove
  `JP_BUF` — per channel, all together. Raises per-channel +rail current to 48.7 mA (12× = 584 mA;
  still within the 1.1 A PTC).
- **CR-210 bypass / bias-filter bypass**: the respective 0R jumpers per the single-channel DNP tables.

## Changes vs 12× the single channel

| Part | Single channel | Twelve channel |
|---|---|---|
| PTC `F_P/F_N` | 0.1 A `1206L010/60WR` | **1.1 A `1812L110/24DR`** (Littelfuse) |
| Schottky `D_RP/D_RN` | `SS14` (SMA) | **`SSA24`** (onsemi, 2 A SMA) |
| Bulk `C_BULKP/C_BULKN` | 100 µF `UWT1V101MCL1GS` | **470 µF `EEE-FN1V471UP`** (Panasonic) |
| Power connector | `J_PWR` ×1 | `J_PWR` + **`J_DAISY`** (1715734 ×2) |

See `SOURCING-VERIFICATION-2026-07-08.md` for the verification (all 3 provisional up-rated MPNs
were rejected — obsolete / wrong package / fictional — and replaced with in-stock parts).
