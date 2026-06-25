#!/usr/bin/env python
"""A5 shaper-sim M1 analysis: CR-200-1us single-event response.

Reads decks/m1_cr200.raw, computes figures of merit for the as-built (P/Z=51k) channel
and the no-P/Z / low-P/Z comparison cases, and saves plots in plots/.
FOM: peak amplitude, gain (peak/Vstep), peaking time (step->peak), FWHM, undershoot.
"""
import sys, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "scripts"))
from ltspice_raw import read_raw

T0 = 1e-6      # step time
VSTEP = 6.5e-3 # CSP step (0.5 pC * 13 mV/pC)
TAU = 1e-6     # CR-200-1us shaping time
FWHM_SPEC = 2.4e-6


def fwhm(t, y):
    """FWHM about the positive peak via linear interpolation of the half-max crossings."""
    ipk = int(np.argmax(y))
    ymax = y[ipk]
    half = ymax / 2.0
    # left crossing
    li = ipk
    while li > 0 and y[li] > half:
        li -= 1
    if li == ipk:
        tl = t[ipk]
    else:
        tl = np.interp(half, [y[li], y[li + 1]], [t[li], t[li + 1]])
    # right crossing
    ri = ipk
    while ri < len(y) - 1 and y[ri] > half:
        ri += 1
    if ri == ipk:
        tr = t[ipk]
    else:
        tr = np.interp(half, [y[ri], y[ri - 1]], [t[ri], t[ri - 1]])
    return tr - tl, tl, tr, ymax, t[ipk]


def fom(t, y, label):
    ipk = int(np.argmax(y))
    ymax = y[ipk]; tpk = t[ipk]
    width, tl, tr, _, _ = fwhm(t, y)
    peaking = tpk - T0
    # undershoot = most-negative excursion after the peak, as % of peak
    post = y[t > tpk]
    umin = post.min() if len(post) else 0.0
    upct = 100.0 * umin / ymax if ymax else 0.0
    print(f"[{label}]")
    print(f"  peak amplitude   = {ymax*1e3:8.3f} mV   (gain = {ymax/VSTEP:6.2f} V/V from {VSTEP*1e3:.2f} mV step)")
    print(f"  peaking time     = {peaking*1e6:8.3f} us  (step->peak; shaping tau = {TAU*1e6:.2f} us)")
    print(f"  FWHM             = {width*1e6:8.3f} us  (datasheet spec {FWHM_SPEC*1e6:.2f} us = 2.4*tau)")
    print(f"  undershoot       = {umin*1e3:8.3f} mV  ({upct:+.2f} % of peak)")
    return dict(ymax=ymax, tpk=tpk, peaking=peaking, fwhm=width, umin=umin, upct=upct,
                gain=ymax / VSTEP, tl=tl, tr=tr)


def main():
    r = read_raw(str(SIM / "decks" / "m1_cr200.raw"))
    d = r["data"]; t = d["time"]
    csp = d["V(csp)"]
    opz = d["V(outpz)"]; onop = d["V(outnop)"]; olow = d["V(outlow)"]

    print("=== M1 CR-200-1us figures of merit ===")
    print(f"CSP stimulus: step {csp.max()*1e3:.3f} mV (target 6.5), decay tau 51 us\n")
    f_pz  = fom(t, opz,  "CR-200 + P/Z 51k (as-built)")
    f_nop = fom(t, onop, "CR-200, NO P/Z (open)")
    f_low = fom(t, olow, "CR-200 + P/Z 10k (too low)")

    tus = t * 1e6
    # --- Plot 1: the as-built channel: CSP input vs shaped output ---
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(tus, csp * 1e3, color="tab:gray", lw=1.4, label="CSP input (6.5 mV, tau=51us)")
    ax1.set_xlabel("time (us)"); ax1.set_ylabel("CSP input (mV)", color="tab:gray")
    ax1.tick_params(axis="y", labelcolor="tab:gray")
    ax2 = ax1.twinx()
    ax2.plot(tus, opz * 1e3, color="tab:blue", lw=1.8, label="CR-200 output (P/Z 51k)")
    ax2.axhline(0, color="k", lw=0.5)
    ax2.plot(f_pz["tpk"] * 1e6, f_pz["ymax"] * 1e3, "o", color="tab:red")
    ax2.annotate(f"peak {f_pz['ymax']*1e3:.1f} mV\n@ {f_pz['peaking']*1e6:.2f} us\nFWHM {f_pz['fwhm']*1e6:.2f} us",
                 (f_pz["tpk"] * 1e6, f_pz["ymax"] * 1e3), textcoords="offset points",
                 xytext=(12, -6), fontsize=8, color="tab:red")
    ax2.hlines(f_pz["ymax"] * 1e3 / 2, f_pz["tl"] * 1e6, f_pz["tr"] * 1e6,
               color="tab:green", lw=1.2, linestyles="--", label="FWHM")
    ax2.set_ylabel("CR-200 output (mV)", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    lines = ax1.get_lines() + ax2.get_lines()[:1]
    ax1.legend(lines, [l.get_label() for l in lines], loc="upper right", fontsize=8)
    plt.title("M1: CR-200-1us shaped Gaussian response to a 0.5 pC CSP event")
    fig.tight_layout()
    p1 = SIM / "plots" / "m1_cr200_gaussian.png"
    fig.savefig(p1, dpi=130); plt.close(fig)
    print(f"\nsaved {p1}")

    # --- Plot 2: P/Z effect (overlay 3 cases) ---
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(tus, opz * 1e3, lw=1.8, label=f"P/Z 51k (correct): undershoot {f_pz['upct']:+.1f}%")
    ax.plot(tus, onop * 1e3, lw=1.4, label=f"No P/Z: undershoot {f_nop['upct']:+.1f}%")
    ax.plot(tus, olow * 1e3, lw=1.4, label=f"P/Z 10k (too low): undershoot {f_low['upct']:+.1f}%")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("time (us)"); ax.set_ylabel("CR-200 output (mV)")
    ax.set_title("M1: pole-zero cancellation removes long-tail undershoot")
    ax.legend(fontsize=8, loc="upper right"); fig.tight_layout()
    p2 = SIM / "plots" / "m1_polezero_effect.png"
    fig.savefig(p2, dpi=130); plt.close(fig)
    print(f"saved {p2}")

    # save numeric FOM
    import json
    out = {k: {kk: float(vv) for kk, vv in v.items()} for k, v in
           dict(pz=f_pz, nop=f_nop, low=f_low).items()}
    (SIM / "data" / "m1_fom.json").write_text(json.dumps(out, indent=2))
    print(f"saved {SIM/'data'/'m1_fom.json'}")


if __name__ == "__main__":
    main()
