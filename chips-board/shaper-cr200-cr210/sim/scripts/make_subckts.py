#!/usr/bin/env python
"""A5 shaper-sim: wrap the Cremat model netlists as portable .subckt blocks.

The Cremat LTspice models ship as schematic (.asc)+symbol (.asy) hierarchical BLOCKs.
`LTspice.exe -netlist <file>.asc` produces a flat netlist whose external connections are
the symbol pins (named nets: input/output/pole-zero/+Vsupply/-Vsupply). We convert each
into a .subckt with those exact ports so a top-level deck can instantiate the genuine
Cremat model unchanged. The internal .lib/.model lines are kept (LTspice resolves them
against its own library: UniversalOpAmp2.lib, standard.jft, LTC.lib).

Pin order chosen to match the model .asy SpiceOrder:
  CR200_1us : input output pole-zero -Vsupply +Vsupply
  CR210     : input output -Vsupply +Vsupply
"""
import re, sys, pathlib

SIM = pathlib.Path(__file__).resolve().parents[1]
MODELS = SIM / "cremat-models"

SPECS = {
    "CR200_1US": {
        "net":   MODELS / "CR-200" / "CR-200-1us-R2.1.net",
        "ports": ["input", "output", "pole-zero", "-Vsupply", "+Vsupply"],
        "out":   SIM / "decks" / "cr200_1us.sub",
    },
    "CR210": {
        "net":   MODELS / "CR-210" / "CR-210-R0.net",
        "ports": ["input", "output", "-Vsupply", "+Vsupply"],
        "out":   SIM / "decks" / "cr210.sub",
    },
}

# Map the model's external net names to clean subckt port names (avoid '+'/'-' in ports).
PORTMAP = {
    "input": "IN", "output": "OUT", "pole-zero": "PZ",
    "+Vsupply": "VP", "-Vsupply": "VN",
}


def convert(name, spec):
    raw = spec["net"].read_text(encoding="utf-8", errors="replace").splitlines()
    body = []
    libs = []
    for ln in raw:
        s = ln.strip()
        if not s or s.startswith("*"):
            continue
        if s.lower().startswith(".backanno") or s.lower() == ".end":
            continue
        if s.lower().startswith(".lib") or s.lower().startswith(".model"):
            libs.append(s)
            continue
        body.append(ln.rstrip())

    # rename the external nets to clean port tokens everywhere they appear as whole words
    ports_clean = [PORTMAP[p] for p in spec["ports"]]
    def rename(line):
        for orig, new in PORTMAP.items():
            # whole-token replace (nets are space-delimited; 'pole-zero' has a dash)
            line = re.sub(r'(?<![\w\-])' + re.escape(orig) + r'(?![\w])', new, line)
        # LTspice's auto-generated subinstance names use a section sign (X§U1) that the
        # netlist parser rejects on re-read; strip it to a plain ASCII instance name.
        line = line.replace("X§", "XX")
        # micro sign -> 'u' so the deck is pure ASCII and unambiguous to the parser
        line = line.replace("µ", "u").replace("μ", "u")
        return line
    body = [rename(b) for b in body]
    libs = [rename(l) for l in libs]

    out = []
    out.append(f"* Cremat {name} wrapped as .subckt from official LTspice model netlist")
    out.append(f"* source: {spec['net'].name}  (model retrieved 2026-06-25 from cremat.com)")
    out.append(f".subckt {name} " + " ".join(ports_clean))
    out += ["  " + b for b in body]
    out.append(f".ends {name}")
    out.append("")
    spec["out"].write_text("\n".join(out) + "\n", encoding="ascii")
    print(f"wrote {spec['out'].name}: {len(body)} device lines, ports={ports_clean}")
    return libs


if __name__ == "__main__":
    all_libs = []
    for n, sp in SPECS.items():
        all_libs += convert(n, sp)
    # de-dup, preserve order; write a single models include for the top-level decks
    seen, uniq = set(), []
    for l in all_libs:
        if l not in seen:
            seen.add(l); uniq.append(l)
    inc = SIM / "decks" / "models.inc"
    hdr = ["* Cremat model libraries referenced by cr200_1us.sub / cr210.sub.",
           "* LTspice resolves these from its own lib dir (UniversalOpAmp2.lib, standard.jft, LTC.lib).",
           "* Included once at the top of every top-level deck."]
    inc.write_text("\n".join(hdr + uniq) + "\n", encoding="ascii")
    print(f"wrote models.inc: {len(uniq)} lib/model lines")
