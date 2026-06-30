#!/usr/bin/env python
"""C3 board-sim -- shared-rail loading / decoupling / bulk adequacy for the 12-ch board.

Computes the total +-12 V supply current for 12 channels from datasheet quiescent
currents, the IR drop across each part's 4.7 ohm series decoupling resistor at 12x
context (the drop is PER-CHANNEL -- the 4.7 ohm only carries one part's current --
plus a separate check of the shared feed), and assesses bulk-cap adequacy for a
single-event charge demand and for the per-rail droop.

All quiescent currents are PER RAIL (current drawn from each of +12 V / -12 V).
Sources (retrieval in SESSION_LOG):
  CR-112 : Cremat CR-112-R2.1 datasheet, "Power supply current" ~5 mA/rail @ Vs=+-6V;
           rises with Vs.  No-load power dissipation 70 mW. Use 8 mA/rail @ +-12 V
           (conservative: power-dissipation curve ~doubles 6V->12V; CR-110 sibling
           shows ~9 mA @ Vs=13).
  CR-200 : Cremat CR-200-R2.1, "quiescent power supply current" 7 mA/rail @ Vs=+-13 V.
  CR-210 : Cremat CR-210-R0, "Power supply current" pos 17 mA, neg 13 mA @ Vs=+-13 V
           (ASYMMETRIC -- the +rail is the heaviest single load on the board).
  THS3491: TI SBOS875C, IQ typ 16.7 mA @ +-15 V (16.8 trimmed), 15.8 mA @ +-7 V;
           use 16.7 mA/rail (symmetric, no-load quiescent). Output drive transient
           handled separately by the bulk-cap charge check.
"""

N = 12  # channels

# ---- per-rail quiescent currents [mA], (pos_rail, neg_rail) ----
parts = {
    # name         I_pos   I_neg   note
    "CR-112 CSP":   (8.0,   8.0,  "datasheet ~5 mA @ +-6V; 8 mA conservative @ +-12V"),
    "CR-200 shaper":(7.0,   7.0,  "datasheet quiescent 7 mA @ Vs=+-13V"),
    "CR-210 BLR":   (17.0, 13.0,  "datasheet pos 17 / neg 13 mA @ Vs=+-13V (asymmetric)"),
    "THS3491 buf":  (16.7, 16.7,  "TI IQ typ 16.7 mA @ +-15V; ~16.3 @ +-12V"),
}

Rdecouple = 4.7   # ohm, per-part per-rail series decoupling resistor
Vrail = 12.0      # V nominal

print("=" * 74)
print("12-CHANNEL SHARED-RAIL LOADING  (per-rail quiescent currents, datasheet)")
print("=" * 74)
print("%-16s %8s %8s   %-s" % ("part", "+rail/mA", "-rail/mA", "note"))
ipos_ch = ineg_ch = 0.0
for name, (ip, ino, note) in parts.items():
    print("%-16s %8.1f %8.1f   %s" % (name, ip, ino, note))
    ipos_ch += ip
    ineg_ch += ino
print("-" * 74)
print("%-16s %8.1f %8.1f   PER CHANNEL" % ("SUBTOTAL", ipos_ch, ineg_ch))

ipos_12 = ipos_ch * N
ineg_12 = ineg_ch * N
print("%-16s %8.1f %8.1f   x12 CHANNELS (board total quiescent)" % ("TOTAL", ipos_12, ineg_12))
print()
print("Board quiescent supply current:  +12V rail = %.0f mA (%.2f A)" % (ipos_12, ipos_12/1000))
print("                                 -12V rail = %.0f mA (%.2f A)" % (ineg_12, ineg_12/1000))
print("Total board power (both rails)  = %.2f W" % ((ipos_12+ineg_12)/1000.0 * Vrail))
print()

# ---- IR drop across the 4.7 ohm PER-PART decoupling R (carries ONE part's current) ----
print("=" * 74)
print("IR DROP across each 4.7 ohm series decoupling R (per part, NOT shared)")
print("  The 4.7 ohm sits in each part's own rail feed -> it carries only that")
print("  part's current, INDEPENDENT of channel count. 12x does NOT raise it.")
print("=" * 74)
print("%-16s %10s %10s" % ("part", "Vdrop+/mV", "Vdrop-/mV"))
worst = 0.0
for name, (ip, ino, note) in parts.items():
    dvp = ip/1000.0 * Rdecouple * 1000  # mV
    dvn = ino/1000.0 * Rdecouple * 1000
    worst = max(worst, dvp, dvn)
    print("%-16s %10.1f %10.1f" % (name, dvp, dvn))
print("-" * 74)
print("Worst-case single-part decoupling drop = %.1f mV (%.2f%% of 12 V)" % (worst, worst/Vrail/10))
print("  -> local rail at that part = %.3f V.  CR-11X min Vs = +-6 V; THS3491" % (Vrail - worst/1000))
print("     headroom is on OUTPUT swing (<=+-0.2 V signal), not the rail. AMPLE.")
print()

# ---- IR drop on the SHARED board feed (trace/plane from screw terminal to channels) ----
print("=" * 74)
print("IR DROP on the SHARED rail feed (screw terminal -> channels, on the plane)")
print("=" * 74)
# the shared copper carries the FULL board current; estimate worst (+rail) plane drop.
# 4-layer: -VDC on In2 plane, +VDC on B.Cu pour. Use a conservative lumped feed R.
# 1 oz copper, ~35 um; sheet R ~0.5 mohm/square. A pour the length of the board
# (~12 channel rows, ~220 mm) with width ~ board width is many squares wide ->
# << 10 mohm end-to-end. Take a pessimistic 50 mohm lumped feed R to the far channel.
for Rfeed_mohm in (20, 50, 100):
    dv = ipos_12/1000.0 * Rfeed_mohm/1000.0 * 1000  # mV
    print("  Rfeed=%3d mohm -> +rail feed drop at far channel = %.1f mV (%.3f%%)"
          % (Rfeed_mohm, dv, dv/Vrail/10))
print("  +VDC pour (B.Cu) has no full inner plane -> the +rail (heavier, 17 mA CR-210)")
print("  is the one to watch; a pour still gives mohm-scale R. Drop is sub-100 mV.")
print()

# ---- bulk-cap adequacy: per-event charge demand vs 100 uF board bulk + 10 uF/channel
print("=" * 74)
print("BULK-CAP ADEQUACY")
print("=" * 74)
Cbulk = 100e-6     # board bulk pair (one per rail), shared
Cch   = 10e-6      # per-channel per-rail local bulk (x12 = 120 uF distributed)
Cper_part = 10e-6  # actually each PART has its own 10 uF -> 4 parts/channel
Clocal_total = Cper_part * 4 * N  # all local 10 uF caps on one rail
print("Board bulk (per rail)            : %.0f uF (1 pair, shared)" % (Cbulk*1e6))
print("Per-part local bulk              : 10 uF x 4 parts x 12 ch = %.0f uF distributed" % (Clocal_total*1e6))
print("Total rail decoupling capacitance: %.0f uF" % ((Cbulk+Clocal_total)*1e6))
print()

# (a) single-event dynamic charge demand from the THS3491 driving 50 ohm
# OUT_50 peak 67 mV into 50 ohm -> buffer output 134 mV; transient load current is tiny.
Vbuf_pk = 0.134
Iload_pk = Vbuf_pk / (49.9+50)  # A, through back-term + load
tpulse = 2.5e-6
Qevent = Iload_pk * tpulse      # rough charge per single event from one channel
print("Single-event dynamic demand (one channel):")
print("  buffer out peak %.0f mV -> load I_pk = %.2f mA, ~%.1f us wide" % (Vbuf_pk*1e3, Iload_pk*1e3, tpulse*1e6))
print("  charge per event Q ~= %.3f nC" % (Qevent*1e9))
dV_event = Qevent / Cch
print("  if served entirely by the 10 uF local cap: dV = Q/C = %.3f mV  (negligible)" % (dV_event*1e3))
print()

# (b) all 12 channels firing simultaneously (worst correlated case)
Q12 = Qevent * N
dV12_local = Q12 / (Cch*N)   # each channel's local cap serves its own channel
dV12_bulk  = Q12 / Cbulk
print("All 12 channels firing at once (worst correlated transient):")
print("  total event charge = %.2f nC" % (Q12*1e9))
print("  served by distributed local caps (10 uF/ch): dV = %.3f mV" % (dV12_local*1e3))
print("  served by 100 uF board bulk alone:           dV = %.3f mV" % (dV12_bulk*1e3))
print()

# (c) static rail droop from quiescent current is set by the SUPPLY regulation, not C.
# The caps only matter for the LF/HF transient; quiescent draw (0.59 A +rail) is a DC
# load the bench supply must source. Check it's within a typical +-12 V lab/brick supply.
print("Static check: %.0f mA / %.0f mA quiescent is a DC load (supply must source it)."
      % (ipos_12, ineg_12))
print("  A typical +-12 V supply (>=1 A/rail) covers it with margin; 0.7 W..7 W class.")
print()
print("VERDICT: see SESSION_REPORT.md")
