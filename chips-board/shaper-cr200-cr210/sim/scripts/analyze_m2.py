#!/usr/bin/env python
"""A5 shaper-sim M2 analysis: CR-210 baseline restoration vs JU1 bypass.

Reads decks/m2_blr.raw (pulse train, 100 kHz). For the BLR-OFF (AC-coupled bypass) and
BLR-ON (CR-210) paths, tracks the inter-pulse baseline (valley envelope) over time to show
that AC coupling depresses the baseline while the CR-210 holds it near ground.
"""
import sys, pathlib, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "scripts"))
from ltspice_raw import read_raw

TPER = 10e-6  # 100 kHz


def baseline_envelope(t, y):
    """Per-period minimum (the inter-pulse baseline) and its time."""
    tb, yb = [], []
    n = int(np.floor(t[-1] / TPER))
    for k in range(1, n):  # skip first incomplete period
        m = (t >= k * TPER + 6e-6) & (t < (k + 1) * TPER)  # window in the tail, away from peak
        if m.sum() > 2:
            seg = y[m]
            tb.append((k + 0.8) * TPER)
            yb.append(seg.min())
    return np.array(tb), np.array(yb)


def main():
    r = read_raw(str(SIM / "decks" / "m2_blr.raw"))
    d = r["data"]; t = d["time"]
    byp = d["V(out_off)"]   # BLR OFF (AC-coupled, no restorer)
    blr = d["V(out_on)"]    # BLR ON (CR-210)
    # ignore the supply turn-on transient
    keep = t > 30e-6
    t = t[keep]; byp = byp[keep]; blr = blr[keep]

    tb_off, base_off = baseline_envelope(t, byp)
    tb_on, base_on = baseline_envelope(t, blr)

    # steady-state baseline = mean over the last 20% of the run
    def ss(tb, base):
        sel = tb > 0.8 * t[-1]
        return base[sel].mean() if sel.any() else base[-1]
    ss_off = ss(tb_off, base_off)
    ss_on = ss(tb_on, base_on)
    # un-drooped reference = early (first ~few-pulse) peak of the BLR-off path
    pk_off = byp[t < t[0] + 5 * TPER].max()

    print("=== M2 baseline restoration figures of merit (100 kHz train) ===")
    print(f"early pulse peak (BLR off, reference)   = {pk_off*1e3:8.3f} mV")
    print(f"steady-state baseline, BLR OFF (no BLR) = {ss_off*1e3:8.3f} mV  "
          f"({100*ss_off/pk_off:+.1f} % of peak)")
    print(f"steady-state baseline, BLR ON  (CR-210) = {ss_on*1e3:8.3f} mV  "
          f"({100*ss_on/pk_off:+.1f} % of peak)")
    improvement = abs(ss_off) - abs(ss_on)
    print(f"baseline droop removed by CR-210        = {improvement*1e3:8.3f} mV  "
          f"({100*improvement/abs(ss_off):.0f} % reduction in droop)")

    tms = t * 1e3
    # peak envelope (per-period max) for a clean overlay that isn't a solid block
    def peak_env(y):
        tp, yp = [], []
        n = int(np.floor((t[-1] - t[0]) / TPER))
        for k in range(n):
            m = (t >= t[0] + k * TPER) & (t < t[0] + (k + 1) * TPER)
            if m.sum() > 1:
                tp.append(t[0] + (k + 0.35) * TPER); yp.append(y[m].max())
        return np.array(tp), np.array(yp)
    tp_off, pe_off = peak_env(byp)
    tp_on, pe_on = peak_env(blr)

    # --- Plot: peak + baseline envelopes (clean) ---
    fig, (axw, axb) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)
    axw.plot(tp_off * 1e3, pe_off * 1e3, lw=1.4, color="tab:orange",
             label="BLR OFF peak (JU1 short: AC-coupled, no restorer)")
    axw.plot(tp_on * 1e3, pe_on * 1e3, lw=1.4, color="tab:blue",
             label="BLR ON peak (JU1 open: through CR-210)")
    axw.axhline(0, color="k", lw=0.5)
    axw.set_ylabel("per-pulse PEAK (mV)")
    axw.set_title("M2: CR-210 holds pulse height; without BLR the peak sinks with the baseline")
    axw.legend(fontsize=8, loc="center right")

    axb.plot(tb_off * 1e3, base_off * 1e3, "-o", ms=2, color="tab:orange",
             label=f"BLR OFF baseline -> {ss_off*1e3:.2f} mV ({100*ss_off/pk_off:+.0f}%)")
    axb.plot(tb_on * 1e3, base_on * 1e3, "-o", ms=2, color="tab:blue",
             label=f"BLR ON baseline -> {ss_on*1e3:.2f} mV ({100*ss_on/pk_off:+.0f}%)")
    axb.axhline(0, color="k", lw=0.5)
    axb.set_xlabel("time (ms)"); axb.set_ylabel("inter-pulse baseline (mV)")
    axb.set_title("Inter-pulse baseline: AC coupling droops, CR-210 holds it at ground")
    axb.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    p = SIM / "plots" / "m2_baseline_restoration.png"
    fig.savefig(p, dpi=130); plt.close(fig)
    print(f"\nsaved {p}")

    # --- Zoom plot: a few pulses early vs late to show droop shape ---
    fig, ax = plt.subplots(figsize=(9, 4))
    early = (t > t[0]) & (t < t[0] + 5 * TPER)
    late = (t > t[-1] - 5 * TPER)
    ax.plot((t[early] - t[0]) * 1e6, byp[early] * 1e3, color="tab:orange", lw=1,
            label="BLR OFF, early (baseline ~0)")
    ax.plot((t[late] - (t[-1] - 5 * TPER)) * 1e6, byp[late] * 1e3, color="tab:red", lw=1,
            label="BLR OFF, late (baseline depressed)")
    ax.plot((t[late] - (t[-1] - 5 * TPER)) * 1e6, blr[late] * 1e3, color="tab:blue", lw=1,
            label="BLR ON, late (restored)")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("time within 5-pulse window (us)"); ax.set_ylabel("output (mV)")
    ax.set_title("M2: pulse-shape detail -- baseline depression vs CR-210 restoration")
    ax.legend(fontsize=8)
    fig.tight_layout()
    p2 = SIM / "plots" / "m2_pulse_detail.png"
    fig.savefig(p2, dpi=130); plt.close(fig)
    print(f"saved {p2}")

    out = dict(first_pulse_peak_mV=float(pk_off * 1e3),
               baseline_off_mV=float(ss_off * 1e3),
               baseline_on_mV=float(ss_on * 1e3),
               droop_off_pct=float(100 * ss_off / pk_off),
               droop_on_pct=float(100 * ss_on / pk_off),
               droop_removed_pct=float(100 * improvement / abs(ss_off)))
    (SIM / "data" / "m2_fom.json").write_text(json.dumps(out, indent=2))
    print(f"saved {SIM/'data'/'m2_fom.json'}")


if __name__ == "__main__":
    main()
