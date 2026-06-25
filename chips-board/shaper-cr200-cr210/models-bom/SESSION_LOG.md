# Session Log — A6 shaper-bom

> **Ground truth, append-only.** One dated entry per working session: what you did, exact
> commands/tools, results (numbers, ERC/DRC counts, sim figures of merit), decisions **and
> why**, dead-ends, next steps. Never rewrite earlier entries.

Track: `A6 shaper-bom` · Sub-component: `shaper-cr200-cr210` · Aspect: `models-bom`
Reads (inputs): charter, conventions §7, brief A-shaper-cr200-cr210.md, `reference/cremat-CR-160-R7/CR-160-R7.net`, `hardware/lib/cremat.kicad_sym`, `hardware/lib/cremat.pretty/`, `hardware/bom/`.
Success criteria (mirror of report): every part on the CR-200 (M1) and CR-200+CR-210 (M2) board sourced to a real, in-stock, economical Digi-Key part (modules via Cremat-direct) with full provenance; explicit DNP table for CR-210 populated vs bypassed; BOM CSV + report delivered; 1:1 generic→real mapping for A4/A5.

---

## 2026-06-25 — session 1 — full M1+M2 BOM sourced

**Goal this session:** Source every part for the shaper/BLR eval board (both milestones),
make the DNP state explicit, deliver CSV + report + generic→real mapping.

**Did:**
- Read charter, conventions (§7 sourcing), brief. Created `chips-board/shaper-cr200-cr210/models-bom/`, copied protocol templates.
- Studied prior art: `hardware/lib/cremat.kicad_sym` (CR-200/CR-210 symbols + confirmed pinouts), `hardware/lib/cremat.pretty/` (MCX CONMCX013 fp + STEP present), `hardware/bom/bom.md` + `bom-full-variant.csv`.
- Extracted the authoritative application circuit from `reference/cremat-CR-160-R7/CR-160-R7.net` with a Python net-parser (KiCad bundled python). Mapped every net touching U4(CR-200), U5(CR-210), R7(200k P/Z trim), R9(100k P/Z fixed), R25(100k), R20(1k), JU1(bypass jumper). Key results:
  - U4.2(P/Z) <-> R7.1 (200k trimpot); U4.1(in) <-> R7.2. => **R7=200k pole-zero trim**.
  - JU1.1 = U4.8(CR-200 out) + U5.1(CR-210 in); JU1.2 = U5.8(CR-210 out) + R20. => **JU1 bridges CR-200 out -> CR-210 out, bypassing CR-210. Populate U5 XOR JU1.** Confirms the iron-rule jumper scheme.
  - Per-rail decoupling pattern: 4.7 ohm (1206) + 10uF (1206) + 0.1uF (0805) per rail; board bulk 1000uF.
- WebSearch + WebFetch (Digi-Key direct = 403 to bots, per coordinator; used product pages where reachable, octopart/manufacturer + search snippets otherwise):
  - Module pricing from cremat.com US price list (retrieved 2026-06-25): **CR-200-1us-R2.1 $59 (1-24)/$55 (25+); CR-210-R0 $77 (1-24)/$69 (25+).**
  - Digi-Key parts confirmed in stock: Yageo RC0805 R (100k 311-100KCRCT-ND, 49.9 311-49.9CRCT-ND, 4.7 311-4.7ARCT-ND, 0R 311-0.0ARCT-ND), Samsung CL21 MLCC (0.1uF/50V 1276-1000-1-ND, 10uF/25V 1276-1037-1-ND), Nichicon UWT 100uF/35V 493-2203-1-ND, Bourns 3296W-1-204LF 200k 3296W-204LF-ND, Phoenix 1715734 MKDS 1,5/3-5,08 277-1264-ND, TE/Linx CONMCX013 343-CONMCX013-ND ($3.22 qty1, 1200 in stock, tray, 50ohm/8.5GHz).
- Wrote `shaper-bom.csv` (per-line value/MPN/mfr/DK-PN/cost/stock/pkg/fp/sym/3D/datasheet/milestone + two populate columns), `BOM-REPORT.md` (tables, DNP table, cost roll-up, deviations, generic->real mapping). Computed cost roll-ups with python/csv.

**Results:**
- All lines sourced + in stock; **0 unsourced / 0 obsolete / 0 out-of-stock.**
- Cost roll-up (qty1): M1 = $72.29; M2 CR-210-populated = $150.01; M2 CR-210-bypassed = $72.39. Cremat modules ~90% of cost; passives+conn <= $15/board.
- Symbol/footprint/3D: all present in repo + KiCad stock libs. **No login-gated downloads needed.**

**Decisions & why:**
- **Scope = shaper/BLR core only**, not the whole CR-160-R7. Excluded the 3x EL5163, MAX4649 mux, SW1 DIP, HA9P5002 op-amp, and the discrete +-11/+-6V regulator transistor net - those are the eval-instrument buffer/IO and belong to the single-channel buffer track (B). Brief scopes A6 to CR-200 + P/Z + per-rail decoupling + CR-210 + bypass + MCX + screw term. Modules run directly off +-12V with the canonical 4.7+10uF+0.1uF per-rail RC (the relevant slice of CR-160-R7's supply).
- **Passives 0805** per project default; 1% on signal-defining R (P/Z 100k, 49.9 term), 5% acceptable on 4.7 ohm decoupling + 0R jumper. Jellybean Yageo RC / Samsung CL21 / Bourns 3296W chosen for max stock + min cost + lowest supply risk.
- **Bulk 100uF/35V** instead of CR-160-R7's 1000uF - single-channel eval needs far less; 35V >> 12V.
- **CR-210 decoupling (Rdp2/Rdn2/Cbp2/Cbn2/Clp2/Cln2) is DNP when CR-210 bypassed** - no module to feed.

**Dead-ends / surprises:**
- CR-200/CR-210 app-guide PDFs (cremat.com) use CID/subset font encoding => raw stream text extraction = garbage. No PDF text/render libs in KiCad python (no fitz/pypdfium2/pdfminer). Fell back to the CR-160-R7 **netlist** as the authoritative application circuit (it is Cremat's own OSHW eval board for these modules) - better than the PDF anyway.
- Digi-Key + octopart return HTTP 403 to WebFetch (expected per coordinator); the digikey product-detail page for CONMCX013 did resolve via WebFetch and gave exact price/stock.

**State vs criteria:** All success criteria met for M1 and M2. BOM == intended design topology (CR-160-R7-derived). Awaiting A4 design BOM to confirm 1:1 consistency at the Coordinator COMPLETE gate.

**Next:** Hand the generic->real mapping to A4 (design) and A5 (sim) for the real-parts swap. If A4's ref designators differ, reconcile names (values/MPNs are the binding part). Update if A4 adds support passives I didn't anticipate.

---

## 2026-06-25 — session 2 — coordinator reconciliation: remove the 100k `R_PZ2`

**Goal this session:** act on the coordinator finding that the 100k "P/Z fixed R" (`R_PZ2`)
does not belong on the shaper board; remove it from the BOM + report; record the evidence.

**Finding (re-verified against `reference/cremat-CR-160-R7/CR-160-R7.net`):** my session-1
mapping mis-attributed `R9` (100k). `R9` is on **net code 10 `Net-(R9-Pad2)` → `U7` pin6
(MAX4649 mux) + `SW1` pin1 (gain/polarity DIP)**, with `R9` pin1 → +11V (net code 1) — i.e. the
buffer/mux/gain-DIP section I **explicitly excluded** from A6 scope (§5 Deviations). It is NOT
in the CR-200 P/Z. The CR-200 pole-zero is the **200k trimpot `R7` alone** (net code 3 `R7-Pad1`
→ `U4`/CR-200 pin2 P/Z; net code 9 `R7-Pad2` → `U4` pin1 input). So the 100k must not be on
the shaper board.

**Did:**
- Removed the `R_PZ2` (100k, RC0805FR-07100KL) row from `shaper-bom.csv`. Annotated `R_PZ`
  (200k) as the **sole** P/Z element.
- Updated `BOM-REPORT.md`: dropped R_PZ2 from the intro topology line, the parts table, the DNP
  table, and the generic→real map; fixed the cost roll-up; appended a dated reconciliation note
  with the net-code-10 evidence. Added a forward-pointer note near the top.
- Confirmed with A4: design removed the matching part from `gen_sch.py`/`gen_pcb.py`, regenerated
  + re-routed both milestones (ERC 0/0, DRC 0/0/0/0), design BOM == this BOM (incl. DNP).

**Results (figures):**
- BOM lines after removal: **M1 = 14 fitted; M2 = 21 fitted + 1 DNP (`JP_BLR` 0R).**
- Cost roll-up (qty1) revised −$0.10/variant: **M1 $72.19; M2-populated $149.91; M2-bypassed $72.29.**
- 0 unsourced / 0 obsolete / 0 out-of-stock still holds (only a line was removed).

**Decisions & why:** removed rather than re-homed the 100k — there is no fixed-R companion in the
CR-200 P/Z (the trimpot is the whole network); keeping it would diverge from the reference and
from A4's verified design. Net-code-10 evidence is authoritative (Cremat's own OSHW eval board).

**Dead-ends / surprises:** none — the removal re-placed/re-routed cleanly on A4's side.

**State vs criteria:** all criteria still met. **BOM == design BOM confirmed** for M1 and M2
(incl. DNP table) — the previously-pending consistency item is now closed.

**Next:** none pending — reconciliation closed. Coordinator commits.
