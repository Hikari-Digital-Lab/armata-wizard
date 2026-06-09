#!/usr/bin/env bash
# detect.sh — Linux/macOS/WSL2. READ-ONLY: detectează OS-ul și ce e deja instalat.
# Nu modifică nimic. Tipărește linii key=value ușor de parsat.
set -u

# PATH-ul moștenit din Claude Desktop poate să nu vadă binarul nou → adăugăm calea tipică.
export PATH="$HOME/.local/bin:$PATH"

say() { printf '%s\n' "$1"; }

# --- OS ---
uname_s="$(uname -s 2>/dev/null || echo unknown)"
case "$uname_s" in
  Linux)  os="linux";  [ -n "${WSL_DISTRO_NAME:-}" ] && os="wsl2" ;;
  Darwin) os="macos" ;;
  *)      os="$uname_s" ;;
esac
say "OS=$os"
say "UNAME=$uname_s"
[ "$os" = "macos" ] && say "ARCH=$(uname -m 2>/dev/null)"

# --- Hermes binar ---
hermes_bin=""
if command -v hermes >/dev/null 2>&1; then
  hermes_bin="$(command -v hermes)"
elif [ -x "$HOME/.local/bin/hermes" ]; then
  hermes_bin="$HOME/.local/bin/hermes"
fi

if [ -n "$hermes_bin" ]; then
  say "HERMES_INSTALLED=yes"
  say "HERMES_BIN=$hermes_bin"
  ver="$("$hermes_bin" --version 2>/dev/null | head -1)"
  say "HERMES_VERSION=${ver:-necunoscuta}"
  cfg="$("$hermes_bin" config path 2>/dev/null | head -1)"
  env="$("$hermes_bin" config env-path 2>/dev/null | head -1)"
  say "HERMES_CONFIG=${cfg:-$HOME/.hermes/config.yaml}"
  say "HERMES_ENV=${env:-$HOME/.hermes/.env}"
else
  say "HERMES_INSTALLED=no"
  say "HERMES_CONFIG=$HOME/.hermes/config.yaml"
  say "HERMES_ENV=$HOME/.hermes/.env"
fi

# --- unelte pentru instalare ---
for t in curl bash docker; do
  if command -v "$t" >/dev/null 2>&1; then say "HAS_${t}=yes"; else say "HAS_${t}=no"; fi
done
# docker daemon viu?
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  say "DOCKER_RUNNING=yes"
else
  say "DOCKER_RUNNING=no"
fi
