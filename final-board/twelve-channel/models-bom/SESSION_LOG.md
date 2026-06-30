# Session Log — C2 board-bom

> **Ground truth, append-only.** One dated entry per working session.

Track: `C2 board-bom` · Sub-component: `twelve-channel` (Phase C) · Aspect: `models-bom`
Reads (inputs): `00-CHARTER.md`, `01-CONVENTIONS.md` (§7 sourcing), `briefs/C-twelve-channel.md`,
`integration/single-channel/models-bom/single-channel-bom.csv` + `BOM-REPORT.md`,
`hardware/mechanical.md`, Cremat CR-112/CR-200/CR-210 app guides, TI THS3491 datasheet.
Success criteria (mirror of report): final priced ×12 BOM, every line real/in-stock/Digi-Key,
per-channel == single-channel ×12, board-shared parts added & sized for 12×, DNP variant table,
total cost @ q1 + q25, long-lead (36 modules) flagged. == the C1 board.

---

## 2026-06-28 — session 1 — build the final twelve-channel BOM

**Goal this session:** scale the COMPLETE single-channel BOM ×12, add board-level shared
parts (power terminal sized for 12×, central bulk, M3 hardware), produce DNP variants + costs.

**Did:**
- Read the four required docs + the single-channel BOM (48 refs / 19 MPNs) + mechanical.md
  (4× M3 corner holes, 1U ~35 mm height budget, 36 MCX split across two long edges).
- Created `final-board/twelve-channel/models-bom/` and copied SESSION_LOG/REPORT templates.
- Built the **current budget** from datasheets (the gating input for terminal sizing):
  - WebFetch Cremat CR-112 app guide PDF: power supply current **5.5 mA pos / 5.5 mA neg**.
  - WebFetch Cremat CR-200 app guide PDF: quiescent power supply current **7 mA**, max out 20 mA.
  - WebFetch Cremat CR-210-R0 spec PDF: power supply current **17 mA pos / 13 mA neg**, max out 35 mA.
  - WebSearch TI THS3491: trimmed quiescent **~16.8 mA** (power-down drops to 750 µA).
  - Per channel ≈ +46.3 / −42.3 mA → **×12 ≈ +0.56 A / −0.51 A** quiescent per rail.
- Sourced board-shared parts on Digi-Key (WebSearch + Octopart, DK direct = 403):
  - Power terminal: Phoenix **1715734** MKDS 1,5/3-5,08 = **17.5 A / 400 V**, DK 277-1264-ND,
    $1.97 q1 — ~30× margin over 0.56 A → no upsizing needed (and it's the same PN the
    single-channel BOM already used; at board level it's ONE shared terminal, not ×12).
  - Central bulk: Nichicon **UVR1V471MPD** 470 µF/35 V radial THT, DK **493-1084-ND**,
    $0.51 q1, **4512 in stock**. 2× (one per rail) at the entry, backing the 12× distributed
    100 µF (UWT1V101MCL1GS) carried from the per-channel cell.
  - Mounting: Keystone **24338** M3 hex Al standoff (36-24338-ND, $0.83) ×4 + M3×6 SS pan
    screws (H743-ND, $0.10) ×8; 4× MountingHole_3.2mm_M3 = 0-cost board feature.
- Wrote `twelve-channel-bom.csv`: 45 PER-CHANNEL ref-types (×12 each, exact copies of the
  single-channel BOM) + 6 BOARD-SHARED lines. Scaling model: `J_PWR` lifted from per-channel
  to shared ×1; `Cbulk_P/N` kept ×12 as distributed bulk AND new central `CBULK_P/N` added.
- Wrote `cost.py` (scratchpad) to roll up q1 + q25 (prod-break) costs for FULL and
  CR-210-bypassed variants; cross-checked against the single-channel total.

**Results:**
- **FULL (CR-210 + bias filter populated, test DNP):** 41 fitted/ch ×12 + 15 shared pcs.
  **1 board q1 = $2,847.27** · **1 board q25-break = $2,517.63** · **25 boards = $62,940.80**.
- **CR-210 BYPASSED:** **1 board q1 = $1,915.83** · q25 $1,687.62 · 25 boards $42,190.40.
- **36 Cremat modules dominate ~85%** ($2,412 q1 / $2,196 q25 for the 36). Board-shared = $7.11.
- Cross-check vs single-channel FULL ($242.08, 45 lines incl test): my per-channel FULL
  ($236.68, 41 lines) = $242.08 − test path ($3.43) − J_PWR moved to shared ($1.97). reconciles.

**Decisions & why:**
- **Terminal NOT upsized:** 0.56 A peak rail vs 17.5 A rating; the datasheet current budget
  proves the existing 1715734 is ample. Documented the budget rather than guessing.
- **Added a central 470 µF pair on top of the 12× distributed 100 µF:** one power entry feeding
  12 cells needs a central reservoir for the THS3491 line-driver transients; radial THT chosen
  (taller part clears the 1U height budget at the board edge; cheap, high stock).
- **J_PWR → shared ×1, not ×12:** logically one power entry per board (matches mechanical.md
  "J_PWR on a short edge" — singular). Published this unambiguously so C1 places ONE terminal.

**Dead-ends / surprises:**
- DK direct + Octopart product pages return 403 to automated fetch (expected per brief) —
  used WebSearch result snippets + manufacturer/Octopart search listings, cited DK PNs.
- Cremat PDFs returned as binary to WebFetch; read the saved PDFs directly to extract the
  spec tables (CR-112/200/210 supply currents). Worked.

**State vs criteria:** All criteria met (S1–S7). No unsourced/out-of-stock lines. BOM ready
for C1 to match (board-shared section is the published source of truth).

**Next:** await C1's design-BOM so the Coordinator can confirm Models-BOM == Design BOM. If
C1 names refs differently or adds/removes a shared part, reconcile here.
