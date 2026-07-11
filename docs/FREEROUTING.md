# Autorouting with FreeRouting

KiCad has no built-in autorouter. The standard route is: **KiCad → Specctra `.dsn` →
FreeRouting (autoroute) → Specctra `.ses` → KiCad**. This repo provides scripts for the
KiCad ends; FreeRouting is a separate free tool.

> **This board was autorouted this way — DRC 0/0/0, 0 unconnected** (see
> [../hardware/routed-top.png](../hardware/routed-top.png)). Verified recipe:
> **FreeRouting v2.2.4** (`freerouting-2.2.4.jar`, needs **Java 25**) +
> **4-layer board with GND plane (In1) and −VDC plane (In2)** so both outer layers are
> free to route. That combination routed all 480 nets; on 2 layers it left ~9 −VDC
> unrouted. Exact commands:
> ```
> "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/gen_pcb.py     # 4-layer, planes
> "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/export_dsn.py  # -> .dsn
> java -jar freerouting-2.2.4.jar -de hardware/...dsn -do hardware/...ses   # ~45 s
> "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/import_ses.py hardware/...ses
> "C:/Program Files/KiCad/10.0/bin/python.exe" hardware/fill_zones.py  # planes + outer GND fill
> bash scripts/drc.sh                                                  # 0/0/0
> ```
> Get Java 25 (Temurin JRE) from adoptium.net; the FreeRouting jar from the releases below.

> **Installed on this machine (2026-07) + the headless invocation that actually works.**
> - Java: **Temurin JRE 25.0.3** at `C:\Users\darro\tools\jdk-25.0.3+9-jre\bin\java.exe`
>   (v2.2.4 is compiled to class-file 69 — **Java 21 fails** with `UnsupportedClassVersionError`;
>   25 is mandatory, not a suggestion).
> - FreeRouting: `C:\Users\darro\tools\freerouting-2.2.4.jar`.
> - **Two flags are required for a headless CLI route, plus a dead proxy:** without them the CLI
>   *hangs on startup* — `--gui.enabled=false` (its default headless path still needs this; a bare
>   `-Djava.awt.headless=true` only gives "couldn't get screen resolution" then hangs), and its
>   **version-check + Google-BigQuery analytics have no network timeout**, so they block forever.
>   Point Java at a dead proxy so those calls fail *fast* (`-da` alone did NOT stop it):
>   ```
>   JAVA="C:/Users/darro/tools/jdk-25.0.3+9-jre/bin/java.exe"
>   JAR="C:/Users/darro/tools/freerouting-2.2.4.jar"
>   "$JAVA" -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=1 \
>           -Dhttp.proxyHost=127.0.0.1  -Dhttp.proxyPort=1 \
>           -jar "$JAR" --gui.enabled=false -da -mp 30 -de board.dsn -do board.ses
>   ```
>   Verified: the single-channel board routed **84 → 0 unrouted in ~3 s**, and after
>   `import_ses.py` + `fill_zones.py` the KiCad DRC was **0 errors / 0 unconnected**.
> - **Route from a shell that FreeRouting can actually run in**, or use these flags — a plain
>   non-interactive shell (no desktop session) needs `--gui.enabled=false` + the dead proxy.

> **Prerequisite — clean placement first.** The Specctra `.dsn` exporter (and a good
> autoroute) require **no overlapping copper**. The headless auto-placement in
> [hardware/gen_pcb.py](../hardware/gen_pcb.py) groups the 12 channels into rows but still
> has copper crowding in the dense module region (run `bash scripts/drc.sh` — look for
> `clearance`/`shorting_items`). **Spread those parts out in the KiCad PCB editor until
> DRC shows no clearance/short errors before exporting the DSN.** Placement is the human
> step; FreeRouting does the tedious trace routing.

---

## 1. Download FreeRouting

- Releases: **https://github.com/freerouting/freerouting/releases** — grab the latest
  installer for your OS (Windows `.msi`/`.exe`) **or** the portable `freerouting-<ver>.jar`.
- The `.jar` needs **Java 21+** (JRE/JDK). The OS installers bundle their own runtime, so on
  Windows the installer is the easy path. Check Java with `java -version`.

## 2. Export the DSN from KiCad

**Reliable (GUI):** open `hardware/multi-channel-cremat-amplifier.kicad_pcb` in the PCB
editor → **File → Export → Specctra DSN…** → save `multi-channel-cremat-amplifier.dsn`.

**Script (after placement is clean):**
```
"C:/Program Files/KiCad/10.0/bin/python.exe" hardware/export_dsn.py   # -> hardware/*.dsn
```
(The script uses `pcbnew.ExportSpecctraDSN`; it returns False if any copper overlaps remain
— clean the placement first, see the prerequisite above.)

## 3. Autoroute in FreeRouting

**GUI:** launch FreeRouting → **Open** the `.dsn` → it begins the **autorouter**
automatically (or click the autoroute/▶ button). Let it converge (the status bar shows
passes / remaining; you can stop when "items to route" hits 0). Then
**File → Export Specctra Session File** → save `multi-channel-cremat-amplifier.ses`.

**Headless / CLI** (recent FreeRouting):
```
java -jar freerouting-<ver>.jar -de hardware/multi-channel-cremat-amplifier.dsn \
                                -do hardware/multi-channel-cremat-amplifier.ses
# -de = design (input .dsn), -do = output (.ses); add -mp <N> to cap passes.
```

## 4. Import the routed session back into KiCad

**GUI:** PCB editor → **File → Import → Specctra Session…** → pick the `.ses`. The routed
tracks + vias appear on the board.

**Script:**
```
"C:/Program Files/KiCad/10.0/bin/python.exe" hardware/import_ses.py hardware/multi-channel-cremat-amplifier.ses
```

## 5. Finish in KiCad

- Pour the **GND zone** (it's added unfilled by `gen_pcb.py`; `Edit → Fill All Zones` / `B`).
  Do this **after** routing so the pour flows around the traces.
- Re-cut the **MCX edge cutouts**: `gen_pcb.py` moved each MCX footprint's `Edge.Cuts`
  cutout to `Dwgs.User` so the board stayed one clean rectangle for routing — when you
  mechanically place the 36 jacks at the board edges, restore those cutouts on `Edge.Cuts`.
- Run **`bash scripts/drc.sh`** (or DRC in the GUI) → resolve to **0 errors** before fab.
- Then fab outputs — see [hardware/BUILD-IN-KICAD.md](../hardware/BUILD-IN-KICAD.md) Track 7.

---

## Notes

- Net classes (`hv_bias` 1.0 mm, `power`, `signal`, `Default`) are in the `.kicad_pro` and
  are written into the DSN, so FreeRouting honors the HV bias clearance.
- FreeRouting respects the board outline (`Edge.Cuts`) as the routing boundary and treats
  zones/keepouts accordingly.
- If the autoroute leaves a few unrouted nets, finish them by hand in the KiCad router.
