#!/usr/bin/env python3
"""Continuous Yahoo-inbox watcher for Erin — runs check_inbox.py every EMAIL_POLL_INTERVAL.

This is the "she listens on Yahoo" loop. It's a plain background process (no Hermes
gateway) launched/stopped by the team launcher (manage.py reads it from team.json
"watchers"). Each pass is deterministic: new mail -> exclusive @erin wake-up; Erin
filters and reports only the important ones to the CEO.

Reads EMAIL_POLL_INTERVAL (seconds, default 120) from <HERMES_HOME>/.env.
HERMES_HOME must point at Erin's profile so .env + cache resolve correctly.
"""
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or pathlib.Path.home() / ".hermes" / "profiles" / "erin")
CHECK = HERE / "check_inbox.py"


def _env(key, default=None):
    f = HERMES_HOME / ".env"
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
    interval = int(_env("MAILBOX_POLL_INTERVAL") or _env("EMAIL_POLL_INTERVAL", "120") or 120)
    env = dict(os.environ)
    env["HERMES_HOME"] = str(HERMES_HOME)
    print(f"[inbox_watcher] start — every {interval}s, HERMES_HOME={HERMES_HOME}", flush=True)
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
