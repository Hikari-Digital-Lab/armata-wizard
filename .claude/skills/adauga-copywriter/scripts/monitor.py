#!/usr/bin/env python3
"""Runaway auto-kill monitor for a Hermes bot team. Cross-platform, stdlib-only.

Watches each profile's gateway.log and counts outbound deliveries ("Sending response").
If the team produces more than `--max-deliveries` NEW deliveries within `--window`
seconds (a runaway loop), it calls `manage.py stop` to kill every gateway, prints a
RUNAWAY alert, and exits non-zero. Otherwise it runs for the window and exits 0.

Use it as a safety net while you run a controlled CEO->copywriter test: a healthy,
capped exchange stays well under the threshold; a loop trips it.

Usage:
  monitor.py --python <venv_python> --manage <path/to/manage.py> \
             --profiles michael,pam,ryan --max-deliveries 5 --window 180
The threshold should be (sum of per-worker caps) + 1, e.g. cap 3 + a couple workers => ~5.
"""
import argparse
import pathlib
import subprocess
import sys
import time

HERMES_PROFILES = pathlib.Path.home() / ".hermes" / "profiles"


def _delivery_count(profile):
    log = HERMES_PROFILES / profile / "logs" / "gateway.log"
    try:
        n = 0
        with log.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "Sending response" in line:
                    n += 1
        return n
    except Exception:
        return 0


def _total(profiles):
    return {p: _delivery_count(p) for p in profiles}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", required=True, help="venv python that runs manage.py")
    ap.add_argument("--manage", required=True, help="path to the live team's manage.py")
    ap.add_argument("--profiles", required=True, help="comma list, e.g. michael,pam,ryan")
    ap.add_argument("--max-deliveries", type=int, default=5,
                    help="kill if NEW deliveries across the team exceed this within the window")
    ap.add_argument("--window", type=int, default=180, help="seconds to watch")
    ap.add_argument("--poll", type=int, default=5, help="seconds between checks")
    a = ap.parse_args()

    profiles = [p.strip() for p in a.profiles.split(",") if p.strip()]
    base = _total(profiles)
    base_sum = sum(base.values())
    print(f"MONITOR: watching {profiles} for {a.window}s; "
          f"runaway threshold = {a.max_deliveries} new deliveries. Baseline={base_sum}.")

    deadline = time.time() + a.window
    while time.time() < deadline:
        time.sleep(a.poll)
        cur = _total(profiles)
        new = sum(cur.values()) - base_sum
        per = ", ".join(f"{p}:{cur[p]-base[p]}" for p in profiles)
        print(f"MONITOR: +{new} new deliveries ({per})")
        if new > a.max_deliveries:
            print(f"🚨 RUNAWAY DETECTED: {new} deliveries > {a.max_deliveries}. Killing team.")
            try:
                subprocess.run([a.python, a.manage, "stop"], timeout=60)
            except Exception as e:
                print(f"MONITOR: failed to stop team automatically: {e}")
            sys.exit(2)

    cur = _total(profiles)
    new = sum(cur.values()) - base_sum
    print(f"MONITOR: OK — window elapsed, {new} new deliveries total (<= {a.max_deliveries}). "
          "No runaway.")
    sys.exit(0)


if __name__ == "__main__":
    main()
