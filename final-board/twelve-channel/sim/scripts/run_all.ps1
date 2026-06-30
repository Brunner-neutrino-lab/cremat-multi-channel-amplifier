# run_all.ps1 -- C3 board-sim full reproducible pipeline (system-level check).
# From final-board/twelve-channel/sim/ :  powershell -File scripts\run_all.ps1
$ErrorActionPreference = "Stop"
$here = Split-Path $PSScriptRoot -Parent

Write-Output "[1/4] one-channel response in the x12 context (re-confirm OUT_50 vs Phase B)"
& powershell -File "$PSScriptRoot\run_ltspice.ps1" chain_single_event
python "$here\scripts\analyze_chain.py"

Write-Output "[2/4] shared-rail loading / decoupling / bulk budget (datasheet currents)"
python "$here\scripts\rail_budget.py"

Write-Output "[3/4] capture one channel's real dynamic supply-current demand"
& powershell -File "$PSScriptRoot\run_ltspice.ps1" chain_isupply

Write-Output "[4/4] shared-rail crosstalk bound (ripple -> THS3491 PSRR -> victim)"
python "$here\scripts\xtalk_analyze.py"

Write-Output "done. Plots in plots/, FoM JSON in data/, budget printed above."
