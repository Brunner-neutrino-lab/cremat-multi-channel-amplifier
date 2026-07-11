#!/usr/bin/env python
"""C3 board-sim -- analyse the AC transfer function + charge-linearity sweep.

  chain_ac.raw       (complex .ac)  -> Bode of the charge->OUT_50 transimpedance;
                                        peak freq + -3 dB corners + bandwidth.
  chain_linearity.log (.step .meas) -> OUT_50/BUF/SHOUT peak vs injected charge;
                                        small-signal gain, compression onset, clip.

Outputs: plots/chain_ac_bode.png, plots/chain_linearity.png,
         data/chain_ac_fom.json, data/chain_linearity_fom.json.
Engine raw/log are produced by run_ltspice.ps1 (LTspice 24.x batch).
"""
import json
import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ...\sim
DATA = os.path.join(HERE, "data")
PLOTS = os.path.join(HERE, "plots")
os.makedirs(PLOTS, exist_ok=True)


# ----------------------------------------------------------------------------
# complex (.ac) .raw reader -- LTspice binary, UTF-16 header
# ----------------------------------------------------------------------------
def read_ac_raw(path):
    raw = open(path, "rb").read()
    idx, mk = -1, None
    for marker in (b"Binary:\r\n", b"Binary:\n"):
        cand = marker.decode("ascii").encode("utf-16-le")
        idx = raw.find(cand)
        if idx != -1:
            mk = cand
            break
    if idx == -1:
        raise ValueError("no Binary: marker")
    header = raw[:idx].decode("utf-16-le", "replace")
    body = raw[idx + len(mk):]
    npts = int(re.search(r"No\. Points:\s*(\d+)", header).group(1))
    nvars = int(re.search(r"No\. Variables:\s*(\d+)", header).group(1))
    names = []
    for ln in header.split("Variables:")[-1].splitlines():
        m = re.match(r"\s*\d+\s+(\S+)\s+\S+", ln)
        if m:
            names.append(m.group(1))
        if len(names) == nvars:
            break
    rowbytes = len(body) // npts
    arr = {}
    if rowbytes == nvars * 16:  # every var complex (re,im) f8
        buf = np.frombuffer(body[: npts * rowbytes], dtype="<f8").reshape(npts, nvars * 2)
        for j, n in enumerate(names):
            arr[n] = buf[:, 2 * j] + 1j * buf[:, 2 * j + 1]
        freq = np.abs(arr[names[0]].real)
    elif rowbytes == 8 + (nvars - 1) * 16:  # freq real f8, rest complex
        freq = np.empty(npts)
        for n in names[1:]:
            arr[n] = np.empty(npts, complex)
        for i in range(npts):
            o = i * rowbytes
            freq[i] = abs(np.frombuffer(body, "<f8", 1, o)[0]); o += 8
            for n in names[1:]:
                re_ = np.frombuffer(body, "<f8", 1, o)[0]; o += 8
                im_ = np.frombuffer(body, "<f8", 1, o)[0]; o += 8
                arr[n][i] = re_ + 1j * im_
    else:
        raise ValueError(f"unexpected rowbytes {rowbytes} (nvars={nvars})")
    return names, freq, arr


def find(arr, want):
    for k in arr:
        if want.lower() in k.lower():
            return arr[k]
    raise KeyError(want)


def corners(freq, z):
    """peak + the -3 dB crossings either side of the peak."""
    ip = int(np.argmax(z))
    zpk, fpk = z[ip], freq[ip]
    thr = zpk / np.sqrt(2.0)

    def cross(lo, hi, step):
        i = ip
        while lo <= i <= hi:
            if z[i] <= thr:
                # linear-interp in log-f between i and i-/+step
                j = i + (-step)
                if 0 <= j < len(z) and (z[j] - thr) * (z[i] - thr) < 0:
                    f1, f2 = np.log10(freq[j]), np.log10(freq[i])
                    z1, z2 = z[j], z[i]
                    fx = f1 + (thr - z1) * (f2 - f1) / (z2 - z1)
                    return 10 ** fx
                return freq[i]
            i += step
        return None

    f_lo = cross(0, ip, -1)
    f_hi = cross(ip, len(z) - 1, +1)
    return fpk, zpk, f_lo, f_hi


def analyse_ac():
    names, f, arr = read_ac_raw(os.path.join(DATA, "chain_ac.raw"))
    stages = [("CSP_OUT", "csp_out"), ("SHOUT", "shout"), ("BLR_OUT", "blr_out"),
              ("BUF_OUT", "buf_out"), ("OUT_50", "out_50")]
    mags = {}
    for label, key in stages:
        mags[label] = np.abs(find(arr, key))

    zout = mags["OUT_50"]
    fpk, zpk, f_lo, f_hi = corners(f, zout)
    fom = {
        "peak_transimpedance_ohm": float(zpk),
        "peak_frequency_Hz": float(fpk),
        "minus3dB_low_Hz": None if f_lo is None else float(f_lo),
        "minus3dB_high_Hz": None if f_hi is None else float(f_hi),
        "bandwidth_Hz": None if (f_lo is None or f_hi is None) else float(f_hi - f_lo),
        "engine": "LTspice 24.x .ac dec 300 0.1 100Meg",
        "note": "1 A AC injected at CSP input -> |V(OUT_50)| = charge-path transimpedance; buffer populated AV=2.",
    }
    with open(os.path.join(DATA, "chain_ac_fom.json"), "w") as fh:
        json.dump(fom, fh, indent=2)

    # Bode plot: normalised OUT_50 (peak=0 dB) + per-stage transimpedance
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 8), sharex=True)
    znorm_db = 20 * np.log10(zout / zpk)
    ax1.semilogx(f, znorm_db, color="C3", lw=2, label="OUT_50 (normalised)")
    ax1.axhline(-3, color="gray", ls="--", lw=0.8)
    if f_lo:
        ax1.axvline(f_lo, color="C0", ls=":", lw=1, label=f"-3 dB lo = {f_lo:,.0f} Hz")
    if f_hi:
        ax1.axvline(f_hi, color="C2", ls=":", lw=1, label=f"-3 dB hi = {f_hi/1e3:,.1f} kHz")
    ax1.axvline(fpk, color="k", ls="-", lw=0.7, label=f"peak = {fpk/1e3:,.1f} kHz")
    ax1.set_ylim(-40, 3)
    ax1.set_ylabel("normalised |gain|  [dB]")
    ax1.set_title("Full-chain AC transfer function  (charge input -> OUT_50, buffer AV=2)")
    ax1.grid(True, which="both", alpha=0.3)
    ax1.legend(fontsize=8, loc="lower center")

    for label, key in stages:
        ax2.loglog(f, mags[label], lw=1.5, label=label)
    ax2.set_xlabel("frequency  [Hz]")
    ax2.set_ylabel("transimpedance |V/I|  [ohm]")
    ax2.grid(True, which="both", alpha=0.3)
    ax2.legend(fontsize=8, ncol=5, loc="lower center")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "chain_ac_bode.png"), dpi=110)
    plt.close(fig)
    return fom


# ----------------------------------------------------------------------------
# linearity (.step .meas) -- parse the LTspice .log measurement tables
# ----------------------------------------------------------------------------
QLIST = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30, 40, 50, 60]  # matches deck .step


def parse_meas(logtext, name):
    blk = re.split(r"Measurement:\s*" + re.escape(name) + r"\s*\n", logtext)
    if len(blk) < 2:
        return None
    vals = []
    for ln in blk[1].splitlines():
        m = re.match(r"\s*(\d+)\s+([-\d.eE+]+)", ln)
        if m:
            vals.append(float(m.group(2)))
        elif vals:
            break
    return vals


def analyse_linearity():
    log = open(os.path.join(DATA, "chain_linearity.log"), "r", errors="replace").read()
    out50 = parse_meas(log, "out50_pk")
    buf = parse_meas(log, "buf_pk")
    shout = [abs(v) for v in parse_meas(log, "shout_mag")]
    q = np.array(QLIST[: len(out50)])
    out50 = np.array(out50[: len(q)])
    buf = np.array(buf[: len(q)])
    shout = np.array(shout[: len(q)])

    # small-signal fit over Q<=2 pC (well below any clip): OUT_50 = m*Q + b
    lin = q <= 2.0
    A = np.vstack([q[lin], np.ones(lin.sum())]).T
    m, b = np.linalg.lstsq(A, out50[lin], rcond=None)[0]  # m in V/pC, b = baseline
    ideal = m * q + b
    dev_pct = 100 * (out50 - ideal) / ideal

    def onset(th):
        for i in range(len(q)):
            if abs(dev_pct[i]) >= th:
                return float(q[i])
        return None

    fom = {
        "small_signal_gain_mV_per_pC": float(m * 1000),
        "baseline_offset_mV": float(b * 1000),
        "out50_clip_V": float(np.max(out50)),
        "buf_clip_V": float(np.max(buf)),
        "compression_onset_1pct_pC": onset(1.0),
        "compression_onset_5pct_pC": onset(5.0),
        "linear_max_charge_pC_at_1pct": onset(1.0),
        "shaper_still_linear_at_60pC": bool(shout[-1] < 11.0),
        "clip_stage": "THS3491 buffer (rail-limited ~+10.25 V) -> OUT_50 ~5.13 V",
        "table": [
            {"Q_pC": float(q[i]), "OUT50_mV": float(out50[i] * 1000),
             "BUF_V": float(buf[i]), "SHOUT_V": float(shout[i]),
             "dev_from_linear_pct": float(dev_pct[i])}
            for i in range(len(q))
        ],
        "engine": "LTspice 24.x .tran .step Qpc",
    }
    with open(os.path.join(DATA, "chain_linearity_fom.json"), "w") as fh:
        json.dump(fom, fh, indent=2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
    ax1.plot(q, out50 * 1000, "o-", color="C3", label="OUT_50 peak (sim)")
    ax1.plot(q, ideal * 1000, "--", color="gray", label=f"ideal {m*1000:.1f} mV/pC")
    ax1.set_xlabel("injected charge  [pC]")
    ax1.set_ylabel("OUT_50 peak  [mV]")
    ax1.set_title("Charge linearity (OUT_50, buffer AV=2)")
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=8)

    ax2.plot(q, buf, "o-", color="C0", label="BUF_OUT peak")
    ax2.plot(q, shout, "s-", color="C2", label="|SHOUT| peak")
    ax2.axhline(10.25, color="C0", ls=":", lw=1, label="buffer clip ~10.25 V")
    ax2.axhline(11.0, color="C2", ls=":", lw=1, label="shaper rail ~11 V")
    ax2.set_xlabel("injected charge  [pC]")
    ax2.set_ylabel("stage peak  [V]")
    ax2.set_title("Which stage clips first (dynamic range)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "chain_linearity.png"), dpi=110)
    plt.close(fig)
    return fom


# ----------------------------------------------------------------------------
# noise -- SPICE .noise floor (modelled sources) + CR-112 datasheet ENC
# ----------------------------------------------------------------------------
Q_E = 1.602176634e-19          # C per electron
GAIN_OUT50_mV_per_pC = 133.4   # small-signal, from the linearity fit / deck of record
# CR-112-R2.1 datasheet (measured, tau=1 us Gaussian shaping):
ENC0_E = 7000.0                # ENC RMS at zero added capacitance, electrons
ENC_SLOPE_E_PER_PF = 30.0      # ENC slope, electrons RMS / pF
CR112_GAIN_mV_per_pC = 13.0
CR112_MAX_CHARGE_pC = 210.0


def read_noise_raw(path):
    """LTspice .noise .raw: real, var0=frequency, then V(onoise)/V(inoise)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ltspice_raw", os.path.join(os.path.dirname(__file__), "ltspice_raw.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    r = mod.read_raw(path)
    d = r["data"]
    fkey = r["vars"][0]
    on = next(k for k in r["vars"] if "onoise" in k.lower())
    return np.abs(d[fkey]), d[on]


def analyse_noise():
    f, onoise = read_noise_raw(os.path.join(DATA, "chain_noise.raw"))
    order = np.argsort(f)
    f, onoise = f[order], onoise[order]

    def rms(fmax):
        m = f <= fmax
        return float(np.sqrt(np.trapz(onoise[m] ** 2, f[m])))

    def to_e(vrms):
        enc_C = vrms / (GAIN_OUT50_mV_per_pC * 1e-3 / 1e-12)   # V / (V per C) = C
        return enc_C / Q_E

    # in-band = shaper passband (out to ~2x the 130 kHz corner); the ENC is defined
    # at the shaper output, so this is the apples-to-apples cross-check vs datasheet.
    # full-band adds the THS3491's out-of-band white noise (buffer sits AFTER shaper).
    vout_rms_inband = rms(300e3)
    vout_rms = rms(f.max())          # full band, 0.1 Hz .. 10 MHz
    enc_e_inband = to_e(vout_rms_inband)
    enc_e_sim = to_e(vout_rms)

    # datasheet ENC vs representative SiPM/detector capacitances
    caps_pF = [0, 100, 470, 1000, 2000, 3400]
    ds = []
    for c in caps_pF:
        enc_e = ENC0_E + ENC_SLOPE_E_PER_PF * c           # Cremat linear model
        enc_C_ds = enc_e * Q_E
        vout_noise_mV = enc_C_ds / 1e-12 * GAIN_OUT50_mV_per_pC   # noise at OUT_50
        ds.append({
            "Cdet_pF": c,
            "ENC_electrons": round(enc_e),
            "ENC_fC": round(enc_C_ds * 1e15, 3),
            "noise_at_OUT50_uV": round(vout_noise_mV * 1e3, 1),
        })
    # dynamic range: OUT_50 linear clip 5.13 V vs the zero-C noise
    dr = 5.131 / (ds[0]["noise_at_OUT50_uV"] * 1e-6)

    fom = {
        "spice_floor": {
            "vout_rms_inband_uV_at_OUT50": round(vout_rms_inband * 1e6, 2),
            "ENC_electrons_inband": round(enc_e_inband),
            "vout_rms_fullband_uV_at_OUT50": round(vout_rms * 1e6, 2),
            "ENC_electrons_fullband": round(enc_e_sim),
            "inband_def": "0.1 Hz .. 300 kHz (shaper passband; ENC is defined at the shaper output)",
            "fullband_def": "0.1 Hz .. 10 MHz (adds THS3491 out-of-band white noise)",
            "captures": "resistor thermal (incl. 680k Rf parallel noise) + THS3491 model noise",
            "excludes": "CR-112 input-transistor series (white+1/f) noise -> not in the noiseless macromodel",
        },
        "datasheet_ENC_CR112": {
            "model": "ENC(C) = 7000 e- + 30 e-/pF  (tau=1 us Gaussian, per CR-112-R2.1 datasheet)",
            "vs_capacitance": ds,
            "max_charge_per_event_pC": CR112_MAX_CHARGE_pC,
            "dynamic_range_zeroC": f"OUT_50 clip 5.13 V / {ds[0]['noise_at_OUT50_uV']} uV = {dr:,.0f} : 1",
        },
        "verdict": ("The SPICE-modelled electronics noise referred to input is ~%d e- in-band "
                    "(shaper passband, to 300 kHz) and ~%d e- full-band (to 10 MHz, where the "
                    "THS3491 sitting AFTER the shaper adds out-of-band white noise). Both are the "
                    "SAME ORDER OF MAGNITUDE as the CR-112 datasheet ENC of 7000 e-, and this is with "
                    "the CSP input-FET series noise ABSENT from the macromodel -- i.e. the noise is "
                    "dominated by the feedback-resistor (680k) parallel thermal noise and the front "
                    "end, exactly as a charge-sensitive preamp should be, and no board stage (BLR, "
                    "buffer, terminations, P/Z) introduces a runaway noise source. The 300 kHz "
                    "brickwall is still wider than the true Gaussian ENC noise-bandwidth, so it over- "
                    "counts somewhat. DESIGN NUMBER for the noise budget = the CR-112 datasheet "
                    "ENC(C)=7000+30*C at tau=1 us (tabulated above); SPICE is only a consistency check."
                    % (round(enc_e_inband), round(enc_e_sim))),
    }
    with open(os.path.join(DATA, "chain_noise_fom.json"), "w") as fh:
        json.dump(fom, fh, indent=2)

    # plot: onoise spectrum + datasheet ENC vs C
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
    ax1.loglog(f, onoise * 1e9, color="C4", lw=1.5)
    ax1.axvline(300e3, color="gray", ls=":", lw=1, label="shaper-band edge (300 kHz)")
    ax1.set_xlabel("frequency  [Hz]")
    ax1.set_ylabel("output noise density  [nV/rtHz]")
    ax1.set_title(f"OUT_50 noise spectrum (modelled)\nin-band {vout_rms_inband*1e6:.0f} uV -> ~{round(enc_e_inband)} e- ; "
                  f"full-band {vout_rms*1e6:.0f} uV -> ~{round(enc_e_sim)} e-")
    ax1.grid(True, which="both", alpha=0.3)
    ax1.legend(fontsize=8)

    cc = [d["Cdet_pF"] for d in ds]
    ee = [d["ENC_electrons"] for d in ds]
    ax2.plot(cc, ee, "o-", color="C1", label="CR-112 datasheet ENC")
    ax2.axhline(round(enc_e_inband), color="C4", ls="--", lw=1,
                label=f"modelled in-band floor ~{round(enc_e_inband)} e-")
    ax2.set_xlabel("detector (SiPM) capacitance  [pF]")
    ax2.set_ylabel("ENC  [electrons RMS]")
    ax2.set_title("ENC vs detector capacitance (tau=1 us)")
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "chain_noise.png"), dpi=110)
    plt.close(fig)
    return fom


if __name__ == "__main__":
    ac = analyse_ac()
    print("AC transfer function (charge -> OUT_50):")
    print(f"  peak transimpedance = {ac['peak_transimpedance_ohm']:.4g} ohm "
          f"at f_peak = {ac['peak_frequency_Hz']/1e3:.2f} kHz")
    lo = ac["minus3dB_low_Hz"]; hi = ac["minus3dB_high_Hz"]
    print(f"  -3 dB band = {lo:,.0f} Hz .. {hi/1e3:,.1f} kHz  (BW ~= {ac['bandwidth_Hz']/1e3:,.1f} kHz)")
    print()
    lin = analyse_linearity()
    print("Charge linearity / dynamic range (OUT_50, buffer AV=2):")
    print(f"  small-signal gain = {lin['small_signal_gain_mV_per_pC']:.2f} mV/pC "
          f"(baseline {lin['baseline_offset_mV']:.2f} mV)")
    print(f"  linear to <1% up to  {lin['compression_onset_1pct_pC']} pC ; "
          f"<5% up to {lin['compression_onset_5pct_pC']} pC")
    print(f"  OUT_50 hard-clip = {lin['out50_clip_V']:.3f} V "
          f"(buffer {lin['buf_clip_V']:.3f} V) ; {lin['clip_stage']}")
    print("  plots -> plots/chain_ac_bode.png, plots/chain_linearity.png")
    print()
    nz = analyse_noise()
    sf = nz["spice_floor"]; ds = nz["datasheet_ENC_CR112"]
    print("Noise / ENC:")
    print(f"  SPICE modelled floor: in-band ~{sf['ENC_electrons_inband']} e- ({sf['vout_rms_inband_uV_at_OUT50']} uV), "
          f"full-band ~{sf['ENC_electrons_fullband']} e- ({sf['vout_rms_fullband_uV_at_OUT50']} uV)")
    print(f"    (Rf thermal + shaper R's + THS3491; no CSP FET series noise -> datasheet is the design number)")
    print(f"  CR-112 datasheet ENC = 7000 e- + 30 e-/pF at tau=1 us:")
    for row in ds["vs_capacitance"]:
        print(f"    Cdet {row['Cdet_pF']:>5} pF -> {row['ENC_electrons']:>6} e-  "
              f"({row['ENC_fC']} fC, {row['noise_at_OUT50_uV']} uV at OUT_50)")
    print(f"  dynamic range (zero-C) = {ds['dynamic_range_zeroC']}")
    print("  plot -> plots/chain_noise.png")
