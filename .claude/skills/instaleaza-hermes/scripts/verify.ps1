# verify.ps1 — Windows nativ. Verifică instalarea + configurarea, NON-interactiv.
# Pași: hermes --version → hermes doctor → hermes -z (round-trip real cu Gemini).
# NU rula niciodată `hermes` interactiv (bare/chat/tui) — ar bloca fără TTY.
$ErrorActionPreference = 'SilentlyContinue'

$hermesBin = $null
$cmd = Get-Command hermes -ErrorAction SilentlyContinue
if ($cmd) { $hermesBin = $cmd.Source }
if (-not $hermesBin) {
  $cand = Join-Path $env:LOCALAPPDATA 'hermes\bin\hermes.exe'
  if (Test-Path $cand) { $hermesBin = $cand }
}
if (-not $hermesBin) { Write-Output "VERIFY_BIN=missing"; Write-Output "RESULT=FAIL"; exit 3 }
Write-Output "VERIFY_BIN=$hermesBin"

# 1) versiune
$ver = (& $hermesBin --version 2>$null | Select-Object -First 1)
if ($ver) { Write-Output "VERSION_OK=yes ($ver)" } else { Write-Output "VERSION_OK=no" }

# 2) doctor
& $hermesBin doctor *> $null
if ($?) { Write-Output "DOCTOR_OK=yes" } else { Write-Output "DOCTOR_OK=no" }

# 3) round-trip real
$out = (& $hermesBin -z "reply with the single word OK" 2>&1)
if ($LASTEXITCODE -eq 0 -and $out) {
  Write-Output "ONESHOT_OK=yes"
  Write-Output "ONESHOT_REPLY=$out"
  Write-Output "RESULT=PASS"
} else {
  Write-Output "ONESHOT_OK=no"
  Write-Output "ONESHOT_ERR=$out"
  if ("$out" -match "agent failed|API key|PERMISSION|401|403") { Write-Output "ONESHOT_HINT=cheie_invalida" }
  else { Write-Output "ONESHOT_HINT=alta_problema" }
  Write-Output "RESULT=FAIL"
}
