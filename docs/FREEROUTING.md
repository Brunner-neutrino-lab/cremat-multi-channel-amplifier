# Autorouting with FreeRouting

KiCad has no built-in autorouter. The standard route is: **KiCad → Specctra `.dsn` →
FreeRouting (autoroute) → Specctra `.ses` → KiCad**. This repo provides scripts for the
KiCad ends; FreeRouting is a separate free tool.

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
