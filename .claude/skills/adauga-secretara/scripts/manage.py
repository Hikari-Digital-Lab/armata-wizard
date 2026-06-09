#!/usr/bin/env python3
"""Cross-platform launcher for the Hermes gateway team (Windows / macOS / Linux).

start | stop | restart | status | logs <profile> | fresh

- Each profile runs its own `hermes -p <profile> gateway run --replace`
  (distinct bot tokens => no Telegram 409 polling conflict).
- Uses psutil to find/stop processes by cmdline (no pkill/pgrep needed).
- `fresh` = stop + wipe each profile's chat sessions + clear handoff state + start
  (use after changing language/persona, since the model otherwise mirrors old history).

Team: reads the profile list from `team.json` next to this script:
  {"profiles": ["michael", "pam"]}
Falls back to env HERMES_TEAM_PROFILES (comma list), then ["michael", "pam"].
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

try:
    import psutil
except ImportError:
    sys.exit("ERROR: psutil not installed. Run:  <hermes-venv-python> -m pip install psutil")

HERE = pathlib.Path(__file__).resolve().parent
HERMES_DIR = pathlib.Path.home() / ".hermes"
LOG_DIR = HERMES_DIR / "office-logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def profiles():
    f = HERE / "team.json"
    try:
        p = json.loads(f.read_text(encoding="utf-8")).get("profiles")
        if p:
            return list(p)
    except Exception:
        pass
    env = os.environ.get("HERMES_TEAM_PROFILES")
    if env:
        return [x.strip() for x in env.split(",") if x.strip()]
    return ["michael", "pam"]


def watchers():
    """Optional background helper scripts (absolute paths) from team.json "watchers".

    These are plain Python loops (e.g. an inbox poller), NOT hermes gateways. They start
    and stop with the team. Backward compatible: no "watchers" key => none."""
    f = HERE / "team.json"
    try:
        w = json.loads(f.read_text(encoding="utf-8")).get("watchers")
        if w:
            return [str(x) for x in w]
    except Exception:
        pass
    return []


def _watcher_procs(path):
    out = []
    for pr in psutil.process_iter(["cmdline"]):
        try:
            cl = pr.info["cmdline"] or []
        except Exception:
            continue
        if path in " ".join(cl):
            out.append(pr)
    return out


def hermes_bin():
    b = shutil.which("hermes")
    if b:
        return b
    for cand in (
        pathlib.Path.home() / ".local" / "bin" / "hermes",
        pathlib.Path.home() / "AppData" / "Roaming" / "Python" / "Scripts" / "hermes.exe",
    ):
        if cand.exists():
            return str(cand)
    sys.exit("ERROR: 'hermes' not found on PATH. Install Hermes Agent first.")


def _procs_for(profile):
    out = []
    for pr in psutil.process_iter(["cmdline"]):
        try:
            cl = pr.info["cmdline"] or []
        except Exception:
            continue
        s = " ".join(cl)
        if "gateway" in s and "run" in s and f"-p {profile} " in (s + " "):
            out.append(pr)
    return out


def start():
    hb = hermes_bin()
    for p in profiles():
        if _procs_for(p):
            print(f"[{p}] already running")
            continue
        logf = open(LOG_DIR / f"{p}.log", "ab")
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = 0x00000200 | 0x00000008  # NEW_PROCESS_GROUP | DETACHED
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen(
            [hb, "-p", p, "gateway", "run", "--replace"],
            stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kwargs,
        )
        print(f"[{p}] starting...")
        time.sleep(1)
    for w in watchers():
        name = pathlib.Path(w).stem
        if _watcher_procs(w):
            print(f"[watcher:{name}] already running")
            continue
        if not pathlib.Path(w).exists():
            print(f"[watcher:{name}] MISSING ({w}) — skipped")
            continue
        logf = open(LOG_DIR / f"watcher-{name}.log", "ab")
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = 0x00000200 | 0x00000008
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen(
            [sys.executable, w],
            stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kwargs,
        )
        print(f"[watcher:{name}] starting...")
    print("---")
    status()


def stop():
    for p in profiles():
        procs = _procs_for(p)
        if not procs:
            print(f"[{p}] not running")
            continue
        for pr in procs:
            try:
                pr.terminate()
            except Exception:
                pass
        _, alive = psutil.wait_procs(procs, timeout=25)
        for pr in alive:
            try:
                pr.kill()
            except Exception:
                pass
        print(f"[{p}] stopped")
    for w in watchers():
        name = pathlib.Path(w).stem
        procs = _watcher_procs(w)
        if not procs:
            print(f"[watcher:{name}] not running")
            continue
        for pr in procs:
            try:
                pr.terminate()
            except Exception:
                pass
        _, alive = psutil.wait_procs(procs, timeout=15)
        for pr in alive:
            try:
                pr.kill()
            except Exception:
                pass
        print(f"[watcher:{name}] stopped")


def status():
    for p in profiles():
        procs = _procs_for(p)
        if procs:
            print(f"[{p}] RUNNING (pids: {', '.join(str(x.pid) for x in procs)})")
        else:
            print(f"[{p}] stopped")
    for w in watchers():
        name = pathlib.Path(w).stem
        procs = _watcher_procs(w)
        if procs:
            print(f"[watcher:{name}] RUNNING (pids: {', '.join(str(x.pid) for x in procs)})")
        else:
            print(f"[watcher:{name}] stopped")


def logs(which=None):
    which = which or profiles()[0]
    f = LOG_DIR / f"{which}.log"
    if not f.exists():
        print(f"(no log yet at {f})")
        return
    data = f.read_text(encoding="utf-8", errors="replace").splitlines()
    print("\n".join(data[-60:]))


def fresh():
    """Stop, wipe sessions + handoff state, start — for a clean (e.g. language) reset."""
    stop()
    time.sleep(2)
    hb = hermes_bin()
    for p in profiles():
        # delete chat sessions
        try:
            listed = subprocess.run(
                [hb, "-p", p, "sessions", "list"],
                capture_output=True, text=True, timeout=30,
            ).stdout
            import re
            for sid in sorted(set(re.findall(r"\d{8}_\d{6}_[0-9a-f]+", listed))):
                subprocess.run([hb, "-p", p, "sessions", "delete", sid, "--yes"],
                               capture_output=True, timeout=30)
        except Exception:
            pass
        # reset the session map + handoff state
        sj = HERMES_DIR / "profiles" / p / "sessions" / "sessions.json"
        try:
            if sj.parent.exists():
                sj.write_text("{}")
        except Exception:
            pass
        cache = HERMES_DIR / "profiles" / p / "cache"
        if cache.exists():
            for hs in cache.glob("handoff_*.json"):
                try:
                    hs.unlink()
                except Exception:
                    pass
        print(f"[{p}] sessions + handoff cleared")
    time.sleep(1)
    start()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "restart":
        stop(); time.sleep(2); start()
    elif cmd == "status":
        status()
    elif cmd == "logs":
        logs(arg)
    elif cmd == "fresh":
        fresh()
    else:
        print("usage: manage.py {start|stop|restart|status|logs <profile>|fresh}")
        sys.exit(1)


if __name__ == "__main__":
    main()
