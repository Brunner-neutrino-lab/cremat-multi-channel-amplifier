#!/usr/bin/env python
"""behavioral_crosscheck.py -- independent analytical CR-112 CSP model.

§5 requires a behavioral model as a fallback / cross-check against the
Cremat-derived SPICE deck. This is a from-datasheet closed-form model with NO
dependence on the SPICE netlist:

  CSP_OUT(t) for an ideal charge impulse Q at t0 is the classic CSP step-with-
  decay shaped by a finite rise:
      v(t) = -(Q/Cf) * (1 - exp(-(t-t0)/tau_r)) * exp(-(t-t0)/tau_d)   for t>t0
  with
      Cf = 75 pF, Rf = 680 k  -> charge gain 1/Cf = 13.33 mV/pC, tau_d = Rf*Cf = 51 us
      tau_r chosen so 10-90% rise = 3 ns (datasheet)  -> tau_r = 3ns/ln(9) = 1.366 ns

Outputs the analytic FoM and overlays the SPICE CSP_OUT (if its CSV exists) so
the two can be compared. Writes plots/behavioral_overlay.png and prints a table.
"""
import os, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIM = os.path.dirname(os.path.abspath(__file__))

# ---- datasheet parameters ----
Q   = 0.5e-12          # C, injected charge
Cf  = 75e-12           # F
Rf  = 680e3            # ohm
tau_d = Rf * Cf        # decay time constant = 51 us
tr_10_90 = 3e-9        # datasheet rise time
tau_r = tr_10_90 / np.log(9.0)   # single-pole rise -> tau_r = 1.366 ns
gain  = 1.0 / Cf       # V per C = 13.33 mV/pC
t0    = 1e-6

# ---- analytic waveform ----
t = np.linspace(0, 300e-6, 600001)
v = np.zeros_like(t)
m = t >= t0
dt = t[m] - t0
v[m] = -(Q / Cf) * (1.0 - np.exp(-dt / tau_r)) * np.exp(-dt / tau_d)

peak = v[np.argmax(np.abs(v))]
gain_mV_pC = peak * 1e3 / (Q * 1e12)

# 10-90 rise on analytic curve
ys = -v  # positive-going
pk = ys.max()
tt = t[m]; yy = ys[m]
def cross(level):
    for i in range(1, len(yy)):
        if yy[i-1] < level <= yy[i]:
            return tt[i-1] + (level-yy[i-1])*(tt[i]-tt[i-1])/(yy[i]-yy[i-1])
    return np.nan
tr = cross(0.9*pk) - cross(0.1*pk)

print("=== Behavioral (analytic) CR-112 cross-check ===")
print("  charge gain        %.3f mV/pC   (datasheet 13)" % gain_mV_pC)
print("  peak amplitude     %.3f mV      (target ~6.5)" % (peak*1e3))
print("  rise time 10-90%%   %.3f ns      (datasheet ~3)" % (tr*1e9))
print("  decay tau          %.2f us      (Rf*Cf = 51)" % (tau_d*1e6))

# ---- overlay with the SPICE result if available ----
csv = os.path.join(SIM, "data", "cr11x_csp_csp_out.csv")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
ax1.plot((t-t0)*1e9, v*1e3, label="behavioral", color="tab:green")
ax2.plot(t*1e6, v*1e3, label="behavioral", color="tab:green")
sp = None
if os.path.exists(csv):
    sp = np.loadtxt(csv, delimiter=",", skiprows=1)
    ax1.plot((sp[:,0]-t0)*1e9, sp[:,1]*1e3, "--", label="SPICE (Cremat-derived)", color="tab:blue")
    ax2.plot(sp[:,0]*1e6, sp[:,1]*1e3, "--", label="SPICE (Cremat-derived)", color="tab:blue")
ax1.set_xlim(-1, 15); ax1.set_xlabel("time after pulse (ns)"); ax1.set_ylabel("CSP_OUT (mV)")
ax1.set_title("Rise comparison"); ax1.grid(alpha=0.3); ax1.legend(fontsize=8)
ax2.set_xlabel("time (us)"); ax2.set_ylabel("CSP_OUT (mV)")
ax2.set_title("Decay comparison"); ax2.grid(alpha=0.3); ax2.legend(fontsize=8)
fig.suptitle("CR-112 0.5 pC: behavioral vs Cremat-derived SPICE")
fig.tight_layout()
fig.savefig(os.path.join(SIM, "plots", "behavioral_overlay.png"), dpi=130)
plt.close(fig)

# numeric agreement
if sp is not None:
    sp_peak = sp[:,1][np.argmax(np.abs(sp[:,1]))]
    print("  --- agreement vs SPICE ---")
    print("  SPICE peak %.3f mV vs behavioral %.3f mV  -> %.2f%% diff"
          % (sp_peak*1e3, peak*1e3, abs(sp_peak-peak)/abs(peak)*100))
