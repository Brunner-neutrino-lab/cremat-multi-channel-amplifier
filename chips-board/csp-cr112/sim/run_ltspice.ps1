# run_ltspice.ps1 -- run an LTspice deck in batch and bring the .raw back.
# LTspice batch silently fails to write outputs to OneDrive paths with spaces,
# so we stage the deck in a clean local temp dir, run there, and copy results back.
#
# Usage:  powershell -File run_ltspice.ps1 <deckname-without-ext>
#         (deck = sim\<deckname>.cir ; outputs -> sim\<deckname>.raw + .log)
param([Parameter(Mandatory=$true)][string]$Name)

$lt   = "C:\Users\darro\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
$sim  = $PSScriptRoot
$work = "C:\Temp\ltspice_csp"
New-Item -ItemType Directory -Force -Path $work | Out-Null

$src = Join-Path $sim "$Name.cir"
if (-not (Test-Path $src)) { Write-Error "deck not found: $src"; exit 2 }

$stage = Join-Path $work "$Name.net"
Copy-Item $src $stage -Force
Remove-Item (Join-Path $work "$Name.raw"),(Join-Path $work "$Name.log"),(Join-Path $work "$Name.op.raw") -ErrorAction SilentlyContinue

$p = Start-Process -FilePath $lt -ArgumentList @("-b","-Run",$stage) -NoNewWindow -PassThru -Wait
Write-Output ("LTspice exit code: " + $p.ExitCode)

foreach ($ext in @("raw","log")) {
  $o = Join-Path $work "$Name.$ext"
  if (Test-Path $o) { Copy-Item $o (Join-Path $sim "$Name.$ext") -Force }
}
if (Test-Path (Join-Path $sim "$Name.log")) { Write-Output "--- LOG ---"; Get-Content (Join-Path $sim "$Name.log") }
$rawpath = Join-Path $sim "$Name.raw"
if (Test-Path $rawpath) { Write-Output ("RAW bytes: " + (Get-Item $rawpath).Length) } else { Write-Output "NO RAW PRODUCED" }
