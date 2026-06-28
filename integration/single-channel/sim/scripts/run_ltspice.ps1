# run_ltspice.ps1 -- run a B2 chain deck in LTspice batch, bringing the .raw back.
# LTspice batch silently fails to write outputs to OneDrive paths with spaces, so
# we stage the ENTIRE decks/ dir (deck + all .include'd .sub/.inc) in a clean local
# temp dir, run there, and copy the .raw/.log back into sim/data/.
#
# Usage:  powershell -File scripts\run_ltspice.ps1 <deckname-without-ext>
#         deck = decks\<name>.cir  ->  outputs data\<name>.raw + data\<name>.log
param([Parameter(Mandatory=$true)][string]$Name)

$lt    = "C:\Users\darro\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
$sim   = Split-Path $PSScriptRoot -Parent          # ...\single-channel\sim
$decks = Join-Path $sim "decks"
$data  = Join-Path $sim "data"
$work  = "C:\Temp\ltspice_chan"

New-Item -ItemType Directory -Force -Path $work | Out-Null
New-Item -ItemType Directory -Force -Path $data | Out-Null

$src = Join-Path $decks "$Name.cir"
if (-not (Test-Path $src)) { Write-Error "deck not found: $src"; exit 2 }

# stage every deck-support file (LTspice resolves .include relative to the netlist dir)
Get-ChildItem $decks -File | ForEach-Object { Copy-Item $_.FullName (Join-Path $work $_.Name) -Force }
# LTspice batch wants a .net or .cir; copy the chosen deck to <name>.net too
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
if (Test-Path $logpath) { Write-Output "--- LOG (tail) ---"; Get-Content $logpath -Tail 25 }
$rawpath = Join-Path $data "$Name.raw"
if (Test-Path $rawpath) { Write-Output ("RAW bytes: " + (Get-Item $rawpath).Length) } else { Write-Output "NO RAW PRODUCED" }
