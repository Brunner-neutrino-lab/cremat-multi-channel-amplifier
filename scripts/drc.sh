#!/usr/bin/env bash
# DRC gate for the multi-channel Cremat amplifier PCB.
# Usage: bash scripts/drc.sh   -> reports/drc.json  (prints error/warning/unconnected counts)
set -euo pipefail
cd "$(dirname "$0")/.."
KCLI="${KICAD_CLI:-/c/Program Files/KiCad/10.0/bin/kicad-cli.exe}"
[ -x "$KCLI" ] || KCLI="$(command -v kicad-cli)"
mkdir -p reports
PCB="hardware/multi-channel-cremat-amplifier.kicad_pcb"
"$KCLI" pcb drc -o reports/drc.json --format json --severity-error --severity-warning "$PCB" >/dev/null 2>&1 || true
python - <<'PY'
import json
d=json.load(open('reports/drc.json'))
v=d.get('violations',[])
errs=sum(1 for x in v if x['severity']=='error')
warns=sum(1 for x in v if x['severity']=='warning')
unc=d.get('unconnected_items',[])
unc=unc if isinstance(unc,int) else len(unc)
print("DRC: %d error(s), %d warning(s), %d unconnected (ratsnest)"%(errs,warns,unc))
PY
