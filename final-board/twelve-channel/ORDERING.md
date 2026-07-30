# ORDERING — 12-channel board via JLCPCB (fab + SMT/THT assembly) + DigiKey (hand parts)

> Master buy-sheet. Two orders: **JLCPCB** (boards + all SMD parts **and** the THT trimpots +
> screw terminals assembled — MCX included) and **DigiKey** (SIP-8 sockets + case, hand parts).
> The Cremat modules you already have plug into the sockets. Part numbers/stock/prices were
> live-verified 2026-07-11 → 2026-07-30. Re-check stock in the JLC BOM tool at order time.

**BUILD PLAN: 5 assembled boards.** JLC: **fab qty 5** (JLC's 4-layer minimum) + **assembly qty 5**
(all five assembled — no bare spares; raise PCB qty if you want some). DigiKey hand parts: **SIP-8
sockets for 2.5 boards** (the 2 boxed boards + spares) and **one 2U case** (holds the 2-board stack; the
other 3 boards are spares, unboxed).

> ## ⚠ Assembly tier: **STANDARD, not Economic**
> The MCX edge jack **BWMCX-KEF (LCSC C5250059)** is the only true-MCX part in JLC's library;
> it is **PCBA type "Standard Only"** (verified on jlcpcb.com/partdetail 2026-07-30) with
> **"High" assembly difficulty**. It is **not** in the Economic-tier feeder library, so an
> Economic-tier order rejects all 48 MCX as **UNMATCHED at upload** — the same failure mode
> the ROQANG 470 µF hit. **Select JLC's Standard assembly tier.** Standard places every part
> (Basic, Extended, Standard-only) plus the THT parts (wave soldering) and covers this 4-layer
> board. The Economic fee figures no longer apply — **the live Standard-tier quote after BOM/CPL
> upload is authoritative.** (The only Economic-tier edge jack, BWMMCX-KEF-B / C47324993, is
> **MMCX** — a smaller, incompatible family — so it is not an option.)

## The split

| Who | What | Files |
|---|---|---|
| **JLCPCB** | 4-layer PCB fab + **Standard**-tier assembly of all **308** parts/board: **294 SMD** (246 passives/diodes/PTC + 48 MCX edge jacks) + **14 THT wave-soldered** (12 trimpots + 2 screw terminals) | `design/fab/jlc/` (gerber zip, BOM, CPL) |
| **DigiKey** | Hand parts: **36× SIP-8 sockets** per board + **1× 2U case** (+ optional buffer parts, DNP) | `models-bom/digikey-hand-bom.csv` |
| **You already have** | Cremat CR-112 / CR-200-1us / CR-210 ×12 per board (×5 boards = 60 each) — plug into sockets | — |

Hand-solder is now **only the SIP-8 sockets** (you wanted to solder those anyway; no turned-pin
8P SIP socket is both in JLC's library and in stock — see the socket note). Everything else —
SMD, the 48 MCX, the 12 trimpots, and the 2 screw terminals — lands assembled by JLC.

## 1. JLCPCB order (jlcpcb.com → "Order now" wizard)

**Files (in `design/fab/jlc/`):**
1. `gerber-twelve-channel-jlc.zip` — upload first (gerbers + Excellon drill; KiCad 10 export).
   *Regenerated 2026-07-30 to add the D1/D2 silk cathode stripes (top silk only; copper/drill
   unchanged). The zip is gitignored — regenerate from `twelve-channel.kicad_pcb` if missing
   (`kicad-cli pcb export gerbers|drill` → zip, see REVIEW.md).*
2. `bom-twelve-channel-jlc.csv` — BOM, JLC headers (`Comment,Designator,Footprint,JLCPCB Part #`).
   **15 lines**: MCX (`BWMCX-KEF … C5250059`, J1–J48), trimpot (`3296W-1-204 … C48997932`, RV1–RV12),
   screw terminal (`KF128-5.0-3P … C474951`, J49–J50) — the last two THT, wave-soldered.
3. `cpl-twelve-channel-jlc.csv` — pick-and-place, JLC headers (`Designator,Mid X,Mid Y,Layer,Rotation`),
   **308 placements** = 294 SMD (incl. 48 MCX) + 14 THT (12 trimpots + 2 terminals). Only the 36
   SIP-8 sockets and all DNP are excluded. *(Carries manual CPL corrections — see the ⚠ list below.)*

**Wizard settings (verified against a live quote, qty 5):**
- Detected size 213.2 × 334.7 mm, **4 layers**, 1.6 mm, 1 oz outer / 0.5 oz inner, green.
- Surface finish: **leaded HASL** ($73.70/5 boards incl. $25 eng fee + $5 large-size) or
  **ENIG** (+$24.70 → $98.40/5). ENIG is nicer for the MCX edge pads; HASL is fine.
- **Impedance: leave OFF (normal build).** Do **not** request controlled impedance. If a
  remarks/note field is offered, paste (≤200 char, JLC's limit):
  > `4-layer, 1.6mm, JLC04161H-7628 stackup. No controlled impedance. Do not tune trace
  > width; signals are grounded-coplanar (GND pour + inner GND plane), not microstrip.` *(165 chars)*
- The board's 48 edge notches are routed slots ≥5 mm — well within capability; expect at
  most a manual engineering review, no surcharge (routing density ~12 m/m² vs 80 limit).
- **PCB Assembly: STANDARD tier (see ⚠ above), top side, PCBA qty = 5.** Set PCB qty 5, assembly
  qty 5 — all five assembled. Upload BOM + CPL when prompted.
- **Standard-tier fees (live quote is authoritative):** a Standard setup fee + stencil +
  per-Extended-part feeder fees + THT wave-solder charge + per-joint + parts. The MCX (C5250059)
  is **Extended + "High" difficulty**, so expect a **DFM review** and possibly a handling surcharge
  on the edge connector. Per-board parts ≈ 48× MCX @ $0.49 + 12× trimpot @ $0.23 + 2× terminal
  @ $0.39 + SMD passives (~$18) ≈ **$45/board**.
  ⚠ JLC also lists an undocumented per-order assembly "Large Size" fee (~$59) that may appear
  for a 334.7 mm board; the live quote is authoritative.

**In the parts-review screen, check (manual CPL corrections — all live ONLY in the CPL; re-apply
if the CPL is ever regenerated from the board):**
- **J1–J48 (MCX):** rotation +90° CCW (left 0° / right 180°) **and** `Mid X` −1.8 mm inboard
  (left 6.3→8.1, right 206.9→205.1) — the BWMCX-KEF mounting reference is offset from the Linx
  land. Regen → re-apply +90° (left −90°→0°, right +90°→180°) and −1.8 mm on Mid X. Confirm the
  barrel points off the board edge and the part seats on its pads.
- **D1/D2 (Schottky):** rotation +180° (→90°) so the cathode band lands on **pad 1** (cathode:
  D1=+VDC, D2=−VDC_F, per `D_Schottky` pin1=K). A **silk cathode stripe** was added at pad 1 on
  both (board + gerber regenerated). Regen → re-apply +180°. Confirm each band aligns with its stripe.
- **RV1–RV12 (trimpots):** rotation 90° CW (→270°) **and** `Mid X` −2.54 mm to the pin centroid
  (the 3296W footprint origin sits on pin 1, one pitch right of center). Regen → re-apply.
- **J49/J50 (terminals):** `Mid X` −5.0 mm to the pin centroid (the MKDS origin sits on pin 1,
  one 5 mm pitch right of center). Regen → re-apply. Confirm the wire openings face the board edge.
- **C133/C134 (electrolytic)** are already correct — leave them.
- The 470 µF stays **C494847** (Panasonic EEE-FN1V471UP); it is "Economic + Standard" PCBA and
  the verified choice. (The ROQANG C72519 substitute was Standard-only → UNMATCHED in Economic,
  but that's moot in the Standard tier we're ordering.)

**BOM parts encoded (subs chosen to hit JLC's Basic library / dodge per-line feeder fees):**

| Board value (silk/BOM) | Placed at JLC | LCSC | Class | Why |
|---|---|---|---|---|
| 49.9R Yageo | UNI-ROYAL 0805W8F499JT5E (1%) | C17720 | Basic | spec-identical |
| 0.22 µF 100 V KEMET | **exact KEMET** C0805C224K1RACTU | C2167405 | Ext | HV part — exact (fallback Yageo C513710) |
| 0R Yageo | UNI-ROYAL 0805W8F0000T5E | C17477 | Basic | 0R jumper |
| 100 nF 100 V Samsung | **exact** CL21B104KCFNNNE | C28233 | Basic | exact AND Basic |
| 10k Yageo | **YAGEO RC0805FR-0710KL** (1%) | C84376 | Basic | 1.03 M in stock 2026-07-28 |
| 10 µF 25 V KEMET | Samsung CL21A106KAYNNNE (25 V X5R) | C15850 | Basic | KEMET 25V not at LCSC in 0805 |
| 10 pF 1% C0G Yageo | **exact** CC0805FRNPO9BN100 | C541512 | Ext | precision test-input cap; no Basic option |
| 4.7R Yageo (5%) | **FOJAN FRC0805F4R70TS** (1%) | C2933459 | **Ext** | Basic C17675 went LCSC-OOS — see ⚠ below |
| 47R Yageo (5%) | UNI-ROYAL 0805W8F470KT5E equiv | C17714 | Basic | equal-or-better |
| 470 µF 35 V Panasonic | **exact** EEEFN1V471UP | C494847 | Ext | JLC "Economic+Standard" PCBA |
| PTC 1812 1.1 A Littelfuse | **exact** 1812L110/24DR | C207066 | Ext | no Basic PTC |
| SSA24 Schottky | **MDD SS34** (SMA, 40 V, 3 A) | C8678 | Basic | board silk SSA24 — electrically compatible |
| **MCX edge jack 50R** | **BAT WIRELESS BWMCX-KEF** | **C5250059** | **Ext** | SMD edge-mount, Standard-only + High difficulty; drop-in on the Linx CONMCX013 land. J1–J48. |
| **200k trimpot 3296W** | **JIERR 3296W-1-204** | **C48997932** | **Ext** | THT wave-solder; exact 3296W footprint + 200k. RV1–RV12. |
| **Screw terminal 3-pos** | **Cixi Kefa KF128-5.0-3P** | **C474951** | **Ext** | THT wave-solder; exact 5.00 mm 3-pos footprint. J49–J50. |

> **⚠ 4.7 Ω (R6…R209, 144 pcs).** The only JLC-Basic 4.7 Ω 0805 was C17675, now LCSC-OOS, so the
> BOM uses Extended C2933459 (feeder fee). **At upload, check whether JLC's assembly pool still
> lists C17675 as in-stock Basic** (its feeders are a separate pool from LCSC retail); if so revert
> to C17675 to drop the fee. Electrically identical.

DNP stays DNP (buffer block THS3491 + 976R + bypass-variant jumpers/caps are **not** in the
JLC BOM/CPL — populate by hand later if wanted).

## 2. DigiKey order (hand parts) — `models-bom/digikey-hand-bom.csv`

Quick-Add paste for the **5-board build** (sockets for 2.5 boards; one 2U case):

```
612-SS-108-TT-2-ND, 90
HM1166-ND, 1
```

= **~$304.03** (sockets 90 × $1.17 ≈ $105.30 + one 2U case $198.73). Optional buffer if ever
populating (5 boards, DNP by default): `296-49085-1-ND, 60` + `311-976CRCT-ND, 120` (+~$1.1k).
⚠ **Sockets: order qty 90 (2.5 boards' worth); DigiKey stock ~649.** The trimpots and screw
terminals are **no longer on this list** — JLC wave-solders them now.

## 3. Hand-assembly order of operations (per board — ×5)

1. JLC boards arrive with all SMD parts + the 48 MCX + 12 trimpots + 2 screw terminals mounted.
2. **Inspect the 48 MCX joints first** (edge-mount, "High" difficulty): barrel square over its
   edge slot, centre pin / ground pads wetted. Also check the diode bands align with the silk stripes.
3. Hand-solder the **36× SIP-8 sockets** (plug a Cremat module in while soldering so the 8 align).
4. Plug in the Cremat modules; set trimpots per the P/Z procedure (`sim/SESSION_REPORT.md`).
5. **Box mounting (2U):** mill the front/rear panel slots and mount the 2-board stack on standoffs
   in the 2U case — see the box-assembly drawings + standoff BOM (mechanical design).

## Cost snapshot (the 5-board build plan, indicative — live JLC quote authoritative)

| Item | Cost |
|---|---|
| JLC: 5× PCB fab (4L, HASL, large-size incl.) | ~$74 (+$25 ENIG option) |
| JLC: **Standard**-tier assembly, 5 boards (setup + stencil + feeders + THT wave + joints + parts) | ~$275 |
| DigiKey: 90× SIP-8 sockets + 1× 2U case + standoffs | ~$311 |
| **Total ex-shipping (Cremat modules already owned)** | **~$660** |

Shipping: JLC ~$40 (DHL, 5 boards); DigiKey usual. (+ possible ~$59 JLC assembly large-size fee,
and a DFM/handling surcharge for the High-difficulty MCX — see above.)

Full DigiKey-only reference (if ever skipping JLC assembly): `models-bom/PURCHASING.md`.
