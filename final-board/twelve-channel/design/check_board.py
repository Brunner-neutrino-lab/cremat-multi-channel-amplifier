#!/usr/bin/env python3
"""Acceptance gate for the 12-channel board. Run this before generating fab outputs, and
after ANY change (regeneration, GUI edit, refill).

    "C:/Program Files/KiCad/10.0/bin/python.exe" check_board.py

WHY THIS EXISTS -- the stock checks have blind spots that cost this project weeks:

  * `kicad-cli` NEVER READS `.kicad_pro`. ERC, netlist export and everything derived from them
    are structurally blind to every project-file defect. A netclass missing its SCHEMATIC fields
    silently breaks eeschema connectivity for every net in that class -- headless checks stay
    green while the GUI shows hundreds of parity warnings. Check 5 catches that class of defect.
  * `kicad-cli pcb drc --schematic-parity` DOES NOT COMPARE PAD NETS. It is footprint-level only
    and will report 0 while the GUI reports hundreds. Check 2 is the real parity test.
  * Footprints link to symbols by UUID SHEET-PATH (sheetpath.tstamps + component.tstamps), not by
    reference. Collide those paths and "Update PCB from Schematic" duplicates the entire board.
    Check 1 asserts the linkage is a bijection.
  * DRC reporting "0 unconnected" does NOT mean the pours participate: zones left on
    ZONE_CONNECTION_NONE are isolated from every pad, and DRC still passes if tracks carry the
    net. Check 4 asserts the pad-connection mode explicitly.

Every check states what it CANNOT see. None of them can judge schematic legibility, mechanical
sanity, or polarised-part rotation -- those need a human at the GUI and at the fab's preview.

Exit code 0 = all gates pass.
"""
import os, re, sys, csv, json, glob, fnmatch, subprocess, tempfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "twelve-channel.kicad_pcb")
PRO = os.path.join(HERE, "twelve-channel.kicad_pro")
SCH = os.path.join(HERE, "twelve-channel.kicad_sch")
CPL = os.path.join(HERE, "fab", "jlc", "cpl-twelve-channel-jlc.csv")
CLI = os.environ.get("KICAD_CLI", r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe")

FAILURES = []
def ok(msg):   print("  [PASS] %s" % msg)
def bad(msg):  print("  [FAIL] %s" % msg); FAILURES.append(msg)
def info(msg): print("         %s" % msg)
def blind(msg):print("         cannot see: %s" % msg)
def head(n, t):print("\n== %d. %s %s" % (n, t, "=" * max(0, 66 - len(t))))


# ---------------------------------------------------------------- netlist ------------
def export_netlist():
    """Netlist straight from the schematic -- the reference for checks 1 and 2."""
    out = os.path.join(tempfile.gettempdir(), "twelve-channel.check.net")
    r = subprocess.run([CLI, "sch", "export", "netlist", "-o", out, SCH],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr); sys.exit("netlist export failed")
    return out


def parse_netlist(path):
    """-> comps {ref: full_uuid_path}, pinnets {(ref, pin): netname}"""
    t = open(path, encoding="utf-8").read()
    comps = {}
    for cm in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)(?=\(comp\s|\(libparts)', t, re.S):
        ref, body = cm.group(1), cm.group(2)
        m36 = re.search(r'\(tstamps "([0-9a-fA-F-]{36})"\)', body)
        msp = re.search(r'\(tstamps "(/[0-9a-fA-F/-]*)"\)', body)
        if m36:
            comps[ref] = (msp.group(1) if msp else "/") + m36.group(1)
    pinnets = {}
    for nm in re.finditer(r'\(net\s+\(code "[^"]*"\)\s+\(name "([^"]*)"\)(.*?)(?=\(net\s+\(code|\Z)',
                          t, re.S):
        name, body = nm.group(1), nm.group(2)
        for node in re.finditer(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', body):
            pinnets[(node.group(1), node.group(2))] = name
    return comps, pinnets


# ---------------------------------------------------------------- checks -------------
def check_bijection(b, comps):
    head(1, "footprint <-> symbol UUID path bijection")
    fp_paths, noschem = {}, []
    for f in b.GetFootprints():
        p = f.GetPath().AsString()
        if p:
            fp_paths.setdefault(p, []).append(f.GetReference())
        else:
            noschem.append(f.GetReference())
    dupes = {p: r for p, r in fp_paths.items() if len(r) > 1}
    if dupes:
        bad("%d UUID paths carry >1 footprint (Update-PCB would duplicate the board)" % len(dupes))
        for p, r in list(dupes.items())[:5]:
            info("%s -> %s" % (p, r))
    else:
        ok("%d board footprints hold %d distinct UUID paths (no collisions)"
           % (sum(len(r) for r in fp_paths.values()), len(fp_paths)))
    if noschem:
        info("%d board-only footprint(s), no schematic symbol: %s"
             % (len(noschem), ", ".join(sorted(noschem))))
    sch_paths = set(comps.values())
    only_b, only_s = set(fp_paths) - sch_paths, sch_paths - set(fp_paths)
    if only_b or only_s:
        bad("path sets differ: %d board-only, %d schematic-only" % (len(only_b), len(only_s)))
        for p in list(only_b)[:3]: info("board-only    %s (%s)" % (p, fp_paths[p]))
        for p in list(only_s)[:3]: info("schematic-only %s" % p)
    else:
        ok("bijection holds: %d symbols <-> %d footprints" % (len(sch_paths), len(fp_paths)))
    blind("whether the *right* symbol maps to the right footprint (only that a 1:1 map exists)")


def check_pad_nets(b, pinnets):
    """THE parity check. kicad-cli --schematic-parity does not do this."""
    head(2, "pad-net parity (board pads vs schematic netlist)")
    checked = mism = 0
    examples = []
    for f in b.GetFootprints():
        if not f.GetPath().AsString():
            continue                                   # mechanical, no symbol
        ref = f.GetReference()
        for p in f.Pads():
            num = p.GetNumber()
            if not num:
                continue
            board_net = p.GetNetname()
            sch_net = pinnets.get((ref, num))
            checked += 1
            if sch_net is None:
                # schematic leaves it unconnected -> board must too
                if board_net and not board_net.startswith("unconnected-"):
                    mism += 1
                    examples.append("%s pad %s: board '%s', schematic: no net" % (ref, num, board_net))
            elif board_net != sch_net:
                mism += 1
                examples.append("%s pad %s: board '%s' != schematic '%s'" % (ref, num, board_net, sch_net))
    if mism:
        bad("%d/%d pad nets disagree with the schematic" % (mism, checked))
        for e in examples[:8]: info(e)
    else:
        ok("%d/%d pad nets match the schematic exactly" % (checked - mism, checked))
    blind("whether the schematic itself is correct -- this proves board==schematic, not that "
          "either is right")


def check_erc_drc():
    head(3, "ERC / DRC (kicad-cli, --severity-all)")
    for kind, args, target in (
        ("ERC", ["sch", "erc"], SCH),
        ("DRC", ["pcb", "drc", "--schematic-parity"], PCB),
    ):
        out = os.path.join(tempfile.gettempdir(), "check.%s.json" % kind)
        r = subprocess.run([CLI] + args + ["--format", "json", "--severity-all", "-o", out, target],
                           capture_output=True, text=True)
        if not os.path.exists(out):
            bad("%s did not produce a report: %s" % (kind, (r.stderr or r.stdout).strip()[:200]))
            continue
        d = json.load(open(out, encoding="utf-8"))
        counts = {}
        for key in ("violations", "unconnected_items", "schematic_parity"):
            counts[key] = len(d.get(key, []) or [])
        total = sum(counts.values())
        detail = ", ".join("%s=%d" % kv for kv in counts.items() if kv[0] in d)
        (ok if total == 0 else bad)("%s: %s" % (kind, detail or "0"))
        if total:
            for v in (d.get("violations") or [])[:5]:
                info("%s: %s" % (v.get("severity"), v.get("description", "")[:110]))
    blind("ERC/DRC read NO project-file state via kicad-cli; DRC's own --schematic-parity is "
          "footprint-level only (check 2 is the real one)")


def check_zones(b):
    head(4, "copper zones: filled, and actually tied to pads")
    NAMES = {0: "INHERITED", 1: "THERMAL", 2: "NONE", 3: "FULL"}
    zones = list(b.Zones())
    if not zones:
        bad("no copper zones on the board"); return
    for z in zones:
        conn = NAMES.get(z.GetPadConnection(), str(z.GetPadConnection()))
        line = "%-8s net=%-6s prio=%d  %-9s filled=%s  area=%.0f mm2" % (
            b.GetLayerName(z.GetLayer()), z.GetNetname(), z.GetAssignedPriority(),
            conn, z.IsFilled(), z.GetFilledArea() / 1e12)
        if not z.IsFilled():
            bad("zone NOT FILLED -- " + line)
        elif z.GetPadConnection() == 2:                # ZONE_CONNECTION_NONE
            bad("zone isolated from every pad (NONE) -- " + line)
        else:
            ok(line)
    blind("whether the pour is electrically continuous around cutouts -- read the render/GUI")


def check_netclasses(b):
    """Never infer 'the class applied' from 'DRC passed' -- DRC uses the same assignment.
    Measure the copper."""
    head(5, "netclasses really applied (measured from copper)")
    pro = json.load(open(PRO, encoding="utf-8"))
    ns = pro.get("net_settings", {})
    classes = {c["name"]: c for c in ns.get("classes", [])}
    pats = ns.get("netclass_patterns", [])
    if not classes:
        bad("`.kicad_pro` has NO netclasses -- a GUI save probably flattened it"); return
    SCHEMA_FIELDS = ["wire_width", "bus_width", "line_style",
                     "diff_pair_gap", "diff_pair_width", "microvia_diameter", "microvia_drill"]
    for name, c in sorted(classes.items()):
        missing = [f for f in SCHEMA_FIELDS if f not in c]
        if missing:
            bad("netclass '%s' is missing SCHEMATIC fields %s -- this BREAKS eeschema "
                "connectivity for every net in the class (headless checks stay green)"
                % (name, missing))
        else:
            ok("netclass '%s' carries all %d schematic fields" % (name, len(SCHEMA_FIELDS)))
    tracks = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
    for name, c in sorted(classes.items()):
        want = c.get("track_width")
        globs = [p["pattern"] for p in pats if p.get("netclass") == name]
        if want is None or not globs:
            continue
        want = round(float(want), 4)
        got = {round(t.GetWidth() / 1e6, 4)
               for t in tracks if any(fnmatch.fnmatch(t.GetNetname(), g) for g in globs)}
        # A netclass track_width is the DEFAULT/minimum, not a cap -- a deliberately wider run is
        # legal and electrically better. Only NARROWER copper means the class failed to apply.
        under = sorted(w for w in got if w < want)
        if not got:
            info("netclass '%s': patterns %s match no routed track (nothing to measure)" % (name, globs))
        elif under:
            bad("netclass '%s': copper NARROWER than the %s mm class width: %s -- class not applied"
                % (name, want, under))
        elif got == {want}:
            ok("netclass '%s': every matching track measures %s mm" % (name, want))
        else:
            ok("netclass '%s': all matching track >= %s mm class width (also present: %s mm)"
               % (name, want, sorted(w for w in got if w > want)))
    blind("whether the PATTERNS match the nets you intended (a typo'd glob matches nothing and "
          "is silently never applied -- 'matches no routed track' above is the tell)")


def check_bom_cpl(b):
    head(6, "fab package consistency")
    if not os.path.exists(CPL):
        info("no CPL at %s -- skipped" % CPL); return
    rows = list(csv.DictReader(open(CPL, encoding="utf-8-sig")))
    pos = {f.GetReference(): f for f in b.GetFootprints()}
    missing = [r["Designator"] for r in rows if r["Designator"] not in pos]
    dnp_in_cpl = [r["Designator"] for r in rows
                  if r["Designator"] in pos and pos[r["Designator"]].IsDNP()]
    if missing: bad("%d CPL designators are not on the board: %s" % (len(missing), missing[:6]))
    else:       ok("all %d CPL designators exist on the board" % len(rows))
    if dnp_in_cpl: bad("%d DNP parts are in the CPL: %s" % (len(dnp_in_cpl), dnp_in_cpl[:6]))
    else:          ok("no DNP parts in the CPL")
    moved = []
    for r in rows:
        f = pos.get(r["Designator"])
        if not f: continue
        x = float(r["Mid X"].replace("mm", "")); px = f.GetPosition().x / 1e6
        if abs(px - x) > 0.05 and abs(px + x) > 0.05:
            moved.append(r["Designator"])
    if moved: bad("%d CPL positions are stale vs the board: %s" % (len(moved), moved[:6]))
    else:     ok("CPL positions still match the board (%d parts)" % len(rows))
    zips = glob.glob(os.path.join(HERE, "fab", "jlc", "*.zip"))
    for z in zips:
        info("gerber package: %s (%.2f MB)" % (os.path.basename(z), os.path.getsize(z) / 1e6))
    blind("whether the LCSC/MPN part numbers are still orderable -- re-verify live before ordering; "
          "and polarised-part ROTATION, which only the fab's own preview shows")


def census(b):
    head(7, "census (compare against expectation by eye)")
    bb = b.GetBoardEdgesBoundingBox()
    tr = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
    vi = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    fps = list(b.GetFootprints())
    info("board      %.1f x %.1f mm, %d copper layers" % (bb.GetWidth() / 1e6, bb.GetHeight() / 1e6,
                                                          b.GetCopperLayerCount()))
    info("footprints %d (%d DNP)  pads %d  nets %d"
         % (len(fps), sum(1 for f in fps if f.IsDNP()),
            sum(len(list(f.Pads())) for f in fps), b.GetNetCount()))
    info("tracks     %d   vias %d" % (len(tr), len(vi)))


def main():
    print("Acceptance gate -- %s" % os.path.basename(PCB))
    b = pcbnew.LoadBoard(PCB)
    comps, pinnets = parse_netlist(export_netlist())
    check_bijection(b, comps)
    check_pad_nets(b, pinnets)
    check_erc_drc()
    check_zones(b)
    check_netclasses(b)
    check_bom_cpl(b)
    census(b)
    print("\n" + "=" * 72)
    if FAILURES:
        print("FAILED -- %d gate(s):" % len(FAILURES))
        for f in FAILURES: print("  - %s" % f)
    else:
        print("ALL AUTOMATED GATES PASS.")
    print("""
STILL REQUIRES A HUMAN (no script can do these):
  1. Open the .kicad_pro in the KiCad GUI and read the schematic. This is the only
     instrument that sees project-file-scoped defects and GUI-strict connectivity.
  2. Inspect the 3D render for mechanical sanity.
  3. Check polarised-part rotation in the fab's own parts preview before ordering.""")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
