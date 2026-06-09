#!/usr/bin/env python3
"""Deterministic CEO -> copywriter handoff over Telegram. Cross-platform, stdlib-only.

Posts `<@worker> ROUND <n>: <brief>` into the copywriter's topic, via the CEO's own
bot token, with the mention + thread id taken from config (NOT typed by the LLM).
When --image <path> is given, the message is sent as a PHOTO with that text as the
caption, so the copywriter actually SEES the image and can write copy for it. Without
--image (revision/feedback rounds) it sends plain text.

Hard loop cap: a per-worker round counter in a state file. Auto-increments per call,
REFUSES after max_rounds (prints CAP_REACHED), resets after reset_gap seconds idle
(= a new task). The copywriter is gated (require_mention=true) and only this script
ever mentions him, so an infinite CEO<->copywriter loop is structurally impossible.

This script is installed at <ceo_profile>/skills/assign-to-<slug>/scripts/delegate.py,
so the owning CEO profile dir is three levels up — that is where the token/.env lives.

Config: reads `handoff.json` sitting one dir up (next to SKILL.md):
  {"worker_mention": "@<bot>", "thread_id": "<topic_id>",
   "max_rounds": 3, "reset_gap": 600}
Token + group chat id come from <ceo_profile>/.env
  (TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ALLOWED_CHATS).

Usage:
  delegate.py --prompt "BRIEF + copy instructions" --image /path/to/image.png
  delegate.py --prompt "feedback for the previous copy"      # revision round, no image
  delegate.py --reset
"""
import argparse
import json
import mimetypes
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import uuid

# Make Romanian (diacritics) output safe on any console, incl. Windows cp1252.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = pathlib.Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
# <profile>/skills/assign-to-<slug>/scripts/delegate.py -> profile dir is 3 up.
PROFILE_DIR = HERE.parents[2]
HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or PROFILE_DIR)
CAPTION_LIMIT = 1000  # Telegram caption hard cap is 1024; stay safely under.


def _env_value(key):
    candidates = [PROFILE_DIR / ".env", HERMES_HOME / ".env"]
    seen = set()
    for env_file in candidates:
        if env_file in seen:
            continue
        seen.add(env_file)
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
        except Exception:
            continue
    return None


def _load_cfg():
    cfg = {"worker_mention": "", "thread_id": "", "max_rounds": 3, "reset_gap": 600}
    for f in (SKILL_DIR / "handoff.json", HERE / "handoff.json"):
        try:
            cfg.update(json.loads(f.read_text(encoding="utf-8")))
            break
        except Exception:
            continue
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
        return {"round": 0, "ts": 0, "brief": ""}


def _post_text(token, payload):
    data = urllib.parse.urlencode(payload).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=data, timeout=20) as r:
        return json.loads(r.read().decode("utf-8")).get("ok", False)


def _post_photo(token, chat_id, thread, caption, image_path):
    """multipart/form-data sendPhoto, stdlib-only."""
    boundary = "----hermes" + uuid.uuid4().hex
    fields = {"chat_id": str(chat_id), "caption": caption}
    if thread and thread not in ("", "None", "1"):
        fields["message_thread_id"] = str(thread)
    img = pathlib.Path(image_path)
    ctype = mimetypes.guess_type(img.name)[0] or "application/octet-stream"
    body = bytearray()
    for k, v in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        body += f"{v}\r\n".encode()
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="photo"; filename="{img.name}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode()
    body += img.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    req = urllib.request.Request(url, data=bytes(body))
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8")).get("ok", False)


def main():
    cfg = _load_cfg()
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt")
    ap.add_argument("--image", help="local path to the image to send the copywriter (round 1)")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--show-brief", action="store_true",
                    help="print the stored ROUND 1 brief/criteria for the current task")
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
        state_file.write_text(json.dumps({"round": 0, "ts": time.time(), "brief": ""}))
        print(f"RESET: round counter for {worker} cleared. Next delegation will be ROUND 1.")
        return

    if a.show_brief:
        brief = (_load_state(state_file) or {}).get("brief", "")
        if brief:
            print(f"CURRENT_BRIEF (criteriile pe care le-ai trimis workerului):\n{brief}")
        else:
            print("NO_BRIEF: niciun brief stocat (probabil n-ai delegat încă pentru acest task).")
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
        st = {"round": 0, "ts": now, "brief": ""}

    nxt = st.get("round", 0) + 1
    if nxt > a.max_rounds:
        print(
            f"CAP_REACHED: {a.max_rounds} rounds already used for this task. "
            f"Do NOT delegate to {worker} again — take the best copy so far, "
            "deliver the image + copy to the user in the General topic, and stop."
        )
        return

    # Persist the ROUND 1 brief so the review turn (a SEPARATE topic session with NO General
    # context) can recall the criteria via --show-brief.
    brief = st.get("brief", "") or ""
    if nxt == 1:
        brief = a.prompt

    text = f"{worker} ROUND {nxt}: {a.prompt}"

    try:
        if a.image:
            img = pathlib.Path(a.image)
            if not img.is_file():
                print(f"ERROR: image not found: {a.image}")
                return
            caption = text if len(text) <= CAPTION_LIMIT else text[: CAPTION_LIMIT - 1] + "…"
            ok = _post_photo(token, chat_id, a.thread, caption, str(img))
        else:
            payload = {"chat_id": chat_id, "text": text}
            if a.thread and a.thread not in ("", "None", "1"):
                payload["message_thread_id"] = a.thread
            ok = _post_text(token, payload)
    except Exception as e:
        print(f"ERROR: failed to send to Telegram: {e}")
        return

    if not ok:
        print("ERROR: Telegram rejected the message (check token / chat id / thread / image).")
        return

    state_file.write_text(json.dumps({"round": nxt, "ts": now, "brief": brief}))
    kind = "with image" if a.image else "feedback only"
    print(f"DELEGATED ROUND {nxt} to {worker} ({kind}). (cap {a.max_rounds}) Now wait for his copy.")


if __name__ == "__main__":
    main()
