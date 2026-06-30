# Twelve-channel final-board Models-BOM — Track C2 (`board-bom`)

The **final fabricable BOM** for the 12-channel SiPM CSP + shaper + BLR + buffer board:
the **COMPLETE single-channel BOM scaled ×12** plus the **board-level shared parts** (one
shared power-entry terminal, central bulk electrolytics, mounting hardware). Every line is a
real, in-stock, economical Digi-Key part with full provenance. This is the **source of truth
for the board-level shared parts** — C1 must place exactly these so Models-BOM == Design BOM.

- Machine-readable BOM: [`twelve-channel-bom.csv`](twelve-channel-bom.csv)
  (20 fields/line; `Scope` = `PER-CHANNEL` / `BOARD-SHARED`; `Board_Qty_CR210pop` is the
  fitted count on the default Full board).
- Scaled from (COMPLETE + committed): `integration/single-channel/models-bom/single-channel-bom.csv`
  (48 refs, 19 distinct MPNs, THS3491 buffer @ Rf=Rg=976 Ω).

---

## 0. Success / failure criteria (stated before the work)

| # | Criterion | Result |
|---|---|---|
| S1 | Per-channel parts are an **exact ×12** of the COMPLETE single-channel BOM (same MPNs, ×12 qty) | ✅ all 47 per-channel ref-lines copied 1:1, qty×12 (single-channel's 48 − the one `J_PWR` lifted to BOARD-SHARED); central bulk *added* on top (see §2) |
| S2 | **Board-level shared parts added** & sourced: main power terminal sized for 12× current, board bulk electrolytics, M3 mounting hardware | ✅ §3 — J_PWR (17.5 A Phoenix, ample), 2× central 470 µF, 4× M3 standoff + 8× screw, 4× M3 hole feature |
| S3 | Every line real / in-stock / economical on Digi-Key with full fields | ✅ all Digi-Key lines in stock & priced (§3, §4); only Cremat modules are direct-order (expected) |
| S4 | **DNP build-variant table** (Full vs bias-bypass vs CR-210-bypass) | ✅ §5 |
| S5 | **Per-line + total board cost** at qty 1 and a small production qty (25), with ×12 price-break tiering | ✅ §4 |
| S6 | Long-lead items flagged (36 Cremat modules ×12) | ✅ §6 |
| S7 | Board-shared parts published unambiguously for C1 to match | ✅ §3 (the "C1 must place" table) |
| **FAIL flags** | unsourced / out-of-stock line, or BOM ≠ board | **None.** All Digi-Key parts in stock; per-channel set == single-channel BOM. One carryover disclosure (EL5167→THS3491) already resolved in Phase B. |

---

## 1. The scaling model (how single-channel → twelve-channel)

The single-channel BOM has **48 ref lines / 19 distinct MPNs**. Three of those lines are
**board-level** in character, not per-channel-cell:

| Single-channel ref | Single-ch role | In the ×12 board |
|---|---|---|
| `J_PWR` (Phoenix 1715734) | the board's ±12 V/GND screw terminal | **NOT ×12** — becomes the **one shared** `J_PWR` (BOARD-SHARED). One power entry feeds all 12 channels. |
| `Cbulk_P` / `Cbulk_N` (100 µF SMD) | "board bulk electrolytic (rail entry)" | **Kept ×12** as **per-channel distributed bulk** (one pair per channel row) **and** a **new central 470 µF pair** (`CBULK_P/N`, BOARD-SHARED) added at the single power entry. The single-ch board only needed entry bulk for one cell; 12 cells fed from one terminal need both distributed *and* central reservoir. |

Everything else (the 45 remaining ref-types: modules, buffer, passives, jumpers, trimpot,
MCX jacks, test path) is a **true ×12 copy** — identical MPN, qty × 12, same footprint,
same DNP rule. The per-channel cell is **frozen from Phase B** (the brief: "the single-channel
design is frozen — Phase C composes and routes it").

> **Reconciliation note (carried from Phase B §2c):** per-channel bulk = Nichicon
> **UWT1V101MCL1GS** (SMD, 35 V); power terminal = Phoenix **1715734** (5.08 mm). C1 uses
> these reconciled PNs. The new central bulk (`CBULK_P/N`) is radial THT (taller part is fine
> within the 1U / ~35 mm height budget at the board edge).

**Ref-designator scheme for C1:** suffix each per-channel ref with its channel number,
e.g. `U_CSP1..U_CSP12`, `Rfb1..Rfb12`, `J_OUT1..J_OUT12`. Board-shared refs are unsuffixed
(`J_PWR`, `CBULK_P`, `CBULK_N`, `MH1..MH4`).

---

## 2. Per-channel parts = exact ×12 of the single-channel BOM (S1)

**47 per-channel ref-lines**, each ×12 (the single-channel BOM's 48 lines **minus** the one
board-level `J_PWR` line lifted to §3 = 47). Confirmed identical to
`integration/single-channel/models-bom/single-channel-bom.csv` (same Value / MPN / Manufacturer /
DK-PN / footprint / DNP). `Cbulk_P`/`Cbulk_N` stay ×12 (distributed bulk); §3 *adds* the
central pair on top.

| Block | Per-channel ref-types (×12 each) | Distinct MPNs |
|---|---|---|
| CSP + bias front-end | U_CSP, Rf1, Rf2, Cf, Cc, JP_Rf1, JP_Rf2, Rdec_P, Rdec_N, Cdec_P01, Cdec_N01, Cdec_P10, Cdec_N10, Cbulk_P, J_BIAS, J_SIPM, J_TEST, Ctest, R_test | CR-112, 10k, 100nF/100V, 0.22µF/100V, 0R, 4.7Ω, 0.1µF, 10µF, 100µF, CONMCX013, 1pF C0G, 47Ω |
| SHAPER | U_SHAPER, R_PZ, Rdp1, Rdn1, Cbp1, Cbn1, Clp1, Cln1 | CR-200, 200k trim, (shared 4.7/0.1µF/10µF) |
| BLR | U_BLR, JP_BLR, Rdp2, Rdn2, Cbp2, Cbn2, Clp2, Cln2 | CR-210, (shared 0R/4.7/0.1µF/10µF) |
| BUFFER | U_BUF, Rfb, Rgain, R_OUT, Rdp3, Rdn3, Cbp3, Cbn3, Clp3, Cln3, J_OUT, Cbulk_N | THS3491, 976Ω, 49.9Ω, (shared 4.7/0.1µF/10µF/100µF/CONMCX013) |

The shared-jellybean dedupe from Phase B holds at ×12 — e.g. the 4.7 Ω rail R
(`RC0805JR-074R7L`) was 8/channel → **96/board**; 0.1 µF (`CL21B104KBCNNNC`) 8/channel →
**96/board**; 10 µF (`CL21A106KAYNNNE`) 8/channel → **96/board**; CONMCX013 = 4/channel
(3 fitted + J_TEST DNP) → **36 fitted / 48 if all test jacks populated**. These large
quantities are what move the qty-25 price-break tier (§4).

---

## 3. Board-level shared parts — **C1 must place exactly these** (S2, S7)

Single source of truth for the shared section. Refs are **unsuffixed** (one per board).

| Ref | Qty/board | Value | MPN | Mfr | Digi-Key PN | $ q1 | Footprint | Notes |
|---|---|---|---|---|---|---|---|---|
| **J_PWR** | 1 | 3-pos screw term 5.08 mm | **1715734** (MKDS 1,5/3-5,08) | Phoenix Contact | **277-1264-ND** | 1.97 | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal` | **17.5 A / 400 V** — see current budget below; same PN as single-ch J_PWR but now **shared ×1** |
| **CBULK_P** | 1 | 470 µF 35 V | **UVR1V471MPD** | Nichicon | **493-1084-ND** | 0.51 | `Capacitor_THT:CP_Radial_D10.0mm_P5.00mm` | central +12 V reservoir at entry (radial THT, D10×16 mm, LS 5 mm); 4512 in stk |
| **CBULK_N** | 1 | 470 µF 35 V | **UVR1V471MPD** | Nichicon | **493-1084-ND** | 0.51 | `Capacitor_THT:CP_Radial_D10.0mm_P5.00mm` | central −12 V reservoir at entry |
| **MH1..MH4** | 4 | M3 hole | (PCB feature) | — | — | 0.00 | `MountingHole:MountingHole_3.2mm_M3` | corner holes, ≥5 mm from edge, clear of jack courtyards (mechanical.md) |
| **HW_STDOFF** | 4 | M3 hex standoff ~11 mm Al | **24338** | Keystone Electronics | **36-24338-ND** | 0.83 | off-board | board→tray standoff (sets 5–10 mm height); not placed on PCB |
| **HW_SCREW** | 8 | M3×6 pan-head SS | **PMSSS 3-6 PH** | B&F Fastener | **H743-ND** | 0.10 | off-board | 4 board-side + 4 tray-side; not placed on PCB |

### Power-entry current budget (why J_PWR is comfortably sized for 12×)

Per-channel quiescent supply current from the module + buffer datasheets:

| Device | +V rail | −V rail | Source |
|---|---|---|---|
| CR-112 | 5.5 mA | 5.5 mA | CR-112 app guide (Vs=13 V) |
| CR-200-1µs | 7 mA | 7 mA | CR-200 app guide (quiescent) |
| CR-210 | 17 mA | 13 mA | CR-210-R0 spec (Vs=13 V) |
| THS3491 | ~16.8 mA | ~16.8 mA | TI datasheet (trimmed Iq 16.8 mA) |
| **per channel** | **≈46.3 mA** | **≈42.3 mA** | |
| **×12 (board, quiescent)** | **≈0.56 A** | **≈0.51 A** | |

The MKDS 1,5/3-5,08 is rated **17.5 A** — **~30× margin** over the ~0.56 A peak rail.
Transient THS3491 output current (12 line drivers, ≤~40 mA each into 100 Ω) adds dynamic
current but is sourced from the local + central bulk, not the terminal steady-state. **No
upsizing of the terminal is required**; the central 2× 470 µF reservoir handles the
transient demand. *(If a heavier connector is ever desired, the same Phoenix MKDS family in
a higher-current variant is a drop-in — but it is not needed.)*

---

## 4. Cost roll-up — per-board, qty 1 and qty 25 (S5)

Default build = **Full** (CR-210 populated, bias filter populated, test path DNP). The two
big movers at qty-25 are the **Cremat module breaks** (CR-112 $65→$59, CR-200 $59→$55,
CR-210 $77→$69) and the **THS3491 break** ($18.28→$13.60); the passives drop into their
100+/1000+ reel tiers (the ×12 board already buys 96 of each rail jellybean, so even a single
board sits near the production tier on passives).

| Variant | Fitted/ch | **1 board @ q1** | **1 board @ q25 break** | **25 boards** |
|---|---|---|---|---|
| **FULL** (CR-210 + bias filter populated, test DNP) | 41 | **$2,847.27** | **$2,517.63** | **$62,940.80** |
| **CR-210 BYPASSED** (U_BLR + CR-210 decoupling DNP, JP_BLR fitted) | 35 | **$1,915.83** | **$1,687.62** | **$42,190.40** |

Breakdown (FULL, 1 board @ q1): per-channel $236.68 ×12 = **$2,840.16** + board-shared
**$7.11** = **$2,847.27**. The **36 Cremat modules dominate at ~85%** ($2,412 of $2,847).
All Digi-Key passives + connectors + buffer ICs together ≈ $435/board; the board-shared
section is **$7.11** (terminal + 2 bulk caps + standoffs + screws).

> **Per-line costs** are in [`twelve-channel-bom.csv`](twelve-channel-bom.csv)
> (`Unit_Cost_USD_q1`, `Unit_Cost_USD_prod`, `Board_Qty_CR210pop`). Multiply unit × board-qty
> for each line; the totals above are the sums.

Bias-filter-bypass variant cost is **identical to its parent** (swap 3 fitted bias parts for
2 fitted 0R jumpers — a few cents); it changes population, not BOM total materially.

---

## 5. Build-variant DNP table (S4)

Each optional block is a **populate-or-bypass** pair (Iron rule #2 / Convention §6).
"FIT" = populated, "DNP" = do-not-populate. All entries are **per channel** (apply to all 12).

| Ref(s) (per channel) | **Full** (default) | **Bias-filter bypass** | **CR-210 bypass** | **Bench-test build** |
|---|---|---|---|---|
| `U_CSP` (CR-112) | FIT | FIT | FIT | FIT |
| `U_SHAPER` (CR-200) | FIT | FIT | FIT | FIT |
| **`U_BLR` (CR-210)** | **FIT** | FIT | **DNP** | FIT |
| **`JP_BLR` (0R)** | **DNP** | DNP | **FIT** | DNP |
| `Rdp2/Rdn2/Cbp2/Cbn2/Clp2/Cln2` (CR-210 decoupling) | FIT | FIT | **DNP** | FIT |
| `U_BUF` (THS3491) + `Rfb/Rgain/R_OUT` + buffer decoupling | FIT | FIT | FIT | FIT |
| **`Rf1/Rf2/Cf` (bias filter)** | **FIT** | **DNP** | FIT | FIT |
| **`JP_Rf1/JP_Rf2` (0R bypass)** | **DNP** | **FIT** | DNP | DNP |
| `R_PZ` (P/Z trim) | FIT | FIT | FIT | FIT |
| **`J_TEST/Ctest/R_test` (test path)** | **DNP** | DNP | DNP | **FIT** |
| Board-shared (J_PWR, CBULK_P/N, MH, HW) | FIT | FIT | FIT | FIT |

**Rules (enforced by C1 in ERC/DRC):**
- **CR-210:** `U_BLR` ⊕ `JP_BLR` — exactly one populated. When CR-210 DNP, its rail
  decoupling (Rdp2/Rdn2/Cbp2/Cbn2/Clp2/Cln2) is also DNP.
- **Bias filter:** `Rf1/Rf2/Cf` (populated) ⊕ `JP_Rf1/JP_Rf2` (populated) — populate-or-bypass.
- **Test path:** `J_TEST/Ctest/R_test` fitted only for a bench charge-injection build.
- **Buffer is always FIT** (mandatory output stage). Modules CR-112/CR-200 always FIT.
- A board may mix: e.g. Full signal chain + test jacks = "Bench-test build."

Fitted-per-board counts on the default **Full** board (test DNP): **41 per-channel lines/ch
× 12 = 492 placed per-channel parts + 15 board-shared pcs**. **36 MCX** fitted (J_TEST DNP);
48 if all test jacks are populated.

---

## 6. Long-lead callouts — order EARLY (S6)

**The three Cremat modules are made-to-order, not stocked** — they gate the schedule.

| Module | Per board | **×12 board** | $ each (q1 / q25) | Subtotal (12, q1 / q25) |
|---|---|---|---|---|
| CR-112-R2.1 | 12 | 12 | 65 / 59 | $780 / $708 |
| CR-200-1µs-R2.1 | 12 | 12 | 59 / 55 | $708 / $660 |
| CR-210-R0 | 12 | 12 | 77 / 69 | $924 / $828 |
| **Total (Full)** | **36** | **36 modules** | — | **$2,412 / $2,196** |

- **36 Cremat modules per Full board** (24 if CR-210 bypassed). For a 25-board production run
  that is **900 modules** (600 without CR-210) — **place the Cremat order first**, before the
  PCB fab/assembly slot, and confirm lead time with Cremat (US: cremat.com/ordering).
- Everything else ships from Digi-Key stock same-day (passives 100k–4 M, CONMCX013 >1000,
  THS3491 695, Nichicon/Phoenix/Bourns/Keystone in stock). **The buffer THS3491 (695 in stk)
  is NOT a lead-time risk** — but for a 25-board run (300 pcs) verify the reel break/stock at
  order time; tape-and-reel `THS3491IDDAR` (DK `296-39990-1-ND`) is the assembly-friendly
  variant.

---

## 7. Failure-flag disclosure (procurement)

1. **No unsourced / out-of-stock Digi-Key lines.** Every passive, MCX, terminal, electrolytic,
   trimpot, standoff, and the THS3491 buffer shows healthy stock as of 2026-06-28.
2. **Cremat modules are direct-order (not Digi-Key)** — expected and inherent to the design;
   flagged as long-lead (§6), not a sourcing failure.
3. **Carryover from Phase B (already resolved):** the charter-locked EL5167 buffer is obsolete
   and was replaced by the active **THS3491** HV-CFA (user-approved). No new buffer risk at ×12.
4. **`Cc` DK PN** Murata `GRM21AR72A224KAC5K` is real & stocked; the `490-13815-1-ND` PN should
   be confirmed at cart (suffix varies by packaging). Equal-spec alts on the line.
5. **`HW_SCREW` PN** (`H743-ND`, M3×6 SS pan) is a generic fastener line; any equivalent M3×6
   SS pan-head is acceptable — listed for completeness (off-board hardware, not placed on PCB).

---

## 8. Interface to C1 / C3 (how to use my output)

- **C1 (design):** instantiate the channel sheet ×12 with channel-suffixed refs; place the
  **§3 board-shared parts exactly** (PNs/footprints above) so Design BOM == this Models-BOM.
  Use the §1 reconciled per-channel PNs (UWT1V101MCL1GS bulk, 1715734 terminal). Restore the
  36 MCX `Edge.Cuts` cutouts. Enforce the §5 DNP rules in ERC/DRC. Add `CBULK_P/N` (radial
  THT) at the power entry plus `J_PWR` (one terminal).
- **C3 (sim):** the §3 current budget (board quiescent +0.56 A / −0.51 A per rail) + central
  2× 470 µF + 12× 100 µF distributed bulk is the shared-rail loading to sanity-check against
  the decoupling network. Per-channel parts are unchanged from Phase B, so the one-channel
  response is unchanged.
- **One-line:** take `twelve-channel-bom.csv`; per-channel = single-channel BOM ×12 (frozen),
  plus the 6 board-shared lines in §3; cost/DNP in §4–§5.
