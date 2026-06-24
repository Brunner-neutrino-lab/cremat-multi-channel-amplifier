#!/usr/bin/env bash
# ERC gate for the multi-channel Cremat amplifier schematic.
# Usage: bash scripts/erc.sh   -> reports/erc_root.json (exit nonzero on ERROR-severity violations)
set -euo pipefail
cd "$(dirname "$0")/.."
KCLI="${KICAD_CLI:-/c/Program Files/KiCad/10.0/bin/kicad-cli.exe}"
[ -x "$KCLI" ] || KCLI="$(command -v kicad-cli)"
mkdir -p reports
SCH="hardware/multi-channel-cremat-amplifier.kicad_sch"
"$KCLI" sch erc -o reports/erc_root.json --format json "$SCH" >/dev/null 2>&1 || true
python - <<'PY'
import json,sys
d=json.load(open('reports/erc_root.json'))
errs=warns=0
for sh in d.get('sheets',[]):
    for v in sh.get('violations',[]):
        if v['severity']=='error': errs+=1
        elif v['severity']=='warning': warns+=1
print("ERC: %d error(s), %d warning(s)"%(errs,warns))
sys.exit(1 if errs else 0)
PY
