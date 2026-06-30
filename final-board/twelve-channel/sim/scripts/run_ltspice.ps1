# run_ltspice.ps1 -- C3 board-sim: run a deck in LTspice batch, bring the .raw back.
# Same staging trick as B2 (LTspice batch fails on OneDrive space-paths): stage the
# whole decks/ dir to a clean local temp, run there, copy .raw/.log back to sim/data/.
#
# Usage:  powershell -File scripts\run_ltspice.ps1 <deckname-without-ext>
#         deck = decks\<name>.cir  ->  outputs data\<name>.raw + data\<name>.log
param([Parameter(Mandatory=$true)][string]$Name)

$lt    = "C:\Users\darro\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
$sim   = Split-Path $PSScriptRoot -Parent          # ...\twelve-channel\sim
$decks = Join-Path $sim "decks"
$data  = Join-Path $sim "data"
$work  = "C:\Temp\ltspice_12ch"

New-Item -ItemType Directory -Force -Path $work | Out-Null
New-Item -ItemType Directory -Force -Path $data | Out-Null

$src = Join-Path $decks "$Name.cir"
if (-not (Test-Path $src)) { Write-Error "deck not found: $src"; exit 2 }

Get-ChildItem $decks -File | ForEach-Object { Copy-Item $_.FullName (Join-Path $work $_.Name) -Force }
Copy-Item $src (Join-Path $work "$Name.net") -Force
Remove-Item (Join-Path $work "$Name.raw"),(Join-Path $work "$Name.log") -ErrorAction SilentlyContinue

$stage = Join-Path $work "$Name.net"
$p = Start-Process -FilePath $lt -ArgumentList @("-b","-Run",$stage) -NoNewWindow -PassThru -Wait
Write-Output ("LTspice exit code: " + $p.ExitCode)

foreach ($ext in @("raw","log")) {
  $o = Join-Path $work "$Name.$ext"
  if (Test-Path $o) { Copy-Item $o (Join-Path $data "$Name.$ext") -Force }
}
$logpath = Join-Path $data "$Name.log"
if (Test-Path $logpath) { Write-Output "--- LOG (tail) ---"; Get-Content $logpath -Tail 20 }
$rawpath = Join-Path $data "$Name.raw"
if (Test-Path $rawpath) { Write-Output ("RAW bytes: " + (Get-Item $rawpath).Length) } else { Write-Output "NO RAW PRODUCED" }
