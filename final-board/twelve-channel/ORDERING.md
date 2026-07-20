# ORDERING — 12-channel board via JLCPCB (fab + SMT assembly) + DigiKey (hand parts)

> Master buy-sheet as of **2026-07-11**. Two orders: **JLCPCB** (boards + all SMD passives
> assembled) and **DigiKey** (connectors/sockets/trimpots/case, hand-soldered). The Cremat
> modules you already have plug into the sockets. All part numbers, stock and prices below
> were live-verified 2026-07-11 (13-agent sourcing pass; re-check in the JLC BOM tool at
> order time — stock moves).

**BUILD PLAN: 2 assembled boards.** JLC: fab qty **5** (JLC's 4-layer minimum — the 3 extra
bare boards are free spares), **assembly qty 2**. DigiKey: hand-solder parts at 2-board
quantities **+20% spares** (breakage/loss margin); cases exactly 2 (not solderable — no spares).

## The split

| Who | What | Files |
|---|---|---|
| **JLCPCB** | 4-layer PCB fab + SMT assembly of all 246 FIT SMD passives/diodes/PTC per board | `design/fab/jlc/` (gerber zip, BOM, CPL) |
| **DigiKey** | Hand-solder parts: 48× MCX, 36× SIP-8 sockets, 12× trimpots, 2× screw terminals, 1× case per board (+ optional buffer parts) | `models-bom/digikey-hand-bom.csv` |
| **You already have** | Cremat CR-112 / CR-200-1us / CR-210 ×12 each — plug into sockets after soldering | — |

Hand-solder = the THT parts (you wanted to solder the sockets yourself anyway) + the
edge-mount MCX (not an LCSC part). Everything else lands assembled.

## 1. JLCPCB order (jlcpcb.com → "Order now" wizard)

**Files (in `design/fab/jlc/`):**
1. `gerber-twelve-channel-jlc.zip` — upload first (gerbers + Excellon drill; KiCad 10 export).
2. `bom-twelve-channel-jlc.csv` — BOM, JLC headers (`Comment,Designator,Footprint,JLCPCB Part #`).
3. `cpl-twelve-channel-jlc.csv` — pick-and-place, JLC headers (`Designator,Mid X,Mid Y,Layer,Rotation`),
   246 placements (FIT SMD only; DNP and THT excluded).

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
- **PCB Assembly: Economic tier, top side, PCBA qty = 2** (board qualifies: 4L/1.6 mm/green/
  one-sided, 2–50 pcs; no edge rails or fiducials required). Set PCB qty 5, assembly qty 2 —
  JLC assembles 2 of the 5 and ships 3 bare. Upload BOM + CPL when prompted.
- Assembly fees (Economic): $8 setup + $1.50 stencil + **4 Extended lines × $3 = $12**
  (8 of 12 lines are Basic = free) + ~$0.0016/joint (~$2/board) + parts (~$18/board).
  ⚠ JLC lists an undocumented per-order assembly "Large Size" fee ($59.23) — it may appear
  for a 334.7 mm board; the live assembly quote after gerber upload is authoritative.

**In the parts-review screen, check:**
- **D1/D2 (Schottky) and C10/C11 (electrolytic) polarity/rotation** — JLC's preview renders
  each part on the footprint; rotate in the tool if the cathode band / cap stripe is wrong.
  (KiCad→JLC rotation conventions differ for polarized parts; everything else is 0805 chips.)
- The 470 µF (C494847) had only ~53 pcs at JLC — enough for ~5 boards; fallback pre-verified:
  ROQANG RVT1V471M1010 = **C72519** (130k stock, standard-ESR — fine for bulk duty).

**BOM substitutions already encoded (all spec-equal-or-better, chosen to hit JLC's Basic
library and dodge $3/line fees):**

| Board value (silk/BOM) | Placed at JLC | LCSC | Class | Why |
|---|---|---|---|---|
| 49.9R Yageo | UNI-ROYAL 0805W8F499JT5E (1%) | C17720 | Basic | spec-identical |
| 0.22 µF 100 V KEMET | **exact KEMET** C0805C224K1RACTU | C2167405 | Ext | HV part — exact (fallback Yageo C513710) |
| 0R Yageo | UNI-ROYAL 0805W8F0000T5E | C17477 | Basic | 0R jumper |
| 100 nF 100 V Samsung | **exact** CL21B104KCFNNNE | C28233 | Basic | exact AND Basic |
| 10k Yageo | UNI-ROYAL 0805W8F1002T5E (1%) | C17414 | Basic | spec-identical |
| 10 µF 25 V KEMET | Samsung CL21A106KAYNNNE (25 V X5R) | C15850 | Basic | KEMET 25V not at LCSC in 0805 (their "106K8" = 10 V — never sub those) |
| 1 pF C0G Yageo | **exact** CC0805CRNPO9BN1R0 | C513668 | Ext | no Basic 1 pF exists |
| 4.7R / 47R Yageo (5%) | UNI-ROYAL 1% equivalents | C17675 / C17714 | Basic | equal-or-better |
| 470 µF 35 V Panasonic | **exact** EEEFN1V471UP | C494847 | Ext | low-ESR FN series |
| PTC 1812 1.1 A Littelfuse | **exact** 1812L110/24DR | C207066 | Ext | no Basic PTC |
| SSA24 Schottky | **MDD SS34** (SMA, 40 V, 3 A ≥ 2 A) | C8678 | Basic | SSA24 has 2 pcs at LCSC; board silk says SSA24 — electrically compatible |

DNP stays DNP (buffer block THS3491 + 976R + bypass-variant jumpers/caps are **not** in the
JLC BOM/CPL — populate by hand later if wanted).

## 2. DigiKey order (hand-solder parts) — `models-bom/digikey-hand-bom.csv`

Quick-Add paste for the **2-board build + 20% spares** (per-line: ceil(per-board × 2 × 1.2);
cases exactly 2):

```
343-CONMCX013-ND, 116
612-SS-108-TT-2-ND, 87
3296W-204LF-ND, 29
277-1264-ND, 5
HM1004-ND, 2
```

= **$893.04** (MCX $373.52 + sockets $101.79 + trimpots $70.76 + terminals $8.55 + cases
$338.42). Optional buffer if ever populating (2 boards + 20%, DNP by default):
`296-49085-1-ND, 29` + `311-976CRCT-ND, 58` (+$536).
⚠ **Trimpots: order qty 29 vs ~80 in DigiKey stock — order promptly**, or take the balance
from Mouser `652-3296W-1-204LF` (~1.5k). Per-board reference quantities stay in the CSV.

## 3. Hand-assembly order of operations (per board — ×2)

1. JLC boards arrive with all SMD passives mounted.
2. Solder 36× SIP-8 sockets (plug a Cremat module in while soldering so the 8 sockets align).
3. Solder 48× MCX edge jacks, 12× trimpots, 2× screw terminals.
4. Plug in the Cremat modules; set trimpots per the P/Z procedure (`sim/SESSION_REPORT.md`).
5. Mill the two panel slots per case (~340 × 7 mm — spec in `design/SESSION_LOG.md`
   session 14), mount on standoffs, slide panels over the protruding board edges.

## Cost snapshot (the 2-board build plan, indicative)

| Item | Cost |
|---|---|
| JLC: 5× PCB fab (4L, HASL, large-size incl.; 3 bare spares) | ~$74 (+$25 ENIG option) |
| JLC: assembly setup + stencil + 4 ext lines | ~$22 |
| JLC: joints + parts, 2 assembled boards | ~$40 |
| DigiKey hand parts (2 boards + 20% spares, incl. 2 cases) | ~$893 |
| **Total ex-shipping (modules already owned)** | **~$1,030** |

Shipping: JLC ~$30 (DHL, ~1.4 kg); DigiKey usual. (+ possible ~$59 JLC assembly
large-size fee — see above.)

Full DigiKey-only reference (if ever skipping JLC assembly): `models-bom/PURCHASING.md`.
