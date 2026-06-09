#!/usr/bin/env bash
# configure_gemini.sh — Linux/macOS/WSL2. Configurează Hermes pt Gemini, NON-interactiv.
# Uz:  configure_gemini.sh <GEMINI_API_KEY> [MODEL]
# - setează model.provider=gemini + model.default=MODEL via `hermes config set`
# - scrie cheia în .env (merge-safe, fără să strice alte chei) și chmod 600
set -eu

KEY="${1:-}"
MODEL="${2:-gemini-3.5-flash}"
if [ -z "$KEY" ]; then echo "EROARE: lipsește cheia Gemini (argument 1)" >&2; exit 2; fi

export PATH="$HOME/.local/bin:$PATH"

# Binar Hermes prin cale absolută (ocolește gotcha-ul PATH din Claude Desktop)
HERMES=""
if command -v hermes >/dev/null 2>&1; then HERMES="$(command -v hermes)"
elif [ -x "$HOME/.local/bin/hermes" ]; then HERMES="$HOME/.local/bin/hermes"
else echo "EROARE: nu găsesc binarul 'hermes'. Hermes e instalat?" >&2; exit 3; fi

# 1) provider + model (CLI non-interactiv; nu strică restul config.yaml)
"$HERMES" config set model.provider gemini
"$HERMES" config set model.default "$MODEL"

# 2) calea .env (din Hermes, autoritativ per-OS)
ENV_PATH="$("$HERMES" config env-path 2>/dev/null | head -1)"
[ -z "$ENV_PATH" ] && ENV_PATH="$HOME/.hermes/.env"
mkdir -p "$(dirname "$ENV_PATH")"
touch "$ENV_PATH"

# 3) merge cheile (scoate liniile vechi GOOGLE_API_KEY/GEMINI_API_KEY, adaugă cele noi)
TMP="$(mktemp)"
grep -vE '^(GOOGLE_API_KEY|GEMINI_API_KEY)=' "$ENV_PATH" > "$TMP" 2>/dev/null || true
{
  cat "$TMP"
  printf 'GOOGLE_API_KEY=%s\n' "$KEY"
  printf 'GEMINI_API_KEY=%s\n' "$KEY"
} > "$ENV_PATH"
rm -f "$TMP"
chmod 600 "$ENV_PATH"

echo "OK: provider=gemini model=$MODEL"
echo "ENV_PATH=$ENV_PATH"
