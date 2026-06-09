#!/usr/bin/env python3
"""Idempotently patch the IMAGE worker's `delegate.py` so the CEO's image->copy chain works.

Why this exists (lessons learned):
  The copywriter runs AFTER the image worker. The CEO decides "this ad needs copy" in the
  GENERAL session, but reviews/approves the image in the ART-topic session (a SEPARATE Hermes
  session with no General context). The only context the Art session can recover is the brief
  stored by the artist's delegate.py (via `--show-brief`). So the "needs copy" signal must live
  in that brief — WITHOUT being sent to the artist (or the artist would render the marker text
  into the image). This patch adds a `--note` flag that is stored in the brief but never sent.

  It also hardens token reading: the older artist delegate.py reads the token only from
  `HERMES_HOME/.env`, which breaks when a script is run with a different HERMES_HOME. We make it
  try `PROFILE_DIR/.env` first (the profile that owns the skill), then `HERMES_HOME/.env`.

Idempotent: safe to run many times. If already patched, it reports and exits 0.
Robust: if an expected anchor is missing (a very different delegate.py), it changes nothing and
exits 2 so the caller can fall back to a manual edit.

Usage:
  patch_artist_delegate.py <path-to-artist/scripts/delegate.py>
"""
import io
import pathlib
import sys

NOTE_ARG = (
    '    ap.add_argument("--note", default="",\n'
    '                    help="internal note stored in the brief (recoverable via --show-brief) "\n'
    '                         "but NEVER sent to the worker — e.g. NEEDS_COPY for the image->copy flow")\n'
)

ANCHOR_NOTE_BEFORE = '    ap.add_argument("--prompt")\n'
ANCHOR_NOTE_AFTER = '    ap.add_argument("--reset", action="store_true")\n'

ANCHOR_BRIEF = (
    '    brief = st.get("brief", "") or ""\n'
    '    if nxt == 1:\n'
    '        brief = a.prompt\n'
)
PATCHED_BRIEF = (
    '    brief = st.get("brief", "") or ""\n'
    '    if nxt == 1:\n'
    '        brief = a.prompt\n'
    '        if getattr(a, "note", ""):\n'
    '            # Stored in the brief ONLY (recovered by the Art-session review via\n'
    '            # --show-brief); deliberately NOT added to `text`, so the worker never sees it.\n'
    '            brief = f"{a.prompt}\\n[INTERNAL NOTE \\u2014 not sent to worker] {a.note}"\n'
)

ANCHOR_ENV = (
    'HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or pathlib.Path.home() / ".hermes")\n'
    '\n'
    '\n'
    'def _env_value(key):\n'
    '    env_file = HERMES_HOME / ".env"\n'
    '    try:\n'
    '        for line in env_file.read_text(encoding="utf-8").splitlines():\n'
    '            line = line.strip()\n'
    '            if line.startswith("#") or "=" not in line:\n'
    '                continue\n'
    '            k, _, v = line.partition("=")\n'
    '            if k.strip() == key:\n'
    '                return v.strip().strip(\'"\').strip("\'")\n'
    '    except Exception:\n'
    '        pass\n'
    '    return None\n'
)
PATCHED_ENV = (
    'HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or pathlib.Path.home() / ".hermes")\n'
    '# Profile that owns this skill: scripts -> assign-to-<slug> -> skills -> <profile>.\n'
    'try:\n'
    '    PROFILE_DIR = HERE.parents[2]\n'
    'except Exception:\n'
    '    PROFILE_DIR = HERMES_HOME\n'
    '\n'
    '\n'
    'def _env_value(key):\n'
    '    # Read from the profile .env first (robust regardless of HERMES_HOME), then HERMES_HOME.\n'
    '    seen = set()\n'
    '    for env_file in (PROFILE_DIR / ".env", HERMES_HOME / ".env"):\n'
    '        if env_file in seen:\n'
    '            continue\n'
    '        seen.add(env_file)\n'
    '        try:\n'
    '            for line in env_file.read_text(encoding="utf-8").splitlines():\n'
    '                line = line.strip()\n'
    '                if line.startswith("#") or "=" not in line:\n'
    '                    continue\n'
    '                k, _, v = line.partition("=")\n'
    '                if k.strip() == key:\n'
    '                    return v.strip().strip(\'"\').strip("\'")\n'
    '        except Exception:\n'
    '            pass\n'
    '    return None\n'
)


def main():
    if len(sys.argv) < 2:
        print("ERROR: usage: patch_artist_delegate.py <path-to-delegate.py>")
        return 2
    path = pathlib.Path(sys.argv[1])
    if not path.is_file():
        print(f"ERROR: not a file: {path}")
        return 2
    src = path.read_text(encoding="utf-8")
    orig = src

    already_note = "--note" in src
    already_env = "PROFILE_DIR / \".env\"" in src or "PROFILE_DIR / '.env'" in src

    if already_note and already_env:
        print(f"ALREADY_PATCHED: {path} already has --note + robust token reading. No change.")
        return 0

    # 1) --note argument
    if not already_note:
        anchor = ANCHOR_NOTE_BEFORE + ANCHOR_NOTE_AFTER
        if anchor not in src:
            print("ERROR: could not find the argparse anchor (--prompt / --reset). Patch aborted.")
            return 2
        src = src.replace(anchor, ANCHOR_NOTE_BEFORE + NOTE_ARG + ANCHOR_NOTE_AFTER, 1)

    # 2) store the note in the brief (round 1) without sending it
    if "[INTERNAL NOTE" not in src:
        if ANCHOR_BRIEF not in src:
            print("ERROR: could not find the brief-storage anchor. Patch aborted.")
            return 2
        src = src.replace(ANCHOR_BRIEF, PATCHED_BRIEF, 1)

    # 3) robust token reading (PROFILE_DIR/.env then HERMES_HOME/.env)
    if not already_env:
        if ANCHOR_ENV not in src:
            print("ERROR: could not find the _env_value anchor. Token hardening aborted.")
            return 2
        src = src.replace(ANCHOR_ENV, PATCHED_ENV, 1)

    if src == orig:
        print(f"NO_CHANGE: {path} (nothing to do).")
        return 0

    # Validate it still compiles before writing.
    try:
        compile(src, str(path), "exec")
    except SyntaxError as e:
        print(f"ERROR: patched source failed to compile ({e}). NOT written.")
        return 2

    path.write_text(src, encoding="utf-8")
    print(f"PATCHED: {path} now supports --note (brief-only) + robust token reading.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
