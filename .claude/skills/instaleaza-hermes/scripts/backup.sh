#!/usr/bin/env bash
# backup.sh — Linux/macOS/WSL2. Copie de siguranță la config.yaml + .env ÎNAINTE de modificări.
# Salvează pe Desktop (sau ~ dacă nu există Desktop), cu timestamp. Nu modifică originalele.
set -u
export PATH="$HOME/.local/bin:$PATH"

HERMES=""
if command -v hermes >/dev/null 2>&1; then HERMES="$(command -v hermes)"
elif [ -x "$HOME/.local/bin/hermes" ]; then HERMES="$HOME/.local/bin/hermes"; fi

if [ -n "$HERMES" ]; then
  CFG="$("$HERMES" config path 2>/dev/null | head -1)"
  ENVP="$("$HERMES" config env-path 2>/dev/null | head -1)"
fi
[ -z "${CFG:-}" ] && CFG="$HOME/.hermes/config.yaml"
[ -z "${ENVP:-}" ] && ENVP="$HOME/.hermes/.env"

TS="$(date +%Y%m%d-%H%M%S)"
DEST="$HOME/Desktop/hermes-backup-$TS"
[ -d "$HOME/Desktop" ] || DEST="$HOME/hermes-backup-$TS"
mkdir -p "$DEST"

copied=0
[ -f "$CFG" ]  && { cp "$CFG"  "$DEST/config.yaml"; copied=$((copied+1)); }
[ -f "$ENVP" ] && { cp "$ENVP" "$DEST/.env"; chmod 600 "$DEST/.env"; copied=$((copied+1)); }

if [ "$copied" -gt 0 ]; then
  echo "BACKUP_DIR=$DEST"
  echo "BACKUP_FILES=$copied"
else
  rmdir "$DEST" 2>/dev/null || true
  echo "BACKUP_DIR=none"
  echo "BACKUP_FILES=0  (instalare curată — nimic de salvat)"
fi
