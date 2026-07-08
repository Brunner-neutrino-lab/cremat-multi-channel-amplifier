# INTERFACE — `single-channel` (full channel: CSP + shaper/BLR + CFA output buffer)

> Owned by **B1 chan-design**. The contract Phase C (twelve-channel) integrates against
> without reading internals. Status: **REAL-PARTS schematic, human-review WIRED redraw
> (2026-07), ERC 0/0.** Design BOM == `models-bom/single-channel-bom.csv` (**45 refs**).
> The two Phase-A signal blocks are reused, plus three 2026-07 design changes: the **output
> buffer (TI THS3491) is now a populate-or-bypass block, DNP by default**; each supply rail
> carries a **reverse-polarity block (PTC + series Schottky)**; and the test input, HF
> decoupling and layout were reworked (all detailed below).
>
> **⚠ PCB is STALE.** `channel.kicad_pcb` predates this 2026-07 rework (buffer-bypass jumper,
> rail-protection parts, dropped 0.1 µF HF caps, reworked test input), so the earlier
> "DRC 0/0/0, fully autorouted (FreeRouting score 996)" describes the **pre-rework** netlist.
> The layout rebuild — deferred until schematic + BOM + docs are wrapped — will re-sync it.

## What this board is — one complete channel

```
BIAS_IN(MCX,<=60V) ─Rf1─┬─Rf2─ FE ── SIPM(MCX, DC to detector)
                        Cf(HV)│        │
                        GND   │       Cc(HV) ─► CR-112 ─CSP_OUT─► CR-200(1µs) ─SH_OUT─► CR-210(BLR)
TEST_IN(MCX) ─┬─47R─ GND       │       (+ P/Z trim 200k)          (JP_BLR 0R bypass)   │ SHAPER_OUT
              └─1pF─► CSP_IN                                                            ▼
                                    SHAPER_OUT ─┬─► [THS3491 CFA buffer, Av=+2] ─► BUF_OUT
                                                │      (Rf=Rg=976R) — DNP BY DEFAULT      │
                                                └──────── JP_BUF 0R (fitted, DEFAULT) ────┤ BUF_OUT
                                                                                     49.9Ω  (50Ω back-term)
                                                                                          │
                                                                                       OUT_50 (MCX, Zout=50Ω)
Power: ±12V/GND via 3-pos screw terminal ─► per-rail PTC(0.1A) + series Schottky(SS14) REVERSE-BLOCK ─► +VDC/−VDC.
Per-rail decoupling = 4.7Ω + 10µF at every module (+ the buffer, DNP); ONE 100µF rail-bulk pair. (0.1µF HF caps dropped in the 2026-07 rework.)
Default build: buffer DNP + JP_BUF fitted → CR-210 drives the 49.9Ω back-term directly (OUT_50 = ½·SHAPER_OUT into 50Ω).
Populated build: fit the THS3491 block, remove JP_BUF → Av=+2 recovers the ÷2 (OUT_50 ≈ SHAPER_OUT into 50Ω).
Detector charge sign must make the CR-112/CR-200 output POSITIVE into the CR-210 (see Polarity).
```

The signal chain is the two **proven Phase-A sub-components wired in series** (CR-112 CSP
output → CR-200 shaper input on one board, no MCX between; CR-210 output drives the buffer
+IN directly) followed by a **TI THS3491 high-voltage current-feedback output buffer**
(EL5167-class, runs direct on ±12 V) that presents a **50 Ω back-terminated** output.

## Electrical I/O (ports)

| Port | Dir | Connector | Signal | Range / notes |
|------|-----|-----------|--------|---------------|
| `BIAS_IN` | in | MCX (J1) | SiPM bias DC | **≤ 60 V** (HV net, `hv_bias` class 0.6 mm). Through RC+R filter to `FE`. |
| `SIPM`    | i/o | MCX (J2) | detector bias + charge | DC-coupled to filtered bias node `FE`; carries HV. Detector connects here. |
| `TEST_IN` | in | MCX (J3) | test pulse | Coax-terminated charge injector: 47 Ω shunt to GND (`R5`) + 1 pF series (`C3`) → CSP input. A V step `Vt` injects `Q = 1 pF × Vt`. (2026-07 rework — `R5` is now the shunt termination, **not** a series R; net `TEST_N` is gone.) |
| `OUT_50`  | out | MCX (J4) | shaped Gaussian pulse | **Zout = 50 Ω (back-terminated)**, drives a 50 Ω DAQ/scope. Peaking ≈ 1 µs (CR-200-1µs). **B2 sim (0.5 pC): OUT_50 peak = +67.1 mV into 50 Ω** (= 0.5 pC × 13.3 mV/pC × 10.2 shaper × 1.0 BLR × 2.0 buffer × 0.5 back-term). Unipolar positive (see Polarity below). |
| `+12V`/`GND`/`−12V` | pwr | 3-pos screw terminal (J5) | supply | ±12 V nominal. **Reverse-polarity protection per rail:** terminal → PTC (`F1/F2`, 0.1 A hold) → series Schottky (`D1/D2`, SS14) → `+VDC/−VDC` (~0.4 V drop; blocks reversed leads, interrupts sustained faults). **No over-voltage clamp** (see Protection note). Per-rail 4.7 Ω + 10 µF decoupling + one 100 µF bulk pair. THS3491 (only when populated) runs **direct on ±12 V**, no regulator. |

**Net names (netlist-level):** `BIAS_IN, N_filt, FE, SIPM`shield→`GND`, `TEST_IN` (47 Ω to
GND + 1 pF to CSP_IN — **no** `TEST_N`), `CSP_IN, CSP_OUT` (= CR-112 out **and** CR-200 in —
the merge join), `PZ, SH_OUT, SHAPER_OUT` (= CR-210 out; drives buffer +IN **and** the JP_BUF
bypass), `BUF_OUT` (buffer OUT = JP_BUF far end = R15 in), `BUF_FB, OUT_50`. Rails: raw inputs
`+VDC_IN/−VDC_IN` (screw terminal) → PTC → `+VDC_F/−VDC_F` → Schottky → board rails
`+VDC/−VDC` + `GND`; filtered module/buffer rails `+VS_F/−VS_F` (CSP), `SHVP/SHVN` (CR-200),
`BLVP/BLVN` (CR-210), `BVP/BVN` (buffer).

## Schematic handle (the Phase-C unit)
- **`channel`** — `design/channel.kicad_sch` (flat single sheet; the reusable per-channel
  cell). Generated by `design/gen_sch.py` (**45 symbols**), which as of 2026-07 emits a
  **human-review WIRED layout** (parts placed left→right by stage, signal path drawn
  pin-to-pin, per-rail decoupling in a top/bottom band, rails distributed by power symbols +
  labels) — not the earlier net-label-only capture. Phase C still multiplies the per-channel
  block ×12: every per-channel net is a plain local label (suffix-able to `_chN`), shared
  rails are power symbols. Boundary I/O per channel = `BIAS_IN, SIPM, TEST_IN, OUT_50`
  (4 MCX) + the shared ±12 V screw terminal.
- Key refs: `U1`=CR-112, `U2`=CR-200, `U3`=CR-210, `U4`=**TI THS3491** buffer (**DNP by
  default**); `R18`=**JP_BUF** 0 Ω buffer bypass; `F1/F2`=rail PTCs, `D1/D2`=rail Schottkys.
  THS3491 DDA (SOIC-8 PowerPAD) pin map (KiCad `THS3491xDDA` symbol = datasheet):
  **1=REF, 2=−IN, 3=+IN, 4=V−, 5=NC, 6=OUT, 7=V+, 8=PD, 9=EP** (thermal pad). Module pin
  maps unchanged from Phase A.

## Output buffer (the real stage — TI THS3491)
> **Populate-or-bypass (2026-07): the buffer is DNP by default.** `JP_BUF` (R18, 0 Ω,
> `SHAPER_OUT→BUF_OUT`) is fitted by default and XORs the whole THS3491 block (U4, R13/R14,
> R16/R17, C12/C13 all DNP). **Default build:** CR-210 drives the 49.9 Ω back-term through
> JP_BUF — no active gain, so `OUT_50 = ½·SHAPER_OUT` into 50 Ω (≈ +33.5 mV for 0.5 pC), and
> the CR-210 sources the ~100 Ω back-term load directly (fine at these signal levels vs its
> ~17 mA output rating). **Populated build:** fit the THS3491 block and remove JP_BUF for the
> Av=+2 stage described below (`OUT_50 ≈ SHAPER_OUT`, ≈ +67.1 mV — the 50 Ω line-driver
> variant). `R15` (49.9 Ω), `J4` and `JP_BUF` stay fitted in both. The rest of this section
> describes the **populated** buffer.
- **Part (B3 gate / coordinator):** **TI THS3491** (`THS3491IDDAT`), a high-voltage
  current-feedback amplifier, SOIC-8 PowerPAD (`Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm`).
  Runs **direct on the channel ±12 V rails** (abs-max ±16 V / 32 V span — no regulator),
  ~900 MHz BW, 500 mA out (huge margin to drive the 50 Ω back-term). Honors the locked
  "CFA, 50 Ω back-terminated" decision; replaces the **obsolete** EL5167.
- **Topology:** non-inverting CFA. `SHAPER_OUT → +IN(pin3)`; feedback **Rf (R13) = 976 Ω**
  from `OUT(pin6) → −IN(pin2)`; gain **Rg (R14) = 976 Ω** from `−IN(pin2) → GND`.
  **Av = 1 + Rf/Rg = +2.** (For a CFA, Rf is the stability-critical element — **976 Ω is the
  TI THS3491 datasheet G=+2 recommended feedback value**, B2-validated against TI's official
  SPICE model — so the datasheet value governs the CFA loop. Flat response, no ringing.)
- **Control pins:** `REF(pin1) → GND` (split-supply mode; sets PD thresholds vs GND);
  `PD(pin8) → V+ (BVP)` (tied high = always enabled — TI advises not floating PD);
  `EP(pin9, thermal pad) → V− (BVN)` (heat-sinks to the −VDC plane; per coordinator).
- **50 Ω back-termination:** `OUT(pin6) → Rser (R15) = 49.9 Ω → OUT_50`. Op-amp Zout ≈ 0;
  in series with 49.9 Ω the impedance **looking back into `OUT_50` = 49.9 Ω ≈ 50 Ω**. Into a
  matched 50 Ω load: standard back-terminated line driver, load sees Av·50/(49.9+50) ≈ Av/2
  ≈ ×1, reflection-free. Netlist-audited: `OUT_50` carries only R15-pin2 + J4 (the MCX).
  B2 sim: OUT_50 = ×0.501 of BUF_OUT (back-term divider confirmed), 0 % overshoot into 50 Ω.
- **Decoupling:** per-rail 4.7 Ω series + 10 µF (`BVP/BVN`), same pattern as the Cremat
  modules — the 0.1 µF HF bypass was dropped board-wide in the 2026-07 rework. DNP together
  with the buffer.

## Rail protection (2026-07) — reverse-polarity block + fault interrupt
Each supply rail: **screw terminal → PTC → series Schottky → board rail.**
`+VDC_IN → F1 (PTC) → +VDC_F → D1 (Schottky, cathode→+VDC) → +VDC`; mirror on the −rail
(`F2`, `D2` anode→`−VDC`). The Schottky **blocks a reversed supply** (swapped leads — the #1
bench error); the PTC (100 mA hold, 250 mA trip, 60 V) interrupts a sustained fault. Normal
drop ≈ 0.4 V (rails land ≈ ±11.6 V — well above the modules' ±6 V and the THS3491's ±7 V
minimums).

> **No over-voltage clamp — not a passive option here.** The Cremat modules' supply
> **absolute max is ±13 V** (CR-200 explicit; CR-112/CR-210 spec-table max) vs the **±12 V
> nominal** rail — ~1 V of headroom. A shunt Zener/TVS that idles off at 12 V does not conduct
> until ≥ ~13 V, i.e. at/above the module abs-max, so no passive clamp both stays off at 12 V
> and holds below 13 V (verified vs the CR-112/CR-200/CR-210 + THS3491 datasheets).
> **Over-voltage is an operational limit — set the bench supply correctly.**

Parts: `D1/D2` = onsemi **SS14** (40 V/1 A, `Diode_SMD:D_SMA`); `F1/F2` = Littelfuse
**1206L010/60WR** (0.1 A, `Fuse:Fuse_1206_3216Metric`). New pre-rail nets (all passive):
`+VDC_IN, +VDC_F, −VDC_IN, −VDC_F`.

## CR-210 baseline-restorer polarity (B2 integration finding) — RESOLVED
The real **CR-112 CSP is inverting**, and the CR-200 passband is non-inverting, so the
shaped pulse sign at the **CR-210 input = the CR-112 output sign**. The Cremat **CR-210 is a
unipolar baseline restorer validated for a *positive* pulse** (A5 M2); fed a negative pulse
it mis-restores (B2: a 100 kHz train drove the baseline to +99.8 % of peak instead of ~0).
The channel must therefore present the CR-210 a **positive** pulse, exactly as the CR-160-R7
reference arranges (it uses inverting op-amp stages for this).

**Resolution (no added hardware):** the CR-11X output polarity is set entirely by the
**direction of detector current** — Cremat: *"output is positive when the current pulse
flows from the CSP input, negative when current flows into the CSP"* (CR-110/CR-112 work
with either polarity). So the channel is wired/used so the **detector charge direction makes
the CR-112 (hence CR-200) output POSITIVE into the CR-210**. This is a **detector-coupling /
charge-sign constraint**, documented here — it does **not** require an extra inverter (the
non-inverting THS3491 stays as-is) and does **not** alter the proven blocks.

> **Constraint on the assumed detector/charge sign:** connect the SiPM at `SIPM`/`BIAS_IN`
> so its avalanche current flows in the direction that yields a **positive CR-112 output**
> (current flowing *from* the CSP input). With the *opposite* detector polarity the CR-210
> mis-restores under sustained rates — flip the detector connection (or the bias polarity)
> to correct it. B2 verified the corrected polarity: 100 kHz train baseline −0.8 mV (−1.2 %
> of peak), matching the standalone shaper M2 sim. (B2 modeled this as a unity inverter
> between CR-200 and CR-210; in hardware it is realized by the detector charge sign.)

## DNP / optional blocks (populate-or-bypass)
| Block | Populated (default) | DNP (default) | Bypass action |
|-------|--------------------|---------------|---------------|
| CSP bias filter Rf1 (R1) | R1 (10k) | **JP_Rf1 (R2) 0R** | fit R2, remove R1 |
| CSP bias filter Rf2 (R3) | R3 (10k) | **JP_Rf2 (R4) 0R** | fit R4, remove R3 |
| Shaper CR-210 BLR (U3) | **U3 (CR-210)** | **JP_BLR (R12) 0R** | fit R12, DNP U3 (populate-XOR) |
| **Output buffer (U4 block)** — *2026-07* | **JP_BUF (R18) 0R fitted** | **U4, R13/R14, R16/R17, C12/C13** | for Av=+2: fit the U4 block, remove JP_BUF (populate-XOR) |

Default DNP (2026-07): the bias/BLR bypass jumpers **JP_Rf1/JP_Rf2/JP_BLR (R2/R4/R12)** are
DNP (filters + BLR populated), while **JP_BUF (R18) is FITTED** and the entire buffer block is
DNP. When CR-210 is bypassed its rail decoupling is also DNP; the test path (R5/C3/J3) is DNP
if there's no bench charge-injection. (The rail-protection parts F1/F2/D1/D2 are always fitted.)

## Mechanical / stackup
- **4-layer:** F.Cu / In1.Cu = **GND plane** / In2.Cu = **−VDC plane** / B.Cu = **+VDC pour**.
  (Both supply rails get a low-impedance copper area; +VDC pour added because +VDC has no
  inner plane — this is what let FreeRouting route 100 %.)
- Board outline **164 × 90 mm** (standalone single-channel cell; Phase C shrinks/tiles
  per-channel — the **topology**, not this outline, is reused).
- 4× M3 mounting holes. I/O: 4× MCX `CONMCX013` edge jacks, 1× Phoenix MKDS 3-pos screw
  terminal (1715734, 5.08 mm). (MCX `Edge.Cuts` cutouts parked on `Dwgs.User`; restore on
  `Edge.Cuts` when jacks go at the true edge in the GUI.)
- Net classes: `hv_bias` (0.6 mm clear, 0.4 mm track) on `BIAS_IN/SIPM/FE/N_filt`;
  `power` (0.5 mm) on rails; `signal` (0.33 mm) on the amplifier nets; `Default` 0.2 mm.

## Part list pointer — design BOM
- **Design BOM (this board)** = the per-symbol Value/MPN/Manufacturer/Distributor-PN fields
  in `design/channel.kicad_sch`, matched to `../models-bom/single-channel-bom.csv`:
  **45 ref lines → 20 distinct MPNs.** (Was 48/19 in Phase B; 2026-07 delta: −8 × 0.1 µF HF
  caps, +1 JP_BUF, +4 rail-protection parts → 45 refs; +SS14 +1206L010/60WR, −the 0.1 µF-cap
  MPN → 20 MPNs.)
- 2026-07 sourcing (`models-bom/SOURCING-VERIFICATION-2026-07-07.md`): **Cf** swapped off the
  NRND CL21B104KCC5PNC → **CL21B104KCFNNNE** (same 0.1 µF/100 V/X7R/0805); several Digi-Key
  PNs corrected; the **10 µF 25 V bulk (CL21A106KAYNNNE) is Active but currently 0-stock
  (16-wk lead)** — Taiyo Yuden `TMK212BBJ106KG-T` is the in-stock equal-spec alternate.
- Earlier B3 merge/dedup (still in effect): CSP↔shaper internal jacks removed; the two
  board-edge 49.9 Ω collapsed to **one** at `OUT_50`; one 100 µF Nichicon UWT bulk pair;
  power terminal = Phoenix **1715734** (5.08 mm).

## Verified-by
- ERC: `kicad-cli sch erc channel.kicad_sch` = **0 errors / 0 warnings** (re-run after the
  2026-07 rework + rail protection).
- **DRC / schematic-parity: STALE.** The prior "0/0/0, fully autorouted, 207 tracks" describes
  the **pre-rework** PCB; `channel.kicad_pcb` has not been rebuilt against the new netlist
  (buffer bypass, `F1/F2/D1/D2`, `+VDC_F/−VDC_F`). Re-run DRC + `--schematic-parity` after the
  layout rebuild.
- Function (**B2 chan-sim, populated-buffer variant**): gains compound
  ×10.42·×0.998·×1.999·×0.501, peaking ≈ 2.5 µs, OUT_50 = +67.1 mV for 0.5 pC into 50 Ω,
  buffer stable 0 % overshoot, BLR baseline ≤1.2 %. **Default (buffer-bypassed) build** drops
  the ×1.999 buffer term → OUT_50 ≈ +33.5 mV for 0.5 pC (½·SHAPER_OUT into 50 Ω).

## Phase-A blocks consumed — active modules UNCHANGED; support nets reworked (2026-07)
Netlist-audited: the **active Phase-A modules** (CR-112, CR-200, CR-210) keep their exact pin
maps, values and the CR-210 populate-XOR — unchanged. The 2026-07 rework changed the
**support** circuitry around them:
- **csp-cr112:** front-end Rf1/Cf/Rf2/Cc and the CR-112 pin map are as-is. **Test inject
  reworked** — R5 is now a 47 Ω shunt termination to GND + 1 pF (C3) series into `CSP_IN`
  (was 47 Ω series → `TEST_N` → 1 pF). **Decoupling reduced** to 4.7 Ω + 10 µF per rail (the
  0.1 µF HF cap dropped, board-wide).
- **shaper-cr200-cr210:** CR-200 pin map, 200 k P/Z trimpot (sole P/Z), CR-210 BLR with
  JP_BLR populate-XOR — reproduced; same 4.7 Ω + 10 µF decoupling change. The shaper's
  standalone board-edge 49.9 Ω is dropped in the merge; CR-210 `SHAPER_OUT` drives the buffer
  +IN / JP_BUF bypass, and the single 49.9 Ω back-term (`R15`) lives at `OUT_50`.
- **New vs the standalone blocks:** (1) merge join CR-112 `CSP_OUT`→CR-200 in; (2) the
  **optional** THS3491 buffer + JP_BUF bypass on `SHAPER_OUT`; (3) per-rail reverse-polarity
  protection at the power entry; (4) the dedups + support-net reworks above.

## Buffer real parts (B3 gate RESOLVED — Round 2 complete)
| Ref | Role | Value | MPN | Footprint |
|-----|------|-------|-----|-----------|
| **U4** | HV CFA output buffer | THS3491 | **THS3491IDDAT** (TI) | `Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm` |
| **R13** | feedback Rf | 976 Ω 1% | RC0805FR-07976RL (Yageo) | R_0805 |
| **R14** | gain Rg | 976 Ω 1% | RC0805FR-07976RL (Yageo) | R_0805 |
| **R15** | 49.9 Ω back-term | 49.9 Ω 1% | RC0805FR-0749R9L (Yageo) | R_0805 |
| R16/R17 | buffer rail 4.7 Ω | 4.7 Ω | RC0805JR-074R7L (Yageo) | R_0805 |
| C12 (BVP), C13 (BVN) | buffer decoupling | 10 µF 25 V | CL21A106KAYNNNE (Samsung) | C_0805 |

The buffer block (U4, R13/R14, R16/R17, C12/C13) is **DNP by default** — populate to enable
Av=+2 (see the buffer note above); **R15 (49.9 Ω back-term) and J4 stay fitted in both
builds**. The 0.1 µF HF caps were dropped board-wide in the 2026-07 rework.
THS3491 was coordinator-selected over B3's THS3091 primary — both TI HV-CFAs in the same
SOIC-8 PowerPAD footprint with the same Av=+2.

> **Rf/Rg = 976 Ω** (not 1.21 kΩ): the TI **THS3491 datasheet G=+2 recommended feedback
> resistor**, B2-validated against TI's official SPICE model. For a CFA the feedback resistor
> sets loop stability, so the datasheet value governs. Value-only swap (same RC0805 footprint,
> MPN `RC0805FR-07976RL`), done in-place on the routed board — no placement/route change;
> ERC/DRC stayed 0/0/0. Av = 1 + 976/976 = +2 (unchanged).
