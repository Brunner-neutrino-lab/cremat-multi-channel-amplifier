# Single-channel consolidated Models-BOM — Track B3 (`chan-bom`)

Real, in-stock, economical Digi-Key parts for **one complete channel**: the two proven
Phase-A sub-components (CR-112 CSP + bias front-end, CR-200 shaper + CR-210 BLR) **merged**
and the **CFA output buffer** (50 Ω back-terminated `OUT_50`) **added**. This is the
**buffer real-parts gate**: B1 (design) swaps its generic buffer parts → the MPNs below 1:1.

Machine-readable BOM: [`single-channel-bom.csv`](single-channel-bom.csv) (17 fields/line).

> **Inputs merged (both COMPLETE + committed):**
> `chips-board/csp-cr112/models-bom/csp-cr112-bom.csv` (+ `PARTS_REPORT.md`) and
> `chips-board/shaper-cr200-cr210/models-bom/shaper-bom.csv` (+ `BOM-REPORT.md`).
> Signal chain: `BIAS_IN/SIPM → [CSP] → [SHAPER+BLR] → [BUFFER] → OUT_50 (MCX, Zout=50 Ω)`.

---

## 0. Success / failure criteria (stated before the work)

| # | Criterion | Result |
|---|---|---|
| S1 | One consolidated single-channel BOM; the two Phase-A BOMs merged with shared jellybeans deduped (common value once, qty summed) | ✅ 48 ref lines → **19 distinct MPNs**; shared passives/connectors merged (see §2) |
| S2 | Buffer parts added: CFA op-amp + feedback/gain R's + 49.9 Ω series + decoupling | ✅ `U_BUF`+`Rfb`+`Rgain`+`R_OUT`+`Rdp3/Rdn3`+`Cbp3/Cbn3`+`Clp3/Cln3` |
| S3 | Every line real / in-stock / economical on Digi-Key with full fields | ✅ all Digi-Key lines in stock & priced — incl. the primary buffer (THS3491, 695 in stock). See §4. |
| S4 | Default passives 0805 | ✅ every R/C is 0805 (modules/trimpot/terminal/electrolytic are their native THT/SMD packages) |
| S5 | Buffer op-amp chosen **with explicit justification**: CFA, adequate BW + output drive for 50 Ω back-terminated load | ✅ §3 — **THS3491** (CFA, ±7–16V, 620 mA, 900 MHz, runs direct on ±12V; in stock) |
| S6 | Op-amp symbol/footprint/3D collected; footprint exists | ✅ §5 — KiCad `SOIC-8-1EP` PowerPAD FP verified present; symbol via KiCad `Amplifier_Operational` or re-FP the existing `hardware/lib` EL5167 symbol |
| S7 | One-MPN-per-line so B1 can swap buffer generics → real 1:1 | ✅ §6 mapping |
| **FAIL flags** | unsourced parts / BOM≠design / buffer inadequate for 50 Ω | **None on adequacy.** One disclosure: the locked-class EL5167 is **OBSOLETE** → replaced with an equivalent active CFA (the brief explicitly permits this). See §4. |

---

## 1. Cost roll-up (qty 1, single channel, USD)

Primary buffer = **TI THS3491** (`THS3491IDDAT` @ $18.28 q1), per Coordinator decision (2026-06-25).

| Configuration | Fitted lines | **Total $** | Modules $ | Buffer IC $ | Passives+conn $ |
|---|---|---|---|---|---|
| **CR-210 POPULATED** (default, all blocks fitted) | 45 | **$242.08** | 201.00 | 18.28 | 22.80 |
| **CR-210 BYPASSED** (U_BLR DNP, JP_BLR fitted, CR-210 decoupling DNP) | 40 | **$164.46** | 124.00 | 18.28 | 22.18 |
| CR-210 populated, **buffer alt** (THS3091 @ $11.91, ~6-wk lead) | 45 | **$235.71** | 201.00 | 11.91 | 22.80 |

The **three Cremat modules dominate** (~83% of cost; CR-112 $65 + CR-200 $59 + CR-210 $77 =
$201, all Cremat-direct made-to-order — order early). The buffer IC (THS3491, $18.28) is the
next line item. **All Digi-Key passives + connectors together = $22.80** — jellybeans, noise
vs the modules. Module qty-25 breaks (CR-112 $59 / CR-200 $55 / CR-210 $69) plus the THS3491
qty-25 break ($13.60) drop the ×12 board materially in Phase C.

---

## 2. Merge / dedupe result (how the two Phase-A BOMs were combined)

The two boards each carried their **own copy** of the per-rail decoupling kit, the MCX I/O,
the power terminal, and (on the shaper) a 49.9 Ω output term. Merging into one channel:
**common values collapse to one MPN with summed quantity**, and the **board-edge jacks that
become internal nets are removed**.

### 2a. Shared jellybeans deduped to a single MPN (qty summed)

| Merged MPN | Value | From CSP refs | From Shaper refs | + Buffer refs (new) | Total qty (CR-210 pop.) |
|---|---|---|---|---|---|
| `RC0805JR-074R7L` | 4.7 Ω rail series R | Rdec_P, Rdec_N (2) | Rdp1,Rdn1,Rdp2,Rdn2 (4) | Rdp3,Rdn3 (2) | **8** |
| `CL21B104KBCNNNC` | 0.1 µF 50 V X7R | Cdec_P01,N01 (2) | Cbp1,Cbn1,Cbp2,Cbn2 (4) | Cbp3,Cbn3 (2) | **8** |
| `CL21A106KAYNNNE` | 10 µF 25 V X5R | Cdec_P10,N10 (2) | Clp1,Cln1,Clp2,Cln2 (4) | Clp3,Cln3 (2) | **8** |
| `RC0805JR-070RL` | 0 Ω jumper | JP_Rf1,JP_Rf2 (2) | JP_BLR (1) | — | **3** |
| `CONMCX013` | MCX edge jack | J_BIAS,J_SIPM,J_OUT,J_TEST (4) | J_IN,J_OUT (2) | — | **4** (see 2b) |

### 2b. Board-edge jacks that become **internal nets** (removed in the merge)

| Removed | Was | Now |
|---|---|---|
| CSP `J_OUT` (CSP_OUT) **+** Shaper `J_IN` | two MCX jacks linking CSP→shaper across board edges | **one internal net** `CSP_OUT→IN` (no connector) — **−2 MCX** |
| Shaper board-edge 49.9 Ω `R_OUT` | shaper's own 50 Ω output term at its board edge | shaper output goes **internally to the buffer**; the **single** 49.9 Ω term now lives at the channel's true output `OUT_50` after the buffer — **−1× 49.9 Ω** (the buffer's R_OUT is the one that remains) |

Net MCX count: CSP had 4, shaper had 2 (=6 standalone) → **4 in the merged channel**
(J_BIAS, J_SIPM, J_TEST on the input side + the single final `J_OUT`/OUT_50 after the
buffer). The two internal CSP↔shaper jacks are gone.

### 2c. Conflicting parts reconciled (same role, different Phase-A MPN)

| Role | CSP picked | Shaper picked | **Reconciled to** | Why |
|---|---|---|---|---|
| Board bulk electrolytic (100 µF) | Nichicon **UVR1E101MED** (radial THT, 25 V) | Nichicon **UWT1V101MCL1GS** (SMD can, 35 V) | **UWT1V101MCL1GS (SMD, 35 V)** | SMD reflows with the rest of the board; 35 V > 25 V margin; one part for the ×12 build. |
| 3-pos power screw terminal | Phoenix **1715035** (MKDS 1,5/3, **5.00 mm**) | Phoenix **1715734** (MKDS 1,5/3-5,08, **5.08 mm**) | **1715734 (5.08 mm)** | Both MKDS 1,5/3; 5.08 mm is the standard 0.2" pitch and the footprint already used by the shaper. One terminal PN. |

> These two reconciliations are the only places the two Phase-A BOMs disagreed on a part for
> the same function. **B1 must use the reconciled MPN/footprint** so Models-BOM == Design BOM.

### 2d. Tally

- **48 ref-designator lines** in the merged channel (CR-210-populated, test path fitted).
- **19 distinct MPNs** (the dedupe target — one buy line per unique part).
- Standalone-sum would have been **6 MCX + 2× 49.9 Ω + duplicated decoupling**; the merge
  removed **2 MCX** and **1× 49.9 Ω** that became internal, and collapsed all shared
  passives/jacks/terminal to single buy lines.

---

## 3. Output buffer op-amp — choice + justification (the locked-class real-parts gate)

### Decision (PRIMARY, Coordinator 2026-06-25): **TI THS3491** (`THS3491IDDAT`), a high-voltage current-feedback amplifier — **in stock, rail-safe on ±12 V direct.**
### Documented alternate (same family/footprint, lower cost but ~6-wk lead): **TI THS3091** (`THS3091DDAR`).

**Why a substitution at all:** the charter locks the buffer to **"current-feedback amp,
EL5167-class, 50 Ω back-terminated."** The class (CFA, 50 Ω back-term) is honored. The
specific **EL5167 part is OBSOLETE** at Renesas and its SOT-23-5 (`EL5167IWZ-T7A`) shows
**out of stock / no-longer-manufactured** on Digi-Key (Digi-Key itself lists substitutes).
The brief explicitly allows: *"confirm it's in stock/active, or justify an equivalent CFA."*
→ I confirm EL5167 is **not** active, and justify the equivalent below.

**The decisive constraint — supply rail.** This board runs on **±12 V** (same rails as the
Cremat modules). The EL5167 and the obvious SOT-23 CFA alternates are **±6 V-max** parts:

| Candidate | Type | Max dual supply | Out current | Pkg | Status (2026-06) | Verdict |
|---|---|---|---|---|---|---|
| **EL5167** (locked) | CFA | ±6 V (5–12 V) | ~tens mA | SOT-23-5 | **OBSOLETE / 0 stk** | ✗ obsolete **and** needs a regulator on ±12 V |
| OPA695 | CFA | ±6 V | 90 mA | SOT-23-6 | **OBSOLETE** (3 k stk, depleting) | ✗ obsolete + ±6 V |
| AD8001 | CFA | ±6 V | 70 mA | SOIC-8 / SOT-23-5 | mature | ✗ ±6 V on a ±12 V board |
| THS3201 | CFA | ±7.5 V | ~100 mA | SOT-23-5 | active | ✗ ±7.5 V < ±12 V |
| **THS3491** ✅ **(PRIMARY)** | **CFA** | **±16 V** (14–32 V span) | **620 mA** | SOIC-8 PowerPAD | **ACTIVE, 695 in stk** | ✅ **chosen** — in stock + runs direct on ±12 V |
| **THS3091** ✅ (alt) | **CFA** | **±15 V** (10–30 V) | **280 mA** | SOIC-8 PowerPAD | **ACTIVE** (0 DK-direct, ~6-wk lead) | ✅ documented alternate |
| THS3061 | CFA | ±15 V | 145 mA | SOIC-8 | Last-Time-Buy (0 DK-direct) | ◐ good but LTB |

Every ±6 V CFA (EL5167 included) would require a **local ±12 V→±6 V regulator** — exactly
what the reference x6-board did (its schematic note: *"Cremat supply voltage range is 6 V–13 V…
footprints provided for positive and negative linear regulators… if not used, JP1/JP2
shunted,"* with LM317/LM337 fitted to feed the ±6 V EL5167 buffer). Choosing a **high-voltage
CFA that runs directly off the board's ±12 V rails eliminates that regulator entirely** — a
cleaner single-channel cell to instantiate ×12.

**THS3491 adequacy for a 50 Ω back-terminated output (the failure-flag check):**
- **Current-feedback** topology → honors the locked class. ✅
- **Output drive:** 620 mA into the worst case. The load is the 49.9 Ω back-term in series
  feeding a 50 Ω cable/scope = ~100 Ω total; a ±2 V `OUT_50` swing needs only ~20–40 mA at
  the op-amp pin. **620 mA is ~15–30× margin** (this is a high-power line driver). ✅
- **Bandwidth:** 900 MHz. The signal is a CR-200 **1 µs**-shaped Gaussian (peaking ~1–2 µs,
  content ≪ 1 MHz). BW is **non-limiting by ~3 orders of magnitude** — the buffer adds zero
  shaping distortion; it's chosen for *drive + rail compatibility + stock*, not BW. ✅
- **Slew rate:** 8000 V/µs — the 1 µs pulse's slew demand (~µV/ns) is trivially met. ✅
- **Gain:** non-inverting **G = +2** (`Rfb=Rgain=976 Ω`) to recover the 6 dB lost in the
  50 Ω back-term resistive divider → **unity end-to-end into a 50 Ω load** (standard line-driver
  configuration). ✅

**Gain network (CFA-critical):** for a CFA, the feedback resistor `Rf` sets loop stability, not
just gain — `Rf` must be the datasheet's recommended value. **PINNED: `Rfb = Rgain = 976 Ω`
(1 %, E96, 0805)** — the TI THS3491 datasheet G=+2 recommended feedback value, **validated by
B2's sim against TI's official SPICE model** (2026-06-25). Real part: Yageo **RC0805FR-07976RL**
(DK `311-976CRCT-ND`, same 0805 jellybean, in stock). (If the documented alt THS3091 is used
instead, its own Table 8-1 G=+2 value is ~1.21 kΩ — same 0805 footprint/part line, only the
ohm value shifts one E96 step; pick per the populated op-amp.)

---

## 4. Failure-flag disclosure (procurement)

1. **EL5167 (charter-locked part) is OBSOLETE** → replaced by the active CFA **THS3491**
   (Coordinator-chosen primary; justified §3). This is a *part* swap within the *locked
   class*, which the brief permits. **Not** an adequacy failure — the replacement exceeds
   EL5167 on supply range, output drive, and bandwidth.
2. **Buffer is fully in stock — no lead-time risk on the primary.** THS3491IDDAT
   (`296-49085-2-ND`) = **695 in stock**, $18.28 qty1 / $13.60 qty25, status **Active**,
   SOIC-8 PowerPAD, ±7–16 V (runs direct off ±12 V), 620 mA out. The documented alternate
   **THS3091DDAR** (`296-46216-1-ND`, $11.91 qty1, 280 mA, also Active) is cheaper but
   currently 0 DK-direct stock / ~6-wk factory lead — kept on the `U_BUF` Notes as a
   cost-optimization option for Phase C if it returns to stock. *(THS3061 rejected: also
   Last-Time-Buy / 0 DK stock.)*
3. **No other unsourced / obsolete parts.** All passives, MCX, terminal, electrolytic, trimpot
   show healthy stock (passives >100 k–4 M; CONMCX013 >1000; Nichicon/Phoenix/Bourns ship today).
4. **`Cc` Digi-Key PN suffix not 100 % pinned** (carried over from CSP A3): Murata
   `GRM21AR72A224KAC5K` (0.22 µF/100 V/X7R/0805) is confirmed real & stocked; search the exact
   `490-…` PN on digikey.com. Equal-spec alts: TDK `CGA4J3X7T2A224K125AE`, KEMET `C0805C224K1RAC`.

---

## 5. Buffer symbol / footprint / 3D provenance (S6)

| Item | Symbol | Footprint | 3D | Status |
|---|---|---|---|---|
| **Buffer CFA** (THS3491 primary / THS3091 alt) | KiCad `Amplifier_Operational` 8-pin op-amp symbol *or* re-use the existing `hardware/lib/cremat.kicad_sym` **EL5167** symbol (5-pin) — **but** that symbol is SOT-23-5; the THS3491/3091 is **SOIC-8 PowerPAD**, so the cleaner path is the KiCad stock op-amp symbol (8-pin: OUT/−IN/+IN/V−/V+/NC/NC/V+ or pad) | **`Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm`** (TI DDA PowerPAD = SOIC-8 + exposed thermal pad) — **VERIFIED present** in `C:/Program Files/KiCad/10.0/share/kicad/footprints/Package_SO.pretty/` | KiCad stock SOIC-8 3D | **Ready** (footprint confirmed; symbol from KiCad lib) |
| `Rfb`,`Rgain`,`R_OUT` 0805 | KiCad `Device:R` | `Resistor_SMD:R_0805_2012Metric` | KiCad stock | Ready |
| buffer decoupling 0.1µF/10µF 0805 | KiCad `Device:C` | `Capacitor_SMD:C_0805_2012Metric` | KiCad stock | Ready |

> **Footprint note for B1:** the existing `hardware/lib` **EL5167 symbol's Footprint field is
> empty** (`""`) and its description implies **SOT-23-5**. Since the chosen real CFA is
> **SOIC-8 PowerPAD**, do **not** force the SOT-23-5 footprint. Either (a) use the KiCad
> `Amplifier_Operational` 8-pin CFA symbol with `SOIC-8-1EP…EP2.29x3mm`, or (b) add an
> 8-pin THS3091 symbol to the project lib. The footprint itself is stock-verified.
> The exposed pad (pin "EP"/pad) ties to the **most-negative supply (V−)** per TI PowerPAD
> guidance — tell B1.
- **No login-gated download required for the buffer.** (The only project-wide login item
  carried from Phase A is the optional `Cc` Murata 3D; the generic KiCad C_0805 3D is fine.
  The MCX `CONMCX013.step` is present in `hardware/lib/cremat.pretty/` per the shaper report.)

---

## 6. Generic → real mapping for B1 (swap 1:1, then re-run ERC/DRC)

**Buffer block (the new parts B1 adds):**

| B1 design generic | → chosen real MPN | Digi-Key PN | Footprint |
|---|---|---|---|
| CFA op-amp "EL5167-class" | **TI THS3491IDDAT** (alt: THS3091DDAR) | **296-49085-2-ND** (alt 296-46216-1-ND) | `Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm` (EP→V−) |
| buffer Rf "976 Ω" (`Rfb`) | Yageo RC0805FR-07976RL | 311-976CRCT-ND | `Resistor_SMD:R_0805_2012Metric` |
| buffer Rg "976 Ω" (`Rgain`) | Yageo RC0805FR-07976RL | 311-976CRCT-ND | `Resistor_SMD:R_0805_2012Metric` |
| output term "49.9 Ω" (`R_OUT`) | Yageo RC0805FR-0749R9L | 311-49.9CRCT-ND | `Resistor_SMD:R_0805_2012Metric` |
| buffer rail R "4.7 Ω" (`Rdp3/Rdn3`) | Yageo RC0805JR-074R7L | 311-4.7ARCT-ND | `Resistor_SMD:R_0805_2012Metric` |
| buffer HF cap "0.1 µF" (`Cbp3/Cbn3`) | Samsung CL21B104KBCNNNC | 1276-1000-1-ND | `Capacitor_SMD:C_0805_2012Metric` |
| buffer bulk "10 µF" (`Clp3/Cln3`) | Samsung CL21A106KAYNNNE | 1276-1037-1-ND | `Capacitor_SMD:C_0805_2012Metric` |

**Merged-in CSP + shaper parts** keep their Phase-A MPNs unchanged **except the two §2c
reconciliations** (use the *reconciled* PN): board bulk → **UWT1V101MCL1GS** (SMD), power
terminal → **Phoenix 1715734** (5.08 mm). All other CSP/shaper rows = identical to the
committed Phase-A BOMs. Full per-line detail in [`single-channel-bom.csv`](single-channel-bom.csv).

**DNP / variant rules carried forward (B1 enforce in ERC/DRC):**
- **CR-210:** `U_BLR` ⊕ `JP_BLR` (exactly one). When bypassed: `Rdp2/Rdn2/Cbp2/Cbn2/Clp2/Cln2`
  also DNP.
- **Bias filter:** `Rf1/Rf2/Cf` (fitted) ⊕ `JP_Rf1/JP_Rf2` (fitted) — populate-or-bypass.
- **Test path:** `Ctest/R_test/J_TEST` DNP if no bench charge-injection.
- **Buffer is always FIT** (no DNP) — it's the channel's mandatory output stage.

---

## 7. One-line use

> B1: take the CSV, set `U_BUF = THS3491IDDAT` (DK 296-49085-2-ND, the Coordinator-chosen
> primary) on `SOIC-8-1EP…EP2.29x3mm` (EP→V−), `Rfb=Rgain=976 Ω`, `R_OUT=49.9 Ω`, add
> 4.7 Ω/0.1 µF/10 µF buffer decoupling; use the §2c reconciled bulk + terminal PNs;
> everything else is the committed Phase-A parts. Then Models-BOM == Design BOM.
