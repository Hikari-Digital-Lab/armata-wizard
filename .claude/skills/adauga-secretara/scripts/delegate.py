#!/usr/bin/env python3
"""Deterministic CEO -> worker handoff over Telegram. Cross-platform, stdlib-only.

Posts `<@worker> ROUND <n>: <prompt>` into the worker's topic, via the CEO's own
bot token, with the mention + thread id taken from config (NOT typed by the LLM).
This guarantees the worker is triggered every time, even if the model "forgets"
to write the @handle.

Hard loop cap: a per-worker round counter in a state file. Auto-increments per
call, REFUSES after max_rounds (prints CAP_REACHED), resets after reset_gap
seconds idle (= a new task). With workers gated (require_mention=true) and only
this script ever mentioning them, an infinite loop is structurally impossible.

Config: reads `handoff.json` sitting NEXT TO this script:
  {"worker_mention": "@pam_beesly_art_bot", "thread_id": "2",
   "max_rounds": 3, "reset_gap": 600}
Token + group chat id come from <HERMES_HOME>/.env
  (TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ALLOWED_CHATS).
Any field can be overridden via CLI flags.

Usage:
  delegate.py --prompt "ENGLISH image prompt or feedback"
  delegate.py --reset
"""
import argparse
import json
import os
import pathlib
import re
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or pathlib.Path.home() / ".hermes")


def _env_value(key):
    env_file = HERMES_HOME / ".env"
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return None


def _load_cfg():
    cfg = {"worker_mention": "", "thread_id": "", "max_rounds": 3, "reset_gap": 600}
    f = HERE / "handoff.json"
    try:
        cfg.update(json.loads(f.read_text(encoding="utf-8")))
    except Exception:
        pass
    return cfg


def _state_path(worker_mention):
    slug = re.sub(r"[^a-z0-9]+", "_", worker_mention.lower()).strip("_") or "worker"
    d = HERMES_HOME / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"handoff_{slug}.json"


def _load_state(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"round": 0, "ts": 0}


def main():
    cfg = _load_cfg()
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--worker", default=cfg["worker_mention"])
    ap.add_argument("--thread", default=str(cfg["thread_id"]))
    ap.add_argument("--max-rounds", type=int, default=int(cfg["max_rounds"]))
    ap.add_argument("--reset-gap", type=int, default=int(cfg["reset_gap"]))
    ap.add_argument("--chat", default=None)
    a = ap.parse_args()

    worker = a.worker
    if not worker:
        raise SystemExit("ERROR: no worker mention (set handoff.json worker_mention or --worker)")

    state_file = _state_path(worker)

    if a.reset:
        state_file.write_text(json.dumps({"round": 0, "ts": time.time()}))
        print(f"RESET: round counter for {worker} cleared. Next delegation will be ROUND 1.")
        return

    if not a.prompt:
        raise SystemExit("ERROR: --prompt is required")

    token = _env_value("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("ERROR: no TELEGRAM_BOT_TOKEN in profile .env")
    chat_id = a.chat or (_env_value("TELEGRAM_GROUP_ALLOWED_CHATS") or "").split(",")[0].strip()
    if not chat_id:
        raise SystemExit("ERROR: no chat id (TELEGRAM_GROUP_ALLOWED_CHATS or --chat)")

    st = _load_state(state_file)
    now = time.time()
    if now - st.get("ts", 0) > a.reset_gap:
        st = {"round": 0, "ts": now}

    nxt = st.get("round", 0) + 1
    if nxt > a.max_rounds:
        print(
            f"CAP_REACHED: {a.max_rounds} rounds already used for this task. "
            f"Do NOT delegate to {worker} again — pick the best result so far, "
            "deliver it to the user in the General topic, and stop."
        )
        return

    text = f"{worker} ROUND {nxt}: {a.prompt}"
    payload = {"chat_id": chat_id, "text": text}
    if a.thread and a.thread not in ("", "None", "1"):
        payload["message_thread_id"] = a.thread
    data = urllib.parse.urlencode(payload).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with urllib.request.urlopen(url, data=data, timeout=20) as r:
            ok = json.loads(r.read().decode("utf-8")).get("ok", False)
    except Exception as e:
        print(f"ERROR: failed to send to Telegram: {e}")
        return
    if not ok:
        print("ERROR: Telegram rejected the message (check token / chat id / thread).")
        return

    state_file.write_text(json.dumps({"round": nxt, "ts": now}))
    print(f"DELEGATED ROUND {nxt} to {worker}. (cap {a.max_rounds}) Now wait for the result.")


if __name__ == "__main__":
    main()
