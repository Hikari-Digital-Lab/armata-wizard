#!/usr/bin/env python3
"""Continuous inbox watcher — runs check_inbox.py every MAILBOX_POLL_INTERVAL seconds.

This is the "she listens on the mailbox" loop. It's a plain background process (NOT a Hermes
gateway) launched/stopped by the team launcher (manage.py reads it from team.json "watchers").
Each pass is deterministic: new mail -> exclusive @secretary wake-up; she filters and reports
only the important ones to the CEO.

Self-locating: derives the profile dir from its own path
(<profile>/skills/email-studio/scripts/inbox_watcher.py -> up 3), so no slug is hardcoded.
Reads MAILBOX_POLL_INTERVAL (seconds, default 120) from <profile>/.env.
"""
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
PROFILE = pathlib.Path(os.environ.get("HERMES_HOME") or pathlib.Path(__file__).resolve().parents[3])
CHECK = HERE / "check_inbox.py"


def _env(key, default=None):
    f = PROFILE / ".env"
    try:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return default


def main():
    interval = int(_env("MAILBOX_POLL_INTERVAL", "120") or 120)
    env = dict(os.environ)
    env["HERMES_HOME"] = str(PROFILE)
    print(f"[inbox_watcher] start — every {interval}s, HERMES_HOME={PROFILE}", flush=True)
    while True:
        try:
            r = subprocess.run(
                [sys.executable, str(CHECK)],
                env=env, capture_output=True, text=True, timeout=120,
            )
            out = (r.stdout or "").strip()
            err = (r.stderr or "").strip()
            if out:
                print(f"[inbox_watcher] {out}", flush=True)
            if err:
                print(f"[inbox_watcher][err] {err}", flush=True)
        except Exception as e:
            print(f"[inbox_watcher] pass failed: {e}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
