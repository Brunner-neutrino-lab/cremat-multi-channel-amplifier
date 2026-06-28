#!/usr/bin/env python
"""B2 chan-sim -- pulse-train BLR proof for the full chain.

Compares the polarity-corrected chain (chain_pulse_train_pol.raw, CR-210 sees the
positive pulse it restores) baseline behaviour, and plots OUT_50 over the train +
the inter-pulse baseline envelope.  Mirrors A5's M2 baseline-restoration result.
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))
from ltspice_raw import read_raw

DATA = os.path.join(HERE, "data")
PLOTS = os.path.join(HERE, "plots")
TPER = 10e-6
T0 = 1e-6


def load(name):
    r = read_raw(os.path.join(DATA, name))
    d = r["data"]
    g = lambda n: [d[k] for k in d if k.lower() == n.lower()][0]
    return g("time"), g("V(out_50)"), g("V(blr_out)"), g("V(shout)")


def per_pulse_peaks(t, y, base):
    pk = []
    for k in range(30):
        t0 = T0 + k * TPER
        m = (t >= t0) & (t < t0 + TPER)
        if np.any(m):
            yy = y[m]
            pk.append((yy[np.argmax(np.abs(yy - base))] - base, t[m][np.argmax(np.abs(yy - base))]))
    return pk


def baseline_before(t, y, base, k):
    t0 = T0 + k * TPER
    i = np.argmin(np.abs(t - (t0 - 0.3e-6)))
    return y[i] - base


def analyze(name, label):
    t, out, blr, sh = load(name)
    base = np.mean(out[t < T0])
    pk = per_pulse_peaks(t, out, base)
    p0, plast = pk[0][0], pk[-1][0]
    bl_late = baseline_before(t, out, base, 29)
    droop = (1 - abs(plast) / abs(p0)) * 100
    res = {
        "label": label,
        "first_pulse_peak_mV": p0 * 1e3,
        "last_pulse_peak_mV": plast * 1e3,
        "peak_droop_pct": droop,
        "late_baseline_mV": bl_late * 1e3,
        "late_baseline_pct_of_peak": bl_late / abs(plast) * 100,
    }
    return (t, out, blr, base, pk), res


def main():
    corr, rc = analyze("chain_pulse_train_pol.raw", "POL=-1 (CR-210 sees positive pulse, corrected)")
    results = [rc]
    # uncorrected, if present
    if os.path.exists(os.path.join(DATA, "chain_pulse_train.raw")):
        unc, ru = analyze("chain_pulse_train.raw", "POL=+1 (uncorrected, real CR-112 polarity)")
        results.append(ru)
    else:
        unc = None

    print("Pulse-train BLR check (100 kHz, 0.5 pC events, full chain):")
    for r in results:
        print("  %s" % r["label"])
        print("    first peak %.2f mV, last peak %.2f mV, droop %.1f%%" %
              (r["first_pulse_peak_mV"], r["last_pulse_peak_mV"], r["peak_droop_pct"]))
        print("    late baseline %.3f mV (%.2f%% of peak)" %
              (r["late_baseline_mV"], r["late_baseline_pct_of_peak"]))

    with open(os.path.join(DATA, "chain_train_fom.json"), "w") as f:
        json.dump(results, f, indent=2)

    # ---- plot: OUT_50 over the train, corrected vs uncorrected ----
    fig, ax = plt.subplots(figsize=(10, 5))
    t, out, blr, base, pk = corr
    ax.plot(t * 1e6, (out - base) * 1e3, "tab:purple", lw=0.9,
            label="OUT_50, corrected polarity (baseline held)")
    if unc is not None:
        tu, outu, blru, baseu, pku = unc
        ax.plot(tu * 1e6, (outu - baseu) * 1e3, "tab:red", lw=0.8, alpha=0.7,
                label="OUT_50, uncorrected polarity (baseline drifts)")
    ax.axhline(0, color="k", lw=0.5, ls=":")
    ax.set_xlabel("time [us]")
    ax.set_ylabel("OUT_50 [mV] (into 50 ohm)")
    ax.set_title("Full chain, 100 kHz train: CR-210 holds OUT_50 baseline at ground "
                 "(correct polarity)")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "chain_train_baseline.png"), dpi=110)
    plt.close(fig)
    print("\nplot -> plots/chain_train_baseline.png ; FoM -> data/chain_train_fom.json")


if __name__ == "__main__":
    main()
