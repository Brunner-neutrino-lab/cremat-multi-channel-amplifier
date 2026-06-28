#!/usr/bin/env python
"""Minimal LTspice binary/ascii .raw reader (transient analysis).

Returns dict: {'vars': [names], 'data': {name: np.ndarray}}. Time is real; for .tran the
first variable ('time') is stored as a double whose sign bit LTspice abuses -> use abs().
Handles LTspice 'Binary:' (float64 time + float32/float64 values) and 'Values:' ascii.
"""
import numpy as np
import re


def read_raw(path):
    with open(path, "rb") as f:
        raw = f.read()
    # header is UTF-16LE in modern LTspice; find the 'Binary:' or 'Values:' marker
    # detect encoding
    if raw[:2] == b"\xff\xfe" or (b"\x00" in raw[:64]):
        # UTF-16LE
        # split header at 'Binary:\n' encoded in utf-16le
        for marker in (b"Binary:\r\n", b"Binary:\n", b"Values:\r\n", b"Values:\n"):
            mk = marker.decode("ascii").encode("utf-16-le")
            idx = raw.find(mk)
            if idx != -1:
                header_bytes = raw[: idx + len(mk)]
                body = raw[idx + len(mk):]
                header = header_bytes.decode("utf-16-le", errors="replace")
                binary = b"Binary" in marker
                break
        else:
            raise ValueError("no Binary:/Values: marker (utf16)")
    else:
        for marker in (b"Binary:\r\n", b"Binary:\n", b"Values:\r\n", b"Values:\n"):
            idx = raw.find(marker)
            if idx != -1:
                header = raw[: idx + len(marker)].decode("ascii", errors="replace")
                body = raw[idx + len(marker):]
                binary = b"Binary" in marker
                break
        else:
            raise ValueError("no Binary:/Values: marker (ascii)")

    npts = int(re.search(r"No\. Points:\s*(\d+)", header).group(1))
    nvars = int(re.search(r"No\. Variables:\s*(\d+)", header).group(1))
    flags = re.search(r"Flags:\s*(.*)", header).group(1).lower()
    is_real = "real" in flags or "complex" not in flags
    # variable names: the block after the LAST 'Variables:' up to the marker
    var_section = header.split("Variables:")[-1]
    names = []
    for ln in var_section.splitlines():
        m = re.match(r"\s*\d+\s+(\S+)\s+\S+", ln)
        if m:
            names.append(m.group(1))
        if len(names) == nvars:
            break
    assert len(names) == nvars, f"{len(names)} names vs {nvars} vars"

    data = {n: np.empty(npts) for n in names}
    if binary:
        # LTspice tran: time stored as float64, other vars as float32 (unless double flag)
        is_double = "double" in flags
        off = 0
        valbytes = 8 if is_double else 4
        rowbytes = 8 + (nvars - 1) * valbytes  # var0 (time) always float64
        if len(body) < npts * rowbytes:
            # some builds store all as double
            rowbytes = 8 * nvars
            valbytes = 8
            is_double = True
        for i in range(npts):
            base = i * rowbytes
            t = np.frombuffer(body, dtype="<f8", count=1, offset=base)[0]
            data[names[0]][i] = t
            o = base + 8
            for j in range(1, nvars):
                if is_double:
                    v = np.frombuffer(body, dtype="<f8", count=1, offset=o)[0]; o += 8
                else:
                    v = np.frombuffer(body, dtype="<f4", count=1, offset=o)[0]; o += 4
                data[names[j]][i] = v
    else:
        # ASCII Values
        toks = body.split()
        # format: idx t  then nvars-1 values per point
        k = 0
        for i in range(npts):
            # first token is the point index, then time, then values
            _ = toks[k]; k += 1
            data[names[0]][i] = float(toks[k]); k += 1
            for j in range(1, nvars):
                data[names[j]][i] = float(toks[k]); k += 1

    # LTspice abuses sign bit of time
    data[names[0]] = np.abs(data[names[0]])
    return {"vars": names, "data": data, "npts": npts}


if __name__ == "__main__":
    import sys
    r = read_raw(sys.argv[1])
    print("vars:", r["vars"], "npts:", r["npts"])
    t = r["data"][r["vars"][0]]
    print("t range:", t.min(), t.max())
