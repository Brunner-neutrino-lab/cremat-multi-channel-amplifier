#!/usr/bin/env python
"""analyze.py -- parse an LTspice .raw, compute CR-112 CSP figures of merit, plot.

Usage:  python analyze.py <name>      # reads sim/<name>.raw
Outputs (in sim/):
  plots/<name>_csp_out.png      CSP_OUT vs time (rise-time + full decay panels)
  plots/<name>_input_charge.png injected current + cumulative charge
  data/<name>_csp_out.csv       reusable (time_s, csp_out_V) -- shaper stimulus
  data/<name>_fom.csv           figures of merit table
Prints the FoM table to stdout.

No external deps beyond numpy + matplotlib. LTspice .raw reader is built in.
"""
import sys, os, struct
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SIM = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- raw reader
def read_ltspice_raw(path):
    """Read an LTspice binary (or ascii) .raw transient file -> (names, data dict)."""
    with open(path, "rb") as f:
        raw = f.read()
    # Header is UTF-16LE text up to 'Binary:' or 'Values:'
    # Find the 'Binary:\n' or 'Values:\n' marker (encoded UTF-16LE).
    for marker in (b"B\x00i\x00n\x00a\x00r\x00y\x00:\x00\n\x00",
                   b"V\x00a\x00l\x00u\x00e\x00s\x00:\x00\n\x00"):
        idx = raw.find(marker)
        if idx != -1:
            mode = "binary" if marker.startswith(b"B\x00") else "ascii"
            header = raw[:idx].decode("utf-16-le", errors="replace")
            body = raw[idx + len(marker):]
            break
    else:
        raise RuntimeError("no Binary:/Values: marker found")

    nvars = npts = 0
    names = []
    flags = ""
    in_vars = False
    for line in header.splitlines():
        s = line.strip()
        if s.startswith("No. Variables:"):
            nvars = int(s.split(":")[1])
        elif s.startswith("No. Points:"):
            npts = int(s.split(":")[1])
        elif s.startswith("Flags:"):
            flags = s.split(":", 1)[1].strip()
        elif s.startswith("Variables:"):
            in_vars = True
        elif s.startswith("Binary") or s.startswith("Values"):
            in_vars = False
        elif in_vars and s:
            parts = s.split("\t") if "\t" in s else s.split()
            # format: idx name type
            if len(parts) >= 2:
                names.append(parts[1])

    is_complex = "complex" in flags.lower()
    data = {}
    if mode == "binary":
        # LTspice: time axis is float64, other vars float32 (real transient),
        # UNLESS 'double' flag present (all float64). Detect by size.
        # Per-point size for default real transient = 8 (time) + 4*(nvars-1).
        size_default = 8 + 4 * (nvars - 1)
        size_double  = 8 * nvars
        total = len(body)
        if npts and total >= npts * size_double and (total // size_double) == npts:
            per = size_double; alldbl = True
        else:
            per = size_default; alldbl = False
        arr = np.zeros((npts, nvars), dtype=np.float64)
        off = 0
        for p in range(npts):
            base = p * per
            if alldbl:
                vals = struct.unpack_from("<%dd" % nvars, body, base)
                arr[p, :] = vals
            else:
                t = struct.unpack_from("<d", body, base)[0]
                rest = struct.unpack_from("<%df" % (nvars - 1), body, base + 8)
                arr[p, 0] = t
                arr[p, 1:] = rest
        for i, nm in enumerate(names):
            data[nm] = arr[:, i]
    else:  # ascii
        vals = []
        cur = []
        for line in body.decode("utf-8", errors="replace").splitlines():
            s = line.strip()
            if not s:
                continue
            toks = s.split("\t") if "\t" in s else s.split()
            # a point row starts with an integer index then the time value
            if len(toks) >= 2 and toks[0].isdigit() and len(cur) == 0:
                cur = [float(toks[1])]
                if len(toks) >= 3:
                    cur.append(float(toks[2]))
            else:
                cur.append(float(toks[-1]))
            if len(cur) == nvars:
                vals.append(cur); cur = []
        arr = np.array(vals)
        for i, nm in enumerate(names):
            data[nm] = arr[:, i]

    # LTspice may store the time axis as |abs| with sign packed; take abs.
    if names:
        data[names[0]] = np.abs(data[names[0]])
    return names, data

def getvar(names, data, *cands):
    low = {n.lower(): n for n in names}
    for c in cands:
        if c.lower() in low:
            return data[low[c.lower()]]
    # try v(...) wrapping
    for c in cands:
        k = ("v(%s)" % c).lower()
        if k in low:
            return data[low[k]]
    raise KeyError("none of %s in %s" % (cands, names))

# ---------------------------------------------------------------- FoM
def rise_time_10_90(t, y, t_event):
    """10-90% rise time of the leading edge after t_event (signed for polarity)."""
    pk = y[np.argmax(np.abs(y))]
    sign = np.sign(pk) if pk != 0 else 1.0
    ys = y * sign
    peak = ys.max()
    m = t >= t_event
    tt, yy = t[m], ys[m]
    lo, hi = 0.10 * peak, 0.90 * peak
    def cross(level):
        for i in range(1, len(yy)):
            if yy[i-1] < level <= yy[i]:
                # linear interp
                return tt[i-1] + (level - yy[i-1]) * (tt[i] - tt[i-1]) / (yy[i] - yy[i-1])
        return np.nan
    t10, t90 = cross(lo), cross(hi)
    return (t90 - t10) if (np.isfinite(t10) and np.isfinite(t90)) else np.nan

def decay_tau(t, y, t_start):
    """Fit single-exponential tau on the decaying tail (log-linear LS)."""
    pk = y[np.argmax(np.abs(y))]
    sign = np.sign(pk) if pk != 0 else 1.0
    ys = y * sign
    ipk = np.argmax(ys)
    tpk = t[ipk]; ypk = ys[ipk]
    # fit window: from 1*tau-ish after peak down to ~5% of peak, well before end
    m = (t > tpk + 1e-6) & (ys > 0.05 * ypk) & (ys < 0.95 * ypk)
    if m.sum() < 5:
        return np.nan, tpk, ypk
    tt = t[m]; yy = ys[m]
    A = np.vstack([tt, np.ones_like(tt)]).T
    slope, _ = np.linalg.lstsq(A, np.log(yy), rcond=None)[0]
    tau = -1.0 / slope if slope < 0 else np.nan
    return tau, tpk, ypk

# ---------------------------------------------------------------- main
def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "cr11x_csp"
    rawp = os.path.join(SIM, name + ".raw")
    names, data = read_ltspice_raw(rawp)
    t   = getvar(names, data, "time")
    out = getvar(names, data, "V(csp_out)", "csp_out")
    try:
        iin = getvar(names, data, "I(Iinj)", "i(iinj)")
    except KeyError:
        iin = None

    # injected charge: integrate |I| of the pulse (sign: current into 'input')
    Q_inj = None
    if iin is not None:
        Q_inj = np.trapz(iin, t)            # signed integral over whole run
        Q_pulse = np.trapz(np.abs(iin), t)  # magnitude

    t_event = 1.0e-6  # pulse centre
    pk_idx = np.argmax(np.abs(out))
    peak = out[pk_idx]
    tr = rise_time_10_90(t, out, t_event)
    tau, tpk, ypk = decay_tau(t, out, t_event)

    # gain check
    Q_pC = 0.5
    gain_mV_per_pC = peak * 1e3 / Q_pC

    # ---- write reusable CSV (shaper stimulus) ----
    os.makedirs(os.path.join(SIM, "data"), exist_ok=True)
    os.makedirs(os.path.join(SIM, "plots"), exist_ok=True)
    np.savetxt(os.path.join(SIM, "data", name + "_csp_out.csv"),
               np.column_stack([t, out]), delimiter=",",
               header="time_s,csp_out_V", comments="")

    fom = [
        ("peak_amplitude_mV", peak * 1e3),
        ("charge_gain_mV_per_pC", gain_mV_per_pC),
        ("rise_time_10_90_ns", tr * 1e9),
        ("decay_tau_us", tau * 1e6),
        ("peak_time_us", tpk * 1e6),
        ("Q_injected_pC", (Q_pulse * 1e12) if iin is not None else float("nan")),
    ]
    with open(os.path.join(SIM, "data", name + "_fom.csv"), "w") as f:
        f.write("metric,value\n")
        for k, v in fom:
            f.write("%s,%.6g\n" % (k, v))

    # ---- plots ----
    # 1) CSP_OUT: rise panel + full decay panel
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    mr = (t >= 0.99e-6) & (t <= 1.05e-6)
    ax1.plot((t[mr] - 1e-6) * 1e9, out[mr] * 1e3, color="tab:blue")
    ax1.axhline(peak * 1e3, ls="--", color="gray", lw=0.8)
    ax1.set_xlabel("time after pulse (ns)"); ax1.set_ylabel("CSP_OUT (mV)")
    ax1.set_title("CR-112 CSP_OUT rise (tr~%.2f ns)" % (tr * 1e9))
    ax1.grid(alpha=0.3)
    ax2.plot(t * 1e6, out * 1e3, color="tab:blue")
    ax2.set_xlabel("time (us)"); ax2.set_ylabel("CSP_OUT (mV)")
    ax2.set_title("CR-112 CSP_OUT decay (tau~%.1f us)" % (tau * 1e6))
    ax2.grid(alpha=0.3)
    fig.suptitle("CR-112 response to 0.5 pC -> peak %.2f mV (gain %.2f mV/pC)"
                 % (peak * 1e3, gain_mV_per_pC))
    fig.tight_layout()
    fig.savefig(os.path.join(SIM, "plots", name + "_csp_out.png"), dpi=130)
    plt.close(fig)

    # 2) input charge: current pulse + cumulative charge
    if iin is not None:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
        mp = (t >= 0.999e-6) & (t <= 1.003e-6)
        ax1.plot((t[mp] - 1e-6) * 1e9, iin[mp] * 1e3, color="tab:red")
        ax1.set_xlabel("time after 1us (ns)"); ax1.set_ylabel("Iinj (mA)")
        ax1.set_title("Injected current pulse")
        ax1.grid(alpha=0.3)
        cumQ = np.concatenate([[0], np.cumsum(0.5 * (iin[1:] + iin[:-1]) * np.diff(t))])
        ax2.plot(t * 1e6, cumQ * 1e12, color="tab:red")
        ax2.axhline(Q_pulse * 1e12, ls="--", color="gray", lw=0.8)
        ax2.set_xlabel("time (us)"); ax2.set_ylabel("cumulative charge (pC)")
        ax2.set_title("Injected charge = %.3f pC" % (Q_pulse * 1e12))
        ax2.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(SIM, "plots", name + "_input_charge.png"), dpi=130)
        plt.close(fig)

    # ---- print ----
    print("=== CR-112 CSP figures of merit (deck: %s) ===" % name)
    for k, v in fom:
        print("  %-26s %.4g" % (k, v))
    print("  raw vars:", names)

if __name__ == "__main__":
    main()
