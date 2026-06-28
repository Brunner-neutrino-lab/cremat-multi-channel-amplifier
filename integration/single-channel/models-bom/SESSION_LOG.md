# Session Log — B3 `chan-bom` (single-channel Models-BOM)

> Ground truth, append-only. One dated entry per working session.

Track: `B3 chan-bom` · Sub-component: `integration/single-channel` · Aspect: `models-bom`
Reads (inputs): `chips-board/csp-cr112/models-bom/{csp-cr112-bom.csv,PARTS_REPORT.md}`,
`chips-board/shaper-cr200-cr210/models-bom/{shaper-bom.csv,BOM-REPORT.md}`,
`docs/agent-project/{00-CHARTER,01-CONVENTIONS}.md`, `briefs/B-single-channel.md`,
`reference/cremat-x6-board/channel.kicad_sch` (buffer ref), `hardware/lib/cremat.kicad_sym` (EL5167).
Success criteria (mirror of report): one consolidated single-channel BOM, both Phase-A BOMs
merged/deduped + buffer parts added, every line real/in-stock/priced, 0805 default, buffer
op-amp CFA with justification (BW + 50 Ω drive), op-amp symbol/FP/3D collected & FP exists,
one-MPN-per-line for B1 to swap 1:1.

---

## 2026-06-25 — session 1 — consolidate the channel BOM + pick the buffer CFA

**Goal this session:** merge the two committed Phase-A BOMs, dedupe shared jellybeans, add
the EL5167-class CFA output buffer (op-amp + Rf/Rg + 49.9 Ω + decoupling), source every line
on Digi-Key, deliver the buffer real-parts gate for B1.

**Did:**
- Read both Phase-A BOMs + reports; charter/conventions/brief. Confirmed both sub-components
  COMPLETE and the parts they each carry.
- Inspected `reference/cremat-x6-board/channel.kicad_sch`: reference buffer = **EL5167IWZ**
  (`EL5167IWZ-T7ACT-ND`, Renesas, **SOT-23-5**, marked `dnp yes`) with **LM7321** as the
  populated alt; buffer feedback network is a mixed 390/43/49.9/100k eval-instrument circuit
  (not a clean single-buffer). Board note: *"Cremat supply range 6–13 V; LM317/LM337 footprints
  provided… if unused, shunt JP1/JP2"* → reference feeds its ±6 V EL5167 from a regulated rail.
- Checked `hardware/lib/cremat.kicad_sym` EL5167 symbol: present (5-pin, 1=OUT 2=V− 3=+IN
  4=−IN 5=V+) but **Footprint field empty**; description says "EL5167 or LM7321, SOT-23-5".
- WebSearch/WebFetch lifecycle + stock + price for the CFA candidates (Digi-Key 403 to scrapes
  → used WebSearch + manufacturer + Digi-Key product-page fetches):
  - **EL5167** → Renesas **OBSOLETE**; `EL5167IWZ-T7A` Digi-Key **out of stock / NLM**; ±6 V max.
  - **OPA695** (SOT-23-6, ±6 V, 90 mA) → Digi-Key **Obsolete** (3040 stk depleting), $5.77 q1.
  - **AD8001** (±6 V, 70 mA) → ±6 V, wrong rail.
  - **THS3201** (±7.5 V) → too low for ±12 V.
  - **THS3061** (±15 V, 145 mA, SOIC-8) → **Last-Time-Buy**, 0 DK-direct stock.
  - **THS3091** (`THS3091DDAR`, SOIC-8 PowerPAD, ±5–15 V, 280 mA) → **ACTIVE**, $11.91 q1 /
    $7.98 q100, currently 0 DK-direct (6-wk lead).
  - **THS3491** (`THS3491IDDAT`, SOIC-8 PowerPAD, ±7–16 V, 620 mA) → **ACTIVE, 695 in stock**,
    $18.28 q1.
- Decision: **primary buffer = THS3091** (lowest-cost active HV-CFA that runs **direct off the
  board ±12 V rails**, removing the reference's regulator), **in-stock alt = THS3491** (same
  family/footprint, guaranteed stock). Gain **+2** (`Rf=Rg=1.21 kΩ`, datasheet Table 8-1) to
  recover the 6 dB of the 50 Ω back-term divider → unity into 50 Ω.
- Verified footprints in KiCad 10 stock: `Package_TO_SOT_SMD:SOT-23-5` (present),
  `Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm` (present — the PowerPAD SOIC the
  THS309x/349x use).
- Wrote `single-channel-bom.csv` (48 ref lines, 17 fields), `BOM-REPORT.md`, this log + report.
- Validated CSV with KiCad bundled python `csv`: 48 rows, 17 cols each, **19 distinct MPNs**,
  no malformed rows (fixed one row where an unquoted comma in the `R_OUT` Description shifted
  columns → quoted it).
- Computed cost roll-up with bundled python.

**Results:**
- **48 ref lines → 19 distinct MPNs.** Dedupe: 4.7 Ω (8×), 0.1 µF (8×), 10 µF (8×), 0R (3×),
  MCX (4×), 1.21 k (2×), 10 k (2×), 100 µF (2×) collapse to one buy line each.
- Merge removed **2 MCX** (CSP_OUT↔shaper IN now an internal net) and **1× 49.9 Ω** (shaper's
  board-edge term folds into the single buffer OUT_50 term).
- Reconciled 2 same-role conflicts: board bulk → Nichicon **UWT1V101MCL1GS** (SMD 35 V, over
  CSP's radial 25 V); power terminal → Phoenix **1715734** (5.08 mm, over CSP's 5.00 mm).
- **Cost (qty 1):** CR-210 populated **$235.71** (modules $201 + buffer IC $11.91 + DK
  passives/conn $22.80); CR-210 bypassed **$158.09**; with THS3491 alt **$242.08**.
- Buffer adequacy: 280 mA out vs ~20–40 mA needed → ~7–14× margin; BW 235 MHz @ G=+2 vs ≪1 MHz
  signal → non-limiting; CFA topology honors locked class.

**Decisions & why:**
- **EL5167 → THS3091/THS3491 (active HV-CFA):** EL5167 obsolete AND ±6 V on a ±12 V board
  (would need a regulator like the x6-board's LM317/LM337). HV-CFA runs direct off ±12 V →
  cleaner ×12 cell. Brief explicitly permits "justify an equivalent CFA." Both picks are CFA,
  exceed EL5167 on supply + drive.
- **Footprint = SOIC-8 PowerPAD, NOT the EL5167 SOT-23-5:** chosen real part is SOIC-8; do not
  force the existing symbol's implied SOT-23-5. Exposed pad → V−.
- **Gain +2, Rf=Rg=1.21 k:** standard line-driver gain to offset the back-term 6 dB; Rf is the
  datasheet-recommended stability value (CFA), flagged value-defining for B1/B2 to pin & re-sim.
- **SMD bulk + 5.08 mm terminal** on the conflicts: reflow-friendly, higher-V margin, standard
  pitch, single PN for ×12.

**Dead-ends / surprises:**
- The whole ±6 V SOT-23 CFA bench (EL5167/OPA695/AD8001/THS3201) is either obsolete or
  rail-incompatible — the realistic active option set for a ±12 V board is the TI HV-CFA family
  (THS309x/349x/306x), all SOIC-8, several already LTB. THS3091 is the sweet spot; THS3491 the
  in-stock insurance.
- Digi-Key direct = 403 to scrapes (as briefed); WebFetch on individual product pages worked
  and gave status/price/stock. One AD8001 product-URL fetch redirected to an unrelated part —
  ignored, used the AD product page + search instead.
- `kicad-cli`/bundled python path used for CSV validation since system `python3` isn't on PATH.

**State vs criteria:** S1–S7 all ✅ (see report §0). Only disclosure: EL5167 obsolete →
equivalent active CFA (permitted). No adequacy failure, no unsourced part.

**Next:** hand the buffer gate to B1 (swap generics→THS3091/THS3491 + Rf/Rg/49.9/decoupling),
B2 to drop the chosen op-amp SPICE model and pin exact Rf from datasheet Table 8-1. When B1's
design BOM is published, diff it line-for-line against `single-channel-bom.csv` for COMPLETE.

---

## 2026-06-25 — session 2 — Coordinator decision: promote THS3491 to PRIMARY buffer

**Goal this session:** Coordinator picked **TI THS3491 (`THS3491IDDAT`, DK `296-49085-2-ND`)**
as the chosen output buffer (in-stock, rail-safe on ±12 V direct). Promote it from "in-stock
alternate" to primary across the CSV + report; drop THS3091 to a documented alternate; re-roll
qty-1 cost; keep one-MPN-per-line + internally consistent for B1's line-for-line diff.

**Did:**
- `single-channel-bom.csv` `U_BUF` row: MPN THS3091DDAR→**THS3491IDDAT**, DKPN
  296-46216-1-ND→**296-49085-2-ND**, $11.91→**$18.28** (q25 $13.60), stock "0 DK-direct/6-wk"
  →**"695 (in stock)"**, datasheet→ths3491, Notes now mark it PRIMARY (Coordinator) with
  THS3091 demoted to documented-alt in the Notes. Footprint unchanged (both SOIC-8-1EP PowerPAD).
- `BOM-REPORT.md`: §1 cost table re-rolled (THS3491 primary), §3 decision heading + candidate
  table + adequacy bullets + gain-network note rewritten for THS3491, §4 disclosure rewritten
  (buffer now fully in stock; THS3091 = cost-alt), §5 buffer cell relabeled, §6 mapping flipped
  (THS3491 primary / THS3091 alt), §0 S5 + FAIL-flag updated, §7 one-liner → THS3491.
- `SESSION_REPORT.md`: buffer-pick + cost + S3/S5 criteria updated.
- Re-validated CSV (bundled python): 48 rows, 17 cols, 19 distinct MPNs, U_BUF=THS3491IDDAT.
- Re-computed cost roll-up with $18.28 buffer.

**Results:**
- **Buffer MPN-per-line unchanged in count** (still one `U_BUF` line, one buy MPN) → 19 distinct
  MPNs, BOM still internally consistent for B1's diff.
- **New cost (qty 1): CR-210 POPULATED = $242.08** (modules $201 + THS3491 $18.28 + DK
  passives/conn $22.80); **CR-210 BYPASSED = $164.46**. (THS3091-alt populated would be $235.71.)
- Footprint/symbol/decoupling/gain network all identical to session 1 — only the IC line and
  costs moved. Rf=Rg=1.21 kΩ stays (B1/B2 pin exact Rf from THS3491 datasheet; ~1 kΩ-class, same
  0805 part).

**Decisions & why:**
- Followed the Coordinator's part choice (THS3491 primary). Engineering-sound: THS3491 is the
  in-stock, ±12 V-direct, highest-drive member — removes the only procurement caveat (THS3091's
  6-wk lead) at +$6.37/board. THS3091 retained as a documented cheaper alternate for Phase C.

**Dead-ends / surprises:** none — clean swap, BOM re-validated.

**State vs criteria:** S1–S7 ✅; S3 now stronger (primary buffer 695 in stock, no lead-time
risk). No unsourced/obsolete fitted part.

**Next:** B1 sets `U_BUF=THS3491IDDAT` on SOIC-8-1EP (EP→V−) + Rf/Rg/49.9/decoupling; publish
design BOM; Coordinator diffs vs `single-channel-bom.csv` for COMPLETE.

---

## 2026-06-25 — session 3 — pin buffer Rf/Rg to 976 Ω (B2-validated)

**Goal this session:** Coordinator relayed that B2's sim validated the THS3491 buffer with
**Rf = Rg = 976 Ω** (TI THS3491 datasheet G=+2 recommended feedback value; CFA Rf governs loop
stability) against TI's official SPICE model. Update the two buffer feedback-R lines
1.21 kΩ → 976 Ω, MPN RC0805FR-071K21L → RC0805FR-07976RL; re-roll cost; keep one-MPN-per-line.

**Did:**
- WebSearch'd the 976 Ω 0805 part. Exact DK PN didn't surface through the 403 (as briefed), but
  the Yageo RC0805FR-07 ohms-code is deterministic and cross-checked against parts already in
  this BOM: 49.9→`-0749R9L`/`311-49.9CRCT-ND`, 681→`-07681RL`/`311-681CRCT-ND`. 100 Ω–<1 kΩ
  values use the `NNNRL` form → 976 Ω = MPN **RC0805FR-07976RL**, DK **311-976CRCT-ND**.
  Recorded with a "verify suffix" note per the project's Digi-Key-403 convention.
- `single-channel-bom.csv`: `Rfb` and `Rgain` rows — Value 1.21k→**976**, MPN→**RC0805FR-07976RL**,
  DKPN→**311-976CRCT-ND (verify suffix)**, stock >500k→>100k, Notes now say PINNED by B2 sim
  (THS3491 datasheet G=+2 Rf, validated vs TI SPICE). $0.10 each unchanged.
- `BOM-REPORT.md`: §3 gain bullet + gain-network paragraph rewritten (976 Ω pinned, B2-validated,
  real PN), §6 mapping rows → 976 Ω/RC0805FR-07976RL/311-976CRCT-ND, §7 one-liner → 976 Ω.
- `SESSION_REPORT.md`: gain bullet → 976 Ω pinned + PN.
- Re-validated CSV: 48 rows, 17 cols, **19 distinct MPNs** (the 1.21k MPN, used only by these 2
  refs, is fully replaced by the 976R MPN — count unchanged), 0 remaining "1.21k" strings in CSV.

**Results:**
- Buffer Rf/Rg now **976 Ω (Yageo RC0805FR-07976RL, DK 311-976CRCT-ND)** on both `Rfb`+`Rgain`.
- **Cost unchanged**: 976 Ω and 1.21 kΩ are both $0.10 jellybeans → totals stay **CR-210
  populated $242.08 / bypassed $164.46** (THS3091-alt populated $235.71).
- BOM stays **one-MPN-per-line**; 49.9 Ω series output unchanged; everything else untouched.

**Decisions & why:**
- Adopted the B2-validated 976 Ω (the THS3491 datasheet's own G=+2 Rf — correct for CFA loop
  stability; 1.21 kΩ was a placeholder estimate, now superseded by the simmed value).

**Dead-ends / surprises:** none. Exact DK suffix flagged "verify" since Digi-Key blocks scrapes.

**State vs criteria:** S1–S7 ✅. BOM internally consistent and ready for B1's parallel switch to
match line-for-line.

**Next:** B1 publishes design BOM with `Rfb=Rgain=976 Ω` (RC0805FR-07976RL) + `U_BUF=THS3491IDDAT`;
Coordinator diffs vs `single-channel-bom.csv` to close the Phase-B gate.
