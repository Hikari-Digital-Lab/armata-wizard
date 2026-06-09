#!/usr/bin/env python3
"""Package a finished landing job into a .zip AND deliver it to the General topic.

After the web developer writes index.html into the job dir (which already contains the
artist's images), this script zips index.html + the image files (flat, side by side, so
the HTML's relative basenames resolve). Then — DETERMINISTICALLY — it posts the zip as a
document into the **General** topic via the CEO's own bot token.

Why deliver here (not "print MEDIA and let the CEO post it"): the CEO is triggered in the
web-dev topic session and a `MEDIA:` line in his reply would land in THAT topic, not General
(cross-topic). Posting from this script via sendDocument fixes that, exactly like the artist's
deliver.py and the avocat's deliver_verdict.py.

The job dir defaults to the most recent job_* under the CEO's cache/landing/. The zip is named
deterministically per job (landing_<jobname>.zip) and rebuilt only when index.html changed.
An anti-duplicate lock skips re-sending the same zip within 30 min (the two per-topic CEO
sessions can both reach delivery). On a successful delivery the worker round counters are reset
so the next landing job starts clean.

Usage:
  package.py --caption "Gata landing-ul!"        # zip the latest job + deliver to General
  package.py --jobdir /abs/job_dir --caption ".."
  package.py --no-deliver                        # only build the zip, print MEDIA: (legacy)
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
import zipfile

# Make Romanian (diacritics) output safe on any console, incl. Windows cp1252.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = pathlib.Path(__file__).resolve().parent
PROFILE_DIR = HERE.parents[2]  # <profile>/skills/package-landing/scripts/package.py
HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or PROFILE_DIR)
LANDING_ROOT = HERMES_HOME / "cache" / "landing"

EXCLUDE_NAMES = {"BRIEF.md"}  # build inputs, not part of the deliverable
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
CAPTION_LIMIT = 1024


def _latest_jobdir():
    if not LANDING_ROOT.is_dir():
        return None
    jobs = [p for p in LANDING_ROOT.glob("job_*") if p.is_dir()]
    return max(jobs, key=lambda p: p.stat().st_mtime) if jobs else None


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


def _send_document(token, chat_id, caption, doc_path, thread=""):
    boundary = "----hermes" + uuid.uuid4().hex
    fields = {"chat_id": str(chat_id)}
    if caption:
        fields["caption"] = caption[:CAPTION_LIMIT]
    if thread and str(thread) not in ("", "None", "1"):
        fields["message_thread_id"] = str(thread)
    doc = pathlib.Path(doc_path)
    ctype = mimetypes.guess_type(doc.name)[0] or "application/zip"
    body = bytearray()
    for k, v in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        body += f"{v}\r\n".encode()
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="document"; filename="{doc.name}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode()
    body += doc.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    req = urllib.request.Request(url, data=bytes(body))
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8")).get("ok", False)
    except Exception as exc:
        print(f"ERROR: Telegram sendDocument failed: {exc}")
        return False


def _reset_round_counters():
    """The whole landing task (artist + copywriter + dev) is done — reset every worker's round
    counter so the next job starts clean at ROUND 1 (kills the counter leak)."""
    cache = PROFILE_DIR / "cache"
    try:
        for f in cache.glob("handoff_*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                data = {}
            data.update({"round": 0, "ts": int(time.time())})
            f.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass


def _build_zip(jobdir):
    index = jobdir / "index.html"
    if not index.is_file():
        print(
            f"ERROR: {index} not found — the developer hasn't written the HTML yet. "
            "Wait for his HTML:<path> reply before packaging."
        )
        return None, []
    members = []
    for p in sorted(jobdir.iterdir()):
        if not p.is_file() or p.name in EXCLUDE_NAMES:
            continue
        if p.name == "index.html" or p.suffix.lower() in IMAGE_EXTS:
            members.append(p)
    out = LANDING_ROOT / f"landing_{jobdir.name}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.is_file() and out.stat().st_mtime >= index.stat().st_mtime:
        return out, members  # reuse up-to-date zip
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in members:
            z.write(p, arcname=p.name)  # flat: index.html + images side by side
    return out, members


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobdir", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--caption", default="", help="short proud message posted with the zip in General")
    ap.add_argument("--no-deliver", action="store_true", help="only build the zip, print MEDIA (legacy)")
    a = ap.parse_args()

    jobdir = pathlib.Path(a.jobdir) if a.jobdir else _latest_jobdir()
    if not jobdir or not jobdir.is_dir():
        print("ERROR: no landing job dir found. Run the assign-to-<dev> skill first (it creates one).")
        return

    out, members = _build_zip(jobdir)
    if not out:
        return
    if a.out:
        out_override = pathlib.Path(a.out)
        out_override.parent.mkdir(parents=True, exist_ok=True)
        out_override.write_bytes(out.read_bytes())
        out = out_override
    imgs = [p.name for p in members if p.name != "index.html"]

    if a.no_deliver:
        print(f"PACKAGED {len(members)} files (index.html + {len(imgs)} image(s): {', '.join(imgs)})")
        print(f"MEDIA:{out}")
        print("Post that MEDIA line in the General topic with a short proud message; then stop.")
        return

    token = _env_value("TELEGRAM_BOT_TOKEN")
    chat_id = (_env_value("TELEGRAM_GROUP_ALLOWED_CHATS") or "").split(",")[0].strip()
    if not token or not chat_id:
        print("ERROR: no TELEGRAM_BOT_TOKEN / chat id in CEO .env. Falling back to MEDIA print.")
        print(f"MEDIA:{out}")
        return

    # Anti-duplicate: skip re-sending the SAME zip within 30 min.
    digest = hashlib.sha256(out.read_bytes()).hexdigest()[:16]
    lock = PROFILE_DIR / "cache" / ".delivered_landing.json"
    lock.parent.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    try:
        prev = json.loads(lock.read_text(encoding="utf-8"))
    except Exception:
        prev = {}
    if prev.get("digest") == digest and (now - int(prev.get("ts", 0))) < 1800:
        print(f"SKIP: acest landing a fost deja livrat acum {now - int(prev.get('ts', 0))}s (anti-duplicat).")
        return

    caption = a.caption or f"Gata landing-ul! ({len(members)} fișiere: index.html + {len(imgs)} imagini)"
    ok = _send_document(token, chat_id, caption, str(out))
    if not ok:
        print("ERROR: delivery failed — zip built but not posted.")
        print(f"MEDIA:{out}")
        return
    try:
        lock.write_text(json.dumps({"digest": digest, "ts": now}), encoding="utf-8")
    except Exception:
        pass
    _reset_round_counters()
    print(f"DELIVERED to General: {out.name} (index.html + {len(imgs)} image(s)). DONE — do NOT post anything else.")


if __name__ == "__main__":
    main()
