# Models-BOM report — `shaper-cr200-cr210` (Track A6)

Real, in-stock, economical Digi-Key parts for the standalone **CR-200 shaper + CR-210 BLR**
single-channel eval board. Two milestones: **M1 = CR-200 only**, **M2 = + CR-210** (with the
0R populate-or-bypass jumper). Machine-readable BOM: [`shaper-bom.csv`](shaper-bom.csv).

Topology source of truth: Cremat's own OSHW eval board **CR-160-R7**
(`reference/cremat-CR-160-R7/CR-160-R7.net`), which is the application circuit for these
exact modules (U4=CR-200, U5=CR-210, JU1=bypass jumper, **R7=200k P/Z trim — the sole CR-200
pole-zero element**, per-rail 4.7Ω+10µF+0.1µF decoupling). Module pinout per
`hardware/lib/cremat.kicad_sym`.

> **Reconciliation 2026-06-25:** an earlier revision of this BOM also listed a 100k "P/Z fixed
> R" (`R_PZ2`) citing CR-160-R7 `R9`. That was wrong and has been removed — `R9` is in the
> MAX4649-mux / gain-polarity-DIP buffer section that is **out of this sub-component's scope**.
> See the [reconciliation note](#reconciliation-note--r_pz2-100k-removed-2026-06-25) at the bottom.

> **Real-parts gate output (for A4/A5):** one chosen MPN per generic — see the
> [generic→real mapping](#genericreal-mapping-for-a4-design--a5-sim) at the bottom. Swap 1:1.

---

## 1. Parts table (per single channel)

All passives are **0805** (the project default where the part allows). Cremat modules are
SIP-8 THT; trimpot/screw-terminal/electrolytic are THT. Prices are Digi-Key USD, qty 1.

### Active modules (Cremat-direct — NOT Digi-Key)

| Ref | Part | MPN | Source | $ qty1 | $ qty25+ | Pkg | Sym / Fp |
|---|---|---|---|---|---|---|---|
| `U_SHAPER` | CR-200 1µs Gaussian shaper | CR-200-1us-R2.1 | cremat.com (direct) | 59.00 | 55.00 | SIP-8 | cremat.kicad_sym `CR-200` / PinHeader_1x08 |
| `U_BLR` | CR-210 baseline restorer | CR-210-R0 | cremat.com / Amazon | 77.00 | 69.00 | SIP-8 | cremat.kicad_sym `CR-210` / PinHeader_1x08 |

> Modules are **made-to-order, long lead — order early.** Not stocked at Digi-Key (Cremat
> sells direct). Prices from the current Cremat US price list (retrieved 2026-06-25).

### Passives, jumper, connectors (Digi-Key)

| Ref | Value | MPN | Mfr | DK PN | $ qty1 | Stock | Pkg | Footprint (KiCad) |
|---|---|---|---|---|---|---|---|---|
| `R_PZ` | 200k trim (sole P/Z) | 3296W-1-204LF | Bourns | 3296W-204LF-ND | 3.15 | >5k | 3296W THT | Potentiometer_Bourns_3296W_Vertical |
| `R_OUT` | 49.9 | RC0805FR-0749R9L | Yageo | 311-49.9CRCT-ND | 0.11 | >100k | 0805 | R_0805_2012Metric |
| `Rdp1`,`Rdn1` | 4.7 | RC0805JR-074R7L | Yageo | 311-4.7ARCT-ND | 0.10 | >1M | 0805 | R_0805_2012Metric |
| `Rdp2`,`Rdn2` | 4.7 (CR-210) | RC0805JR-074R7L | Yageo | 311-4.7ARCT-ND | 0.10 | >1M | 0805 | R_0805_2012Metric |
| `JP_BLR` | 0R | RC0805JR-070RL | Yageo | 311-0.0ARCT-ND | 0.10 | >1M | 0805 | R_0805_2012Metric |
| `Cbp1`,`Cbn1` | 0.1µF 50V X7R | CL21B104KBCNNNC | Samsung | 1276-1000-1-ND | 0.08 | >4M | 0805 | C_0805_2012Metric |
| `Cbp2`,`Cbn2` | 0.1µF (CR-210) | CL21B104KBCNNNC | Samsung | 1276-1000-1-ND | 0.08 | >4M | 0805 | C_0805_2012Metric |
| `Clp1`,`Cln1` | 10µF 25V X5R | CL21A106KAYNNNE | Samsung | 1276-1037-1-ND | 0.18 | >500k | 0805 | C_0805_2012Metric |
| `Clp2`,`Cln2` | 10µF (CR-210) | CL21A106KAYNNNE | Samsung | 1276-1037-1-ND | 0.18 | >500k | 0805 | C_0805_2012Metric |
| `Cbulk_p`,`Cbulk_n` | 100µF 35V | UWT1V101MCL1GS | Nichicon | 493-2203-1-ND | 0.40 | >20k | SMD can 6.3×7.7 | CP_Elec_6.3x7.7 |
| `J_IN`,`J_OUT` | MCX edge jack 50Ω | CONMCX013 | TE/Linx | 343-CONMCX013-ND | 3.22 | 1200 | MCX edge | cremat:MCX_CONMCX013_EdgeMount |
| `J_PWR` | 3-pos screw 5.08mm | 1715734 | Phoenix Contact | 277-1264-ND | 1.97 | >5k | THT | TerminalBlock_Phoenix_MKDS-1.5-3 |

All Digi-Key lines verified **in stock** (2026-06-25). No obsolete/NRND parts. Datasheet
links + 3D/footprint/symbol source per line in [`shaper-bom.csv`](shaper-bom.csv).

---

## 2. DNP / populate-or-bypass table (the iron-rule jumper)

The CR-210 is **optional**, resolved by a 0R jumper exactly as Cremat's CR-160-R7 does it
(JU1 bridges CR-200 output → board output, jumping over the CR-210). **`U_BLR` XOR `JP_BLR`
— never both, never neither.** When the CR-210 is bypassed, its dedicated decoupling is also
DNP (no module to feed).

| Ref | Variant: **CR-210 POPULATED** (M2 default) | Variant: **CR-210 BYPASSED** |
|---|---|---|
| `U_SHAPER` (CR-200) | ● fitted | ● fitted |
| `R_PZ` (P/Z trim — sole P/Z element) | ● fitted | ● fitted |
| `Rdp1/Rdn1`, `Cbp1/Cbn1`, `Clp1/Cln1` (CR-200 decoupling) | ● fitted | ● fitted |
| `R_OUT`, `J_IN`, `J_OUT`, `J_PWR`, `Cbulk_p/n` | ● fitted | ● fitted |
| **`U_BLR` (CR-210)** | ● **fitted** | ✕ **DNP** |
| **`JP_BLR` (0R bypass)** | ✕ **DNP** | ● **fitted** |
| `Rdp2/Rdn2`, `Cbp2/Cbn2`, `Clp2/Cln2` (CR-210 decoupling) | ● fitted | ✕ DNP |

**Invariant (must hold in design ERC/DRC):** `U_BLR` populated ⊕ `JP_BLR` populated.

---

## 3. Cost roll-up (Digi-Key + Cremat, qty 1, single channel)

| Configuration | Fitted lines | Total $ | Modules $ | Passives+conn $ |
|---|---|---|---|---|
| **M1** (CR-200 only) | 14 | **72.19** | 59.00 | 13.19 |
| **M2 — CR-210 populated** | 21 | **149.91** | 136.00 | 13.91 |
| **M2 — CR-210 bypassed** | 15 | **72.29** | 59.00 | 13.29 |

(Each variant dropped one fitted line / **−$0.10** vs the pre-reconcile roll-up: the 100k
`R_PZ2` was removed 2026-06-25 — see the reconciliation note below.)

The Cremat modules dominate cost (≈90%). Passives are sub-$15/board jellybeans — economical
by construction (Yageo RC/Samsung CL MLCC/Bourns 3296W are the lowest-risk, highest-stock
choices). Module qty-25 break drops CR-200→$55, CR-210→$69 for a 12-up final board.

---

## 4. Economy / selection justification

- **Passives = Yageo RC0805 + Samsung CL21 MLCC**: the canonical multi-million-stock,
  ~$0.01–0.18 jellybeans; 0805 per project default; 1% (F) on signal-defining R (P/Z,
  termination), 5% (J) acceptable on the 4.7Ω rail-decoupling series R and the 0R jumper.
- **MLCC voltages**: 50V X7R for 0.1µF bypass, 25V X5R for 10µF local bulk — both ≫ the ±12V
  rails. (No HV here — the shaper is downstream of the CSP; the HV bias front-end lives on
  the CSP board, not this one.)
- **R_PZ trimpot = Bourns 3296W-1-204LF (200k, 25-turn)**: matches CR-160-R7 R7 value;
  3296W is the standard, well-stocked trimpot already used elsewhere in this project's BOM.
- **MCX `CONMCX013`**: mandated I/O connector (locked decision); footprint + STEP already in
  `hardware/lib/cremat.pretty` — no new model needed.
- **Bulk = 100µF/35V SMD electrolytic** (Nichicon UWT) instead of the CR-160-R7's 1000µF —
  a single-channel eval board doesn't need 1000µF; 100µF/rail is ample and far smaller.

---

## 5. Deviations from CR-160-R7 (and why)

The CR-160-R7 is a **full eval instrument** (3× EL5163 buffers, a MAX4649 input mux, a
polarity/gain DIP, an HA9P5002 output op-amp, and a discrete Q1/Q2/D1/D2 ±11V/±6V rail
regulator). Our brief scopes this board to **CR-200 + P/Z + per-rail decoupling + CR-210 +
bypass + MCX I/O + screw terminal** only. Therefore **excluded** (out of scope, belong to the
single-channel/buffer track B): the EL5163/HA9P5002 buffer chain, MAX4649 mux, SW1 DIP, and
the discrete rail-regulator transistor network. The modules are run **directly off ±12V via
the simple 4.7Ω+10µF+0.1µF per-rail RC** (Cremat's recommended minimum decoupling), which is
the part of CR-160-R7's supply that is actually about the shaper/BLR. Flagged for A4 to
confirm topology consistency.

---

## 6. Symbol / footprint / 3D status

**All models present — no login-gated downloads required.**

| Item | Symbol | Footprint | 3D |
|---|---|---|---|
| CR-200, CR-210 | `hardware/lib/cremat.kicad_sym` ✅ | KiCad stock `PinHeader_1x08_P2.54mm_Vertical` ✅ | KiCad stock pin-header 3D ✅ |
| MCX CONMCX013 | project `Conn_Coaxial` ✅ | `hardware/lib/cremat.pretty/MCX_CONMCX013_EdgeMount` ✅ | `CONMCX013.step` (SnapEDA, license incl.) ✅ |
| R/C 0805, trimpot, screw term, electrolytic | KiCad stock Device/Connector libs ✅ | KiCad stock fp libs ✅ | KiCad stock 3D ✅ |

No SnapEDA/Ultra-Librarian zip needs to be dropped by a human for this board.

---

## Generic→real mapping (for A4 design / A5 sim)

One MPN per generic value — swap 1:1 in the schematic, re-run ERC/DRC.

| Generic (design uses) | Real MPN | DK PN | Footprint |
|---|---|---|---|
| CR-200-1µs module | CR-200-1us-R2.1 (Cremat) | — (Cremat-direct) | PinHeader_1x08_P2.54mm_Vertical |
| CR-210 module | CR-210-R0 (Cremat) | — (Cremat-direct) | PinHeader_1x08_P2.54mm_Vertical |
| 0R jumper (`JP_BLR`) | Yageo RC0805JR-070RL | 311-0.0ARCT-ND | R_0805_2012Metric |
| 200k trim (sole P/Z element) | Bourns 3296W-1-204LF | 3296W-204LF-ND | Potentiometer_Bourns_3296W_Vertical |
| 49.9 (output term) | Yageo RC0805FR-0749R9L | 311-49.9CRCT-ND | R_0805_2012Metric |
| 4.7 (rail decoupling) | Yageo RC0805JR-074R7L | 311-4.7ARCT-ND | R_0805_2012Metric |
| 0.1µF 50V X7R (bypass) | Samsung CL21B104KBCNNNC | 1276-1000-1-ND | C_0805_2012Metric |
| 10µF 25V X5R (local bulk) | Samsung CL21A106KAYNNNE | 1276-1037-1-ND | C_0805_2012Metric |
| 100µF 35V (board bulk) | Nichicon UWT1V101MCL1GS | 493-2203-1-ND | CP_Elec_6.3x7.7 |
| MCX jack (`J_IN`/`J_OUT`) | TE/Linx CONMCX013 | 343-CONMCX013-ND | cremat:MCX_CONMCX013_EdgeMount |
| 3-pos screw terminal (`J_PWR`) | Phoenix 1715734 (MKDS 1,5/3-5,08) | 277-1264-ND | TerminalBlock_Phoenix_MKDS-1.5-3 |

---

## Reconciliation note — `R_PZ2` (100k) removed (2026-06-25)

**What changed:** the `R_PZ2` line — a 100k 0805 (`RC0805FR-07100KL`) labeled "P/Z fixed R,
P/Z network" and citing CR-160-R7 `R9` — has been **removed** from this BOM (the CSV row, the
parts table, the DNP table, the generic→real map, and the cost roll-up). The design (A4)
removed the matching part from `gen_sch.py`/`gen_pcb.py` and re-verified both milestones.

**Why (the evidence):** the `R9` citation was incorrect. In `reference/cremat-CR-160-R7/CR-160-R7.net`:

- **`R9` (100k) is on net code 10, `Net-(R9-Pad2)` → `U7` pin6 (MAX4649 mux) + `SW1` pin1
  (gain/polarity DIP) + `R9` pin1 → +11V rail (net code 1).** That is the **buffer / input-mux /
  gain-DIP section** — exactly the part of CR-160-R7 this sub-component **excludes** (see §5
  Deviations). It is *not* part of the CR-200 pole-zero network.
- **The CR-200 pole-zero is the 200k trimpot `R7` alone:** net code 3 (`R7-Pad1` → `U4` pin2 =
  CR-200 P/Z) and net code 9 (`R7-Pad2` → `U4` pin1 = CR-200 input). `U4` is the CR-200. No
  fixed 100k participates in the P/Z.

So the 100k did not belong on the shaper board. After removal the P/Z is correctly **`R_PZ`
(200k trimpot) only**, and no node is left floating (the design re-ran ERC 0/0 and DRC 0/0/0/0
on both milestones). Design BOM == this BOM for M1 and M2, including the DNP table.

**Cost impact:** each variant dropped one $0.10 line (M1 72.29→72.19, M2-populated
150.01→149.91, M2-bypassed 72.39→72.29).
