#!/usr/bin/env bash
# verify.sh — Linux/macOS/WSL2. Verifică instalarea + configurarea, NON-interactiv.
# Pași: hermes --version → hermes doctor → hermes -z (round-trip real cu Gemini).
# NU rulează niciodată `hermes` interactiv (bare/chat/tui) — ar bloca fără TTY.
set -u
export PATH="$HOME/.local/bin:$PATH"

HERMES=""
if command -v hermes >/dev/null 2>&1; then HERMES="$(command -v hermes)"
elif [ -x "$HOME/.local/bin/hermes" ]; then HERMES="$HOME/.local/bin/hermes"
else echo "VERIFY_BIN=missing"; echo "RESULT=FAIL"; exit 3; fi
echo "VERIFY_BIN=$HERMES"

# 1) versiune
ver="$("$HERMES" --version 2>/dev/null | head -1)"
if [ -n "$ver" ]; then echo "VERSION_OK=yes ($ver)"; else echo "VERSION_OK=no"; fi

# 2) doctor (exit !=0 = probleme)
if "$HERMES" doctor >/tmp/hermes_doctor.$$ 2>&1; then echo "DOCTOR_OK=yes"; else echo "DOCTOR_OK=no"; fi
rm -f /tmp/hermes_doctor.$$

# 3) round-trip real cu modelul (dovada „prima conversație")
out="$("$HERMES" -z "reply with the single word OK" 2>/tmp/hermes_z.$$)"
rc=$?
err="$(cat /tmp/hermes_z.$$ 2>/dev/null)"; rm -f /tmp/hermes_z.$$
if [ $rc -eq 0 ] && [ -n "$out" ]; then
  echo "ONESHOT_OK=yes"
  echo "ONESHOT_REPLY=$out"
  echo "RESULT=PASS"
else
  echo "ONESHOT_OK=no"
  echo "ONESHOT_ERR=${err:-exit $rc}"
  # semnal pt orchestrator: cheie greșită vs altă problemă
  case "$err" in
    *"agent failed"*|*"API key"*|*"PERMISSION"*|*"401"*|*"403"*) echo "ONESHOT_HINT=cheie_invalida" ;;
    *) echo "ONESHOT_HINT=alta_problema" ;;
  esac
  echo "RESULT=FAIL"
fi
