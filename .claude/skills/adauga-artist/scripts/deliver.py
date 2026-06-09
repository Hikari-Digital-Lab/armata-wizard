#!/usr/bin/env python3
"""Deterministic FINAL delivery: post the artist's approved image into the General topic.

Why this exists: when the artist posts an image in the Art topic, the CEO (Michael) is
triggered in the *Art* session and, with native vision, only receives the image PIXELS —
NOT the local file path. So he cannot echo a `MEDIA:<path>` to cross-post into General.
This script does the cross-topic hop deterministically: it uploads the approved image to
the group's **General** topic (no message_thread_id) via the CEO bot token, with a caption.

Image selection (robust — no "newest *.png" guessing, which broke on .jpg / stale caches):
  1. --file <abs path>            (explicit override; always wins)
  2. <artist_images_dir>/last_image.txt   (stable pointer written by gen_image.py)
  3. newest *.png / *.jpg / *.jpeg in <artist_images_dir>   (last-resort fallback)

Idempotency: the two per-topic CEO sessions can both reach delivery. We hash the image
bytes and skip a re-send of the SAME image within 30 minutes (anti-duplicate lock).

Config (deliver.json next to this script):
  {"artist_images_dir": "<abs path to artist cache/images>", "general_thread_id": ""}
Token + group chat id are read from the CEO profile's .env (derived from this script's path).

Usage:
  deliver.py --caption "CEO's proud caption, in the team language"
  deliver.py --caption "..." --file /abs/path/to/specific.png
"""
import argparse
import hashlib
import json
import mimetypes
import os
import pathlib
import sys
import time
import urllib.request
import uuid

# Make Romanian (diacritics) output safe on any console, incl. Windows cp1252.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = pathlib.Path(__file__).resolve().parent
PROFILE_DIR = HERE.parents[2]            # <ceo_profile>/skills/assign-to-<slug>/scripts → profile


def _env_value(key):
    env_file = PROFILE_DIR / ".env"
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


def _cfg():
    cfg = {"artist_images_dir": "", "general_thread_id": "", "worker_mention": ""}
    try:
        cfg.update(json.loads((HERE / "deliver.json").read_text(encoding="utf-8")))
    except Exception:
        pass
    return cfg


def _reset_round_counter(worker_mention):
    """After a successful delivery the task is DONE — clear the delegate round counter so the
    NEXT brief starts clean at ROUND 1 (kills the 'counter leak' between consecutive tasks)."""
    if not worker_mention:
        return
    import re
    slug = re.sub(r"[^a-z0-9]+", "_", worker_mention.lower()).strip("_") or "worker"
    state = PROFILE_DIR / "cache" / f"handoff_{slug}.json"
    try:
        state.write_text(json.dumps({"round": 0, "ts": int(time.time()), "brief": ""}),
                         encoding="utf-8")
    except Exception:
        pass


def _from_pointer(images_dir):
    try:
        p = (pathlib.Path(images_dir) / "last_image.txt").read_text(encoding="utf-8").strip()
        if p and pathlib.Path(p).is_file():
            return p
    except Exception:
        pass
    return None


def _newest(images_dir):
    d = pathlib.Path(images_dir)
    imgs = []
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        imgs.extend(d.glob(ext))
    imgs = [f for f in imgs if f.name != "last_image.txt"]
    if not imgs:
        return None
    return str(sorted(imgs, key=lambda f: f.stat().st_mtime, reverse=True)[0])


def _send_photo(token, chat_id, caption, thread, img):
    boundary = "----hermes" + uuid.uuid4().hex
    crlf = b"\r\n"
    fields = {"chat_id": str(chat_id)}
    if caption:
        fields["caption"] = caption
    # General topic = NO message_thread_id. Only set a thread if explicitly configured.
    if thread and str(thread) not in ("", "None", "1"):
        fields["message_thread_id"] = str(thread)
    body = bytearray()
    for k, v in fields.items():
        body += b"--" + boundary.encode() + crlf
        body += f'Content-Disposition: form-data; name="{k}"'.encode() + crlf + crlf
        body += str(v).encode("utf-8") + crlf
    name = os.path.basename(img)
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    body += b"--" + boundary.encode() + crlf
    body += f'Content-Disposition: form-data; name="photo"; filename="{name}"'.encode() + crlf
    body += f"Content-Type: {ctype}".encode() + crlf + crlf
    body += pathlib.Path(img).read_bytes() + crlf
    body += b"--" + boundary.encode() + b"--" + crlf
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    req = urllib.request.Request(url, data=bytes(body))
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8")).get("ok", False)
    except Exception as e:
        print(f"ERROR: failed to send photo to Telegram: {e}")
        return False


def main():
    cfg = _cfg()
    ap = argparse.ArgumentParser()
    ap.add_argument("--caption", default="")
    ap.add_argument("--file", default=None)
    ap.add_argument("--images-dir", default=cfg["artist_images_dir"])
    ap.add_argument("--thread", default=str(cfg["general_thread_id"]))
    a = ap.parse_args()

    img = a.file or _from_pointer(a.images_dir) or _newest(a.images_dir)
    if not img or not os.path.isfile(img):
        raise SystemExit(
            f"ERROR: no image to deliver (looked at pointer + newest in {a.images_dir!r}, "
            f"--file={a.file!r}). Pass --file <abs path> explicitly."
        )

    token = _env_value("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("ERROR: no TELEGRAM_BOT_TOKEN in CEO profile .env")
    chat_id = (_env_value("TELEGRAM_GROUP_ALLOWED_CHATS") or "").split(",")[0].strip()
    if not chat_id:
        raise SystemExit("ERROR: no chat id (TELEGRAM_GROUP_ALLOWED_CHATS)")

    # Idempotency: never deliver the SAME image twice (both per-topic CEO sessions can reach here).
    digest = hashlib.sha256(pathlib.Path(img).read_bytes()).hexdigest()[:16]
    lock = PROFILE_DIR / "cache" / ".delivered_image.json"
    lock.parent.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    try:
        prev = json.loads(lock.read_text(encoding="utf-8"))
    except Exception:
        prev = {}
    if prev.get("digest") == digest and (now - int(prev.get("ts", 0))) < 1800:
        print(f"SKIP: această imagine a fost deja livrată acum {now - int(prev.get('ts', 0))}s "
              "(anti-duplicat). Nu o retrimit.")
        return

    ok = _send_photo(token, chat_id, a.caption, a.thread, img)
    if not ok:
        raise SystemExit("ERROR: Telegram rejected the photo (check token / chat id).")
    try:
        lock.write_text(json.dumps({"digest": digest, "ts": now}), encoding="utf-8")
    except Exception:
        pass
    _reset_round_counter(cfg.get("worker_mention", ""))  # task done → next brief starts at ROUND 1
    print(f"DELIVERED to General: {os.path.basename(img)}. DONE — do NOT post anything else.")


if __name__ == "__main__":
    main()
