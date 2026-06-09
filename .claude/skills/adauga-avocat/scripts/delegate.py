#!/usr/bin/env python3
"""Deterministic CEO -> worker handoff over Telegram (config-driven, text-first).

Posts `<@worker> ROUND <n>: <brief>` into Ryan's Copywriting topic, via Michael's
own bot token, with the mention + thread id taken from config (NOT typed by the
LLM). When --image <path> is given, the message is sent as a PHOTO with that text
as the caption, so Ryan actually SEES the image Pam made and can write copy for it.
Without --image (revision/feedback rounds) it sends plain text.

Hard loop cap: a per-worker round counter in a state file. Auto-increments per
call, REFUSES after max_rounds (prints CAP_REACHED), resets after reset_gap
seconds idle (= a new task). Ryan is gated (require_mention=true) and only this
script ever mentions him, so an infinite Michael<->Ryan loop is impossible.

Config: reads `handoff.json` sitting NEXT TO this script (one dir up from scripts/):
  {"worker_mention": "@ryan_howard_copy_bot", "thread_id": "289",
   "max_rounds": 3, "reset_gap": 600}
Token + group chat id come from <HERMES_HOME>/.env
  (TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ALLOWED_CHATS).

Usage:
  delegate.py --prompt "BRIEF + copy instructions" --image /path/to/pam_image.png
  delegate.py --prompt "feedback for the previous copy"      # revision round, no image
  delegate.py --reset
"""
import argparse
import json
import mimetypes
import os
import pathlib
import re
import time
import urllib.parse
import urllib.request
import uuid

HERE = pathlib.Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
# This script lives at <profile>/skills/assign-to-ryan/scripts/delegate.py, so the owning
# profile dir is three levels up — the most reliable source of the .env / token.
PROFILE_DIR = HERE.parents[2]
CAPTION_LIMIT = 1000  # Telegram caption hard cap is 1024; stay safely under.

# State (round counter) lives under the Hermes home, like the proven assign-to-pam script.
HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or PROFILE_DIR)


def _env_value(key):
    candidates = [
        PROFILE_DIR / ".env",
        HERMES_HOME / ".env",
    ]
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
        return {"round": 0, "ts": 0}


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


def _post_album(token, chat_id, thread, caption, image_paths):
    """sendMediaGroup with multiple photos; caption on the first item."""
    boundary = "----hermes" + uuid.uuid4().hex
    media = []
    file_parts = []
    for i, path in enumerate(image_paths):
        attach = f"file{i}"
        item = {"type": "photo", "media": f"attach://{attach}"}
        if i == 0 and caption:
            item["caption"] = caption
        media.append(item)
        file_parts.append((attach, pathlib.Path(path)))
    fields = {"chat_id": str(chat_id), "media": json.dumps(media)}
    if thread and thread not in ("", "None", "1"):
        fields["message_thread_id"] = str(thread)
    body = bytearray()
    for k, v in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        body += f"{v}\r\n".encode()
    for attach, img in file_parts:
        ctype = mimetypes.guess_type(img.name)[0] or "application/octet-stream"
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{attach}"; filename="{img.name}"\r\n'.encode()
        body += f"Content-Type: {ctype}\r\n\r\n".encode()
        body += img.read_bytes()
        body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    req = urllib.request.Request(url, data=bytes(body))
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8")).get("ok", False)


def main():
    cfg = _load_cfg()
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt")
    ap.add_argument("--image", action="append", default=[],
                    help="local path to an image to send Ryan (round 1); repeatable for 2-3 site images")
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
            f"Do NOT delegate to {worker} again — take the best analysis so far and "
            "deliver it to the user with deliver_verdict.py, then stop."
        )
        return

    text = f"{worker} ROUND {nxt}: {a.prompt}"

    try:
        if a.image:
            for p in a.image:
                if not pathlib.Path(p).is_file():
                    print(f"ERROR: image not found: {p}")
                    return
            caption = text if len(text) <= CAPTION_LIMIT else text[: CAPTION_LIMIT - 1] + "…"
            if len(a.image) == 1:
                ok = _post_photo(token, chat_id, a.thread, caption, str(a.image[0]))
            else:
                ok = _post_album(token, chat_id, a.thread, caption, [str(p) for p in a.image])
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

    state_file.write_text(json.dumps({"round": nxt, "ts": now}))
    kind = "with image" if a.image else "feedback only"
    print(f"DELEGATED ROUND {nxt} to {worker} ({kind}). (cap {a.max_rounds}) Now wait for his reply.")


if __name__ == "__main__":
    main()
