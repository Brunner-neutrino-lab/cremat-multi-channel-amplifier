#!/usr/bin/env python
"""C3 board-sim -- shared-rail channel-to-channel crosstalk (confidence bound).

Method (separates the hard nonlinear solve from the trivial linear rail network):
  1. data/chain_isupply.raw gives ONE channel's REAL supply-current demand I(Vp),I(Vn)
     during a 0.5 pC event (captured on stiff rails -- the proven, convergent chain).
  2. Drive that DYNAMIC current into the SHARED-RAIL network analytically: the single
     100 uF board bulk (+ESR) fed through a pessimistic 100 mohm feed R, with the other
     11 channels modelled as a constant load (their quiescent current is DC -> no AC
     ripple; only the aggressor's DYNAMIC current causes ripple). The shared-node ripple
     is the crosstalk SOURCE seen by every other channel.
  3. Apply the THS3491 PSRR (datasheet) to bound the victim-channel output error, and
     express it as a fraction of the 67 mV/0.5pC OUT_50 full-scale.

Rail-network model (small-signal, per rail), driven by the aggressor's dynamic current
i_ac(t) = I(rail) - quiescent:
        i_ac --> [ shared node Vrip ] --(Cbulk=100u, ESR=30m)--> gnd
                        |__(Rfeed=100m)__ stiff supply (AC ground)
  Vrip(s) = i_ac(s) * Z_par,  Z_par = Rfeed || (ESR + 1/sCbulk).
At the ~2.5 us pulse the cap is a near-short (1/wC ~ 13 mohm at 1/2.5us); Rfeed=100m
dominates only at DC, the cap shunts the AC -> ripple ~= i_ac * (ESR ~ 30 mohm).
We compute Vrip in the time domain by the cap+ESR+Rfeed network ODE for rigor.
"""
import os, sys, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))
from ltspice_raw import read_raw

RAW = os.path.join(HERE, "data", "chain_isupply.raw")
PLOTS = os.path.join(HERE, "plots"); DATA = os.path.join(HERE, "data")
os.makedirs(PLOTS, exist_ok=True)

r = read_raw(RAW); d = r["data"]
def g(n):
    for k in d:
        if k.lower() == n.lower(): return np.asarray(d[k])
    raise KeyError(n)

t = g("time"); ivp = g("I(Vp)"); ivn = g("I(Vn)")
T0 = 1e-6
base = (t > 0.3e-6) & (t < T0)
iq_p = np.mean(ivp[base]); iq_n = np.mean(ivn[base])
# dynamic (AC) component of the aggressor's per-rail current
iac_p = ivp - iq_p
iac_n = ivn - iq_n

# ---- shared-rail network params ----
Cbulk = 100e-6      # single board bulk pair (per rail)
ESR   = 0.03        # bulk ESR (ohm), typical electrolytic/MLCC stack
Rfeed = 0.1         # pessimistic feed R, screw terminal -> far channel (ohm)

def rail_ripple(iac, tt):
    """Vrip across the shared node when dynamic current iac(t) is pulled from a node
    that is (Cbulk in series ESR) to AC-gnd, in parallel with Rfeed to the stiff supply.
    Node eq:  i_cap + i_feed = iac ;  Vrip = i_feed*Rfeed = Vc + i_cap*ESR ; i_cap=Cbulk dVc/dt.
    Solve for Vc by trapezoidal integration, then Vrip = Vc + i_cap*ESR.
    """
    Vc = np.zeros_like(iac); Vrip = np.zeros_like(iac)
    for k in range(1, len(iac)):
        dt = tt[k] - tt[k-1]
        if dt <= 0:
            Vc[k] = Vc[k-1]; Vrip[k] = Vrip[k-1]; continue
        # at node: (Vrip)/Rfeed + Cbulk*dVc/dt = iac ; Vrip = Vc + Cbulk*dVc/dt*ESR
        # let x = dVc/dt. Cbulk*x = i_cap. Vrip = Vc + ESR*Cbulk*x.
        # (Vc + ESR*Cbulk*x)/Rfeed + Cbulk*x = iac
        # x*(ESR*Cbulk/Rfeed + Cbulk) = iac - Vc/Rfeed
        x = (iac[k] - Vc[k-1]/Rfeed) / (ESR*Cbulk/Rfeed + Cbulk)
        Vc[k] = Vc[k-1] + x*dt
        icap = Cbulk * x
        Vrip[k] = Vc[k] + icap*ESR
    return Vrip

vrip_p = rail_ripple(iac_p, t)
vrip_n = rail_ripple(iac_n, t)
m = t >= T0
dvp = vrip_p[m][np.argmax(np.abs(vrip_p[m]))]
dvn = vrip_n[m][np.argmax(np.abs(vrip_n[m]))]
worst = max(abs(dvp), abs(dvn))

# ---- THS3491 PSRR -> victim output error ----
PSRR_dc_dB   = 78.0   # datasheet MIN (PSRR+ 78 / PSRR- 77)
PSRR_band_dB = 50.0   # conservative in-band (~200 kHz) value
def atten(dB): return 10**(-dB/20.0)
FS = 0.067            # OUT_50 full-scale for 0.5 pC
vic_dc   = worst * atten(PSRR_dc_dB)
vic_band = worst * atten(PSRR_band_dB)

# static DC droop on the shared rail from the FULL board quiescent current + Rfeed
Iboard_p = 0.5844  # A, from rail_budget.py
Iboard_n = 0.5364
droop_p = Iboard_p * Rfeed * 1e3   # mV
droop_n = Iboard_n * Rfeed * 1e3

fom = {
    "per_channel_quiescent_+rail_mA": float(abs(iq_p)*1e3),
    "per_channel_quiescent_-rail_mA": float(abs(iq_n)*1e3),
    "aggressor_dynamic_Ipeak_+rail_mA": float((iac_p[m][np.argmax(np.abs(iac_p[m]))])*1e3),
    "aggressor_dynamic_Ipeak_-rail_mA": float((iac_n[m][np.argmax(np.abs(iac_n[m]))])*1e3),
    "shared_rail_dynamic_ripple_+_uV": float(dvp*1e6),
    "shared_rail_dynamic_ripple_-_uV": float(dvn*1e6),
    "shared_rail_dynamic_ripple_worst_uV": float(worst*1e6),
    "static_DC_droop_+rail_mV_at_100mohm_feed": float(droop_p),
    "static_DC_droop_-rail_mV_at_100mohm_feed": float(droop_n),
    "victim_xtalk_at_DC_PSRR_uV": float(vic_dc*1e6),
    "victim_xtalk_at_band_PSRR_uV": float(vic_band*1e6),
    "victim_xtalk_pct_of_FS_band": float(vic_band/FS*100),
    "params": {"Cbulk_uF":100,"ESR_mohm":30,"Rfeed_mohm":100,
               "PSRR_dc_dB":PSRR_dc_dB,"PSRR_band_dB":PSRR_band_dB,"FS_mV":FS*1e3},
}

print("="*72)
print("SHARED-RAIL CROSSTALK -- aggressor dynamic current -> rail ripple -> victim")
print("="*72)
print("Per-channel quiescent draw on +-12V rails (CR-200+CR-210+THS3491, sim):")
print("  +rail %.2f mA   -rail %.2f mA   (CR-112 ~8 mA on its own op-point rail)"
      % (abs(iq_p)*1e3, abs(iq_n)*1e3))
print("Aggressor DYNAMIC current during 0.5 pC event (the crosstalk driver):")
print("  +rail peak %.3f mA   -rail peak %.3f mA"
      % (iac_p[m][np.argmax(np.abs(iac_p[m]))]*1e3, iac_n[m][np.argmax(np.abs(iac_n[m]))]*1e3))
print()
print("Shared 100 uF bulk (ESR 30 mohm) + 100 mohm feed -> dynamic rail RIPPLE:")
print("  +rail %.2f uV   -rail %.2f uV   worst %.2f uV" % (dvp*1e6, dvn*1e6, worst*1e6))
print("Static DC rail droop (full board %.0f/%.0f mA x 100 mohm feed):"
      % (Iboard_p*1e3, Iboard_n*1e3))
print("  +rail %.1f mV   -rail %.1f mV  (a fixed DC offset, identical every channel;" % (droop_p, droop_n))
print("   it does NOT modulate the signal -> not crosstalk, just headroom: 11.9 V left)")
print()
print("Victim crosstalk = rail_ripple x 10^(-PSRR/20):")
print("  at DC PSRR  (%.0f dB): %.4f uV" % (PSRR_dc_dB, vic_dc*1e6))
print("  at band PSRR(%.0f dB): %.4f uV  = %.6f %% of the 67 mV OUT_50 full-scale"
      % (PSRR_band_dB, vic_band*1e6, vic_band/FS*100))
print()
with open(os.path.join(DATA, "xtalk_fom.json"), "w") as f:
    json.dump(fom, f, indent=2)

# ---- plot ----
tus = t*1e6
fig, axs = plt.subplots(3, 1, figsize=(8.5, 8), sharex=True)
axs[0].plot(tus, iac_p*1e3, "tab:red"); axs[0].set_ylabel("aggressor dynamic\n+rail I [mA]")
axs[1].plot(tus, vrip_p*1e6, "tab:orange"); axs[1].set_ylabel("shared +rail\nripple [uV]")
axs[2].plot(tus, vrip_n*1e6, "tab:blue"); axs[2].set_ylabel("shared -rail\nripple [uV]")
for a in axs: a.grid(True, alpha=0.3); a.axvline(1.0, color="k", ls=":", lw=0.6)
axs[2].set_xlabel("time [us]"); axs[0].set_xlim(0, 15)
axs[0].set_title("Shared-rail crosstalk: one aggressor 0.5 pC event, 100 uF bulk, 12x loaded")
fig.tight_layout(); fig.savefig(os.path.join(PLOTS, "xtalk_rail_ripple.png"), dpi=110)
print("plot -> plots/xtalk_rail_ripple.png ; FoM -> data/xtalk_fom.json")
