# backup.ps1 — Windows nativ. Copie de siguranță la config.yaml + .env ÎNAINTE de modificări.
# Salvează pe Desktop cu timestamp. Nu modifică originalele.
$ErrorActionPreference = 'SilentlyContinue'

$hermesBin = $null
$cmd = Get-Command hermes -ErrorAction SilentlyContinue
if ($cmd) { $hermesBin = $cmd.Source }
if (-not $hermesBin) {
  $cand = Join-Path $env:LOCALAPPDATA 'hermes\bin\hermes.exe'
  if (Test-Path $cand) { $hermesBin = $cand }
}

$cfg = $null; $envp = $null
if ($hermesBin) {
  $cfg  = (& $hermesBin config path 2>$null | Select-Object -First 1)
  $envp = (& $hermesBin config env-path 2>$null | Select-Object -First 1)
}
if (-not $cfg)  { $cfg  = Join-Path $env:LOCALAPPDATA 'hermes\config.yaml' }
if (-not $envp) { $envp = Join-Path $env:LOCALAPPDATA 'hermes\.env' }

$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$dest = Join-Path ([Environment]::GetFolderPath('Desktop')) "hermes-backup-$ts"
New-Item -ItemType Directory -Path $dest -Force | Out-Null

$copied = 0
if (Test-Path $cfg)  { Copy-Item $cfg  (Join-Path $dest 'config.yaml'); $copied++ }
if (Test-Path $envp) { Copy-Item $envp (Join-Path $dest '.env'); $copied++ }

if ($copied -gt 0) {
  Write-Output "BACKUP_DIR=$dest"
  Write-Output "BACKUP_FILES=$copied"
} else {
  Remove-Item $dest -Force -Recurse
  Write-Output "BACKUP_DIR=none"
  Write-Output "BACKUP_FILES=0  (instalare curata - nimic de salvat)"
}
