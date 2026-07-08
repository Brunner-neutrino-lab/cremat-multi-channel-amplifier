# Sourcing verification — 12-channel common-power protection (2026-07-08)

Verified the up-rated common-power parts for the 12-channel board (the per-channel parts are
unchanged from the single-channel BOM). **All three provisional picks were rejected** and
replaced with confirmed in-stock parts. Footprints are unchanged, so the PCB layout was not
affected (DRC stayed 0/0/0).

## Why up-rate — current budget

From `sim/scripts/rail_budget.py` (datasheet quiescent, per rail): CR-112 8 mA, CR-200 7 mA,
CR-210 17 mA (+) / 13 mA (−), THS3491 16.7 mA. Per channel: **+rail 32 mA** (default, buffers
DNP) → **48.7 mA** (all buffers). Per board (12 ch): **+rail 384 mA (default) → 584 mA (all
buffered)**; −rail 336–536 mA. The +rail is heaviest (CR-210 asymmetric). One supply feeds
board 1, which daisies raw power to a stacked 2nd board, so **board 1's input connector/trace
carries ~0.8–1.2 A** (both boards) — but **each board's own PTC/Schottky see only its ~0.4–0.6 A**
(the protection is per-board, downstream of the daisy tap). The single channel's 0.1 A PTC would
nuisance-trip instantly at 12× current → up-rate the PTC (and, for margin, the Schottky + bulk).

## Parts

### PTC fuse `F_P` / `F_N` (×2)
- **Provisional `MF-MSMF110-2` (Bourns) — REJECTED.** Obsolete at DigiKey ("no longer
  manufactured"); and the bare `-2` suffix in the MF-MSMF family is the **6 V** variant — far
  below the ≥16 V a ±12 V rail needs.
- **Verified → Littelfuse `1812L110/24DR`** (DK **F5632CT-ND**). I_hold **1.1 A** (23 °C),
  I_trip 1.95 A, **V_max 24 V**, R_init 60 mΩ. Active, ~1.5k in stock, $0.78/1. Package **1812**
  = `Fuse:Fuse_1812_4532Metric`.
- **Sizing:** hold 1.1 A vs 0.584 A worst-case = **~1.9× margin** (no nuisance trip); trip
  1.95 A clears a hard fault; 24 V > the ±12 V rail with real reverse/transient-fault margin.
  Hold derates to ~0.9 A near 50 °C — still ≫ 0.6 A. (For the full 30 V preference a larger part
  exists, but 24 V is the best current, in-stock 1.1 A/1812 compromise.)

### Schottky `D_RP` / `D_RN` (×2)
- **Provisional `SS24` — REJECTED (footprint mismatch).** SS24 is **SMB / DO-214AA**, not SMA —
  it would not drop into `Diode_SMD:D_SMA`; onsemi's SS24 is also obsolete.
- **Verified → onsemi `SSA24`** (DK **SSA24CT-ND**). The **SMA** member of the same 40 V/2 A
  family (`SSA` prefix = SMA/DO-214AC). V_RRM 40 V, I_F(av) 2 A, V_F 500 mV max @ 2 A, AEC-Q101.
  Active, ~16k in stock, $0.84/1. Fits `Diode_SMD:D_SMA`.
- **Sizing:** 2 A ≫ ~0.5 A per-diode current (each diode carries one rail) → ~3–4× thermal
  margin; V_F ~0.35–0.4 V @ 0.5 A (~0.2 W); Vr 40 V vs ~24 V worst-case reverse. Series
  reverse-block: cathode→+VDC (D_RP), anode→−VDC (D_RN).

### Bulk electrolytic `C_BULKP` / `C_BULKN` (×2)
- **Provisional `UWT1V471MNL1GS` (Nichicon) — REJECTED (does not exist).** The Nichicon UWT
  35 V rank tops out at 47 µF; 470 µF is only offered at 25 V (`UWT1E471…`). The provisional
  MPN is the 25 V part with the voltage code wrongly swapped 1E→1V.
- **Verified → Panasonic `EEE-FN1V471UP`** (DK **10-EEE-FN1V471UPCT-ND**). 470 µF, **35 V**,
  ESR 80 mΩ, ripple 850 mA, Ø **10.0 × 10.5 mm** — exact match for
  `Capacitor_SMD:CP_Elec_10x10.5`. Active, ~2.8k in stock, $1.17/1.
- **Sizing:** 35 V ≈ 3× margin on ±12 V (matches the single channel's 100 µF/35 V choice);
  backs the 12× distributed 10 µF local decoupling.

## Result

`twelve-channel-bom.csv` regenerated: 23 line items, 464 parts (344 FIT + 120 DNP), all with
verified metadata. The 3 up-rated parts + the added `J_DAISY` (2nd Phoenix 1715734) are the only
BOM changes vs 12× the single-channel line; every per-channel part is carried through unchanged.
