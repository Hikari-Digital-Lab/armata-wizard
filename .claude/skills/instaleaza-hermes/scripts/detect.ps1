# detect.ps1 — Windows nativ. READ-ONLY: detectează ce e deja instalat. Nu modifică nimic.
# Tipărește linii key=value ușor de parsat. Rulează în PowerShell.
$ErrorActionPreference = 'SilentlyContinue'

Write-Output "OS=windows"
Write-Output "UNAME=$([System.Environment]::OSVersion.VersionString)"

# Hermes binar: PATH sau %LOCALAPPDATA%\hermes
$hermesBin = $null
$cmd = Get-Command hermes -ErrorAction SilentlyContinue
if ($cmd) { $hermesBin = $cmd.Source }
if (-not $hermesBin) {
  $cand = Join-Path $env:LOCALAPPDATA 'hermes\bin\hermes.exe'
  if (Test-Path $cand) { $hermesBin = $cand }
}

if ($hermesBin) {
  Write-Output "HERMES_INSTALLED=yes"
  Write-Output "HERMES_BIN=$hermesBin"
  $ver = (& $hermesBin --version 2>$null | Select-Object -First 1)
  if (-not $ver) { $ver = "necunoscuta" }
  Write-Output "HERMES_VERSION=$ver"
  $cfg = (& $hermesBin config path 2>$null | Select-Object -First 1)
  $env_ = (& $hermesBin config env-path 2>$null | Select-Object -First 1)
  if (-not $cfg)  { $cfg  = Join-Path $env:LOCALAPPDATA 'hermes\config.yaml' }
  if (-not $env_) { $env_ = Join-Path $env:LOCALAPPDATA 'hermes\.env' }
  Write-Output "HERMES_CONFIG=$cfg"
  Write-Output "HERMES_ENV=$env_"
} else {
  Write-Output "HERMES_INSTALLED=no"
  Write-Output "HERMES_CONFIG=$(Join-Path $env:LOCALAPPDATA 'hermes\config.yaml')"
  Write-Output "HERMES_ENV=$(Join-Path $env:LOCALAPPDATA 'hermes\.env')"
}

# Unelte
foreach ($t in @('docker')) {
  if (Get-Command $t -ErrorAction SilentlyContinue) { Write-Output "HAS_${t}=yes" } else { Write-Output "HAS_${t}=no" }
}
docker info *> $null
if ($?) { Write-Output "DOCKER_RUNNING=yes" } else { Write-Output "DOCKER_RUNNING=no" }
