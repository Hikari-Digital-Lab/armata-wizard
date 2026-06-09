# configure_gemini.ps1 — Windows nativ. Configurează Hermes pt Gemini, NON-interactiv.
# Uz:  configure_gemini.ps1 -Key <GEMINI_API_KEY> [-Model gemini-3.5-flash]
param(
  [Parameter(Mandatory=$true)][string]$Key,
  [string]$Model = "gemini-3.5-flash"
)
$ErrorActionPreference = 'Stop'

# Binar Hermes (PATH sau %LOCALAPPDATA%\hermes\bin)
$hermesBin = $null
$cmd = Get-Command hermes -ErrorAction SilentlyContinue
if ($cmd) { $hermesBin = $cmd.Source }
if (-not $hermesBin) {
  $cand = Join-Path $env:LOCALAPPDATA 'hermes\bin\hermes.exe'
  if (Test-Path $cand) { $hermesBin = $cand }
}
if (-not $hermesBin) { Write-Error "Nu găsesc binarul 'hermes'. Hermes e instalat?"; exit 3 }

# 1) provider + model
& $hermesBin config set model.provider gemini
& $hermesBin config set model.default $Model

# 2) calea .env
$envPath = (& $hermesBin config env-path 2>$null | Select-Object -First 1)
if (-not $envPath) { $envPath = Join-Path $env:LOCALAPPDATA 'hermes\.env' }
$envDir = Split-Path $envPath -Parent
if (-not (Test-Path $envDir)) { New-Item -ItemType Directory -Path $envDir -Force | Out-Null }

# 3) merge cheile (scoate vechile, adaugă noile)
$lines = @()
if (Test-Path $envPath) {
  $lines = Get-Content $envPath | Where-Object { $_ -notmatch '^(GOOGLE_API_KEY|GEMINI_API_KEY)=' }
}
$lines += "GOOGLE_API_KEY=$Key"
$lines += "GEMINI_API_KEY=$Key"
Set-Content -Path $envPath -Value $lines -Encoding utf8

# Permisiuni owner-only (echivalent chmod 600 pe Windows)
icacls $envPath /inheritance:r *> $null
icacls $envPath /grant:r "$($env:USERNAME):(F)" *> $null

Write-Output "OK: provider=gemini model=$Model"
Write-Output "ENV_PATH=$envPath"
