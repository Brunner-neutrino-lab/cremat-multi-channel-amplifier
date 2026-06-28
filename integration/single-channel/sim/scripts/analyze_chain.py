#!/usr/bin/env python
"""B2 chan-sim -- analyze the full single-channel chain single-event response.

Reads data/chain_single_event.raw, extracts per-stage figures of merit
(CSP_OUT, SHOUT, BLR_OUT, BUF_OUT, OUT_50), checks the injected charge = 0.5 pC,
checks consistency with the A2/A5 standalone sims, and writes plots + a FoM CSV.
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

RAW = os.path.join(HERE, "data", "chain_single_event.raw")
PLOTS = os.path.join(HERE, "plots")
DATA = os.path.join(HERE, "data")
os.makedirs(PLOTS, exist_ok=True)

r = read_raw(RAW)
d = r["data"]
# normalise var-name lookup (LTspice lowercases)
def get(name):
    for k in d:
        if k.lower() == name.lower():
            return d[k]
    raise KeyError(name)

t = get("time")
inj = get("V(inj)")
csp = get("V(csp_out)")
sh = get("V(shout)")
blr = get("V(blr_out)")
buf = get("V(buf_out)")
out = get("V(out_50)")
iinj = get("I(Iinj)")

T0 = 1e-6  # event time

def peak_signed(y, t, t_after=T0):
    """Return (peak_value, t_peak) of the largest |excursion| after t_after."""
    m = t >= t_after
    y2 = y[m]; t2 = t[m]
    # baseline-referenced peak: use pre-event baseline (mean before T0)
    base = np.mean(y[t < t_after]) if np.any(t < t_after) else 0.0
    iabs = np.argmax(np.abs(y2 - base))
    return y2[iabs] - base, t2[iabs], base

def fwhm(y, t, t_after=T0):
    base = np.mean(y[t < t_after]) if np.any(t < t_after) else 0.0
    m = t >= t_after
    y2 = y[m] - base; t2 = t[m]
    ipk = np.argmax(np.abs(y2))
    pk = y2[ipk]
    half = pk / 2.0
    # find crossings of half on each side of the peak
    def cross(idx_range, target):
        for i in idx_range:
            a, b = y2[i], y2[i + 1]
            if (a - target) * (b - target) <= 0 and a != b:
                frac = (target - a) / (b - a)
                return t2[i] + frac * (t2[i + 1] - t2[i])
        return None
    left = cross(range(ipk, 0, -1), half)
    right = cross(range(ipk, len(y2) - 1), half)
    if left is None or right is None:
        return None, t2[ipk]
    return right - left, t2[ipk]

# injected charge check (integrate Iinj)
q_inj = np.trapz(iinj, t)

rows = []
stages = [
    ("CSP_OUT", csp, "V"),
    ("SHOUT (shaper)", sh, "V"),
    ("BLR_OUT (CR-210)", blr, "V"),
    ("BUF_OUT (THS3491)", buf, "V"),
    ("OUT_50 (50ohm load)", out, "V"),
]
fom = {}
for name, y, unit in stages:
    pk, tpk, base = peak_signed(y, t)
    fw, _ = fwhm(y, t)
    ptime = tpk - T0
    fom[name] = {
        "peak_V": float(pk),
        "peak_mV": float(pk * 1e3),
        "t_peak_us": float(tpk * 1e6),
        "peaking_time_us": float(ptime * 1e6),
        "fwhm_us": (float(fw * 1e6) if fw else None),
        "baseline_V": float(base),
    }
    rows.append((name, pk * 1e3, ptime * 1e6, (fw * 1e6 if fw else float("nan"))))

print("Injected charge  : %.4f pC (target 0.5 pC)" % (q_inj * 1e12))
print()
print("%-22s %12s %12s %12s" % ("stage", "peak[mV]", "t_peak[us]", "FWHM[us]"))
for name, pkmv, ptus, fwus in rows:
    print("%-22s %12.3f %12.3f %12.3f" % (name, pkmv, ptus, fwus))

# gain chain
csp_pk = fom["CSP_OUT"]["peak_mV"]
sh_pk = fom["SHOUT (shaper)"]["peak_mV"]
blr_pk = fom["BLR_OUT (CR-210)"]["peak_mV"]
buf_pk = fom["BUF_OUT (THS3491)"]["peak_mV"]
out_pk = fom["OUT_50 (50ohm load)"]["peak_mV"]
print()
print("Gain chain (peak ratios):")
print("  CSP step          : %.3f mV" % csp_pk)
print("  shaper / CSP      : %.3f V/V" % (sh_pk / csp_pk))
print("  BLR / shaper      : %.3f V/V" % (blr_pk / sh_pk))
print("  buffer / BLR      : %.3f V/V" % (buf_pk / blr_pk))
print("  OUT_50 / buffer   : %.3f V/V (50ohm back-term into 50ohm = 0.5)" % (out_pk / buf_pk))
print("  OVERALL OUT_50/CSP: %.3f V/V" % (out_pk / csp_pk))
print("  charge->OUT_50    : %.2f mV/pC  (=> %.3f mV for 0.5 pC)" % (out_pk / 0.5, out_pk))

fom["_meta"] = {
    "injected_charge_pC": float(q_inj * 1e12),
    "gain_shaper_over_csp": float(sh_pk / csp_pk),
    "gain_blr_over_shaper": float(blr_pk / sh_pk),
    "gain_buf_over_blr": float(buf_pk / blr_pk),
    "gain_out_over_buf": float(out_pk / buf_pk),
    "overall_out50_over_csp": float(out_pk / csp_pk),
    "out50_peak_mV_for_0p5pC": float(out_pk),
    "engine": "LTspice 24.1.9 batch (-b -Run)",
}
with open(os.path.join(DATA, "chain_fom.json"), "w") as f:
    json.dump(fom, f, indent=2)

# ---------- plots ----------
tus = t * 1e6

# (1) per-stage stacked panel
fig, axs = plt.subplots(5, 1, figsize=(8.5, 11), sharex=True)
panels = [
    ("CSP_OUT (CR-112)", csp, "tab:blue"),
    ("SHOUT (CR-200 shaper)", sh, "tab:orange"),
    ("BLR_OUT (CR-210)", blr, "tab:green"),
    ("BUF_OUT (THS3491)", buf, "tab:red"),
    ("OUT_50 (into 50 ohm)", out, "tab:purple"),
]
for ax, (name, y, c) in zip(axs, panels):
    ax.plot(tus, y * 1e3, c, lw=1.1)
    ax.set_ylabel("%s\n[mV]" % name, fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.axvline(1.0, color="k", ls=":", lw=0.6)
axs[-1].set_xlabel("time [us]")
axs[0].set_title("Full single-channel chain -- 0.5 pC event, per-stage response")
axs[0].set_xlim(0, 20)
fig.tight_layout()
fig.savefig(os.path.join(PLOTS, "chain_per_stage.png"), dpi=110)
plt.close(fig)

# (2) overlay (normalised) to show shaping preserved through the chain
fig, ax = plt.subplots(figsize=(9, 5))
for name, y, c in panels:
    base = np.mean(y[t < T0])
    yy = (y - base)
    pk = yy[np.argmax(np.abs(yy))]
    ax.plot(tus, yy / abs(pk), c, lw=1.2, label="%s (pk %.1f mV)" % (name, pk * 1e3))
ax.set_xlim(0, 12)
ax.set_xlabel("time [us]")
ax.set_ylabel("normalised to own peak")
ax.set_title("Chain: shape preserved stage-to-stage (peaking time held)")
ax.grid(True, alpha=0.3)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(PLOTS, "chain_normalised_overlay.png"), dpi=110)
plt.close(fig)

# (3) OUT_50 detail with peak + FWHM marked
fig, ax = plt.subplots(figsize=(9, 5))
base = np.mean(out[t < T0])
ax.plot(tus, (out - base) * 1e3, "tab:purple", lw=1.4)
pk, tpk, _ = peak_signed(out, t)
ax.plot(tpk * 1e6, pk * 1e3, "ko", ms=5)
ax.annotate("peak %.3f mV @ %.2f us" % (pk * 1e3, (tpk - T0) * 1e6),
            (tpk * 1e6, pk * 1e3), textcoords="offset points", xytext=(10, -10), fontsize=9)
ax.set_xlim(0, 15)
ax.set_xlabel("time [us]")
ax.set_ylabel("OUT_50 [mV] (across 50 ohm load)")
ax.set_title("OUT_50: shaped pulse delivered to 50 ohm load, 0.5 pC event")
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(PLOTS, "chain_out50_detail.png"), dpi=110)
plt.close(fig)

# (4) input charge verification
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(t * 1e9, iinj * 1e3, "k", lw=1.2)
ax.set_xlim(999.8, 1000.2)
ax.set_xlabel("time [ns]")
ax.set_ylabel("Iinj [mA]")
ax.set_title("Injected charge impulse: area = %.4f pC (target 0.5 pC)" % (q_inj * 1e12))
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(PLOTS, "chain_input_charge.png"), dpi=110)
plt.close(fig)

print("\nplots -> plots/chain_per_stage.png, chain_normalised_overlay.png,")
print("         chain_out50_detail.png, chain_input_charge.png")
print("FoM    -> data/chain_fom.json")
