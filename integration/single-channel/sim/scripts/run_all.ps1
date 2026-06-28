# run_all.ps1 -- B2 chan-sim full reproducible pipeline.
# From integration/single-channel/sim/ :  powershell -File scripts\run_all.ps1
$ErrorActionPreference = "Stop"
$here = Split-Path $PSScriptRoot -Parent

Write-Output "[1/5] full chain, single 0.5 pC event (per-stage FoM, polarity-corrected)"
& powershell -File "$PSScriptRoot\run_ltspice.ps1" chain_single_event
python "$here\scripts\analyze_chain.py"

Write-Output "[2/5] full chain, 100 kHz train, corrected polarity (BLR proof)"
& powershell -File "$PSScriptRoot\run_ltspice.ps1" chain_pulse_train_pol

Write-Output "[3/5] full chain, 100 kHz train, raw CR-112 polarity (shows mis-restore)"
& powershell -File "$PSScriptRoot\run_ltspice.ps1" chain_pulse_train
python "$here\scripts\analyze_train.py"

Write-Output "[4/5] THS3491 buffer step stability check"
& powershell -File "$PSScriptRoot\run_ltspice.ps1" buffer_ac

Write-Output "[5/5] done. Plots in plots/, FoM JSON in data/."
