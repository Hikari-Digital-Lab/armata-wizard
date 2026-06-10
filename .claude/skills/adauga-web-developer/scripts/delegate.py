#!/usr/bin/env python3
"""Deterministic CEO -> web-developer handoff over Telegram (landing-page builds).

This is the SINGLE way the CEO hands a page-build to the web developer. On the FIRST
round the CEO passes:
  - the brief (--prompt),
  - the page copy written by the copywriter (--copy "..."  or  --copy-file <path>),
  - the 2-3 site images from the artist (--image, repeatable).

The script then, deterministically (so a small/fast LLM can't get it wrong):
  1. Creates a JOB dir under the CEO's cache: cache/landing/job_<ts>_<rand>/.
  2. Copies each image into the job dir by BASENAME (so the HTML can use relative
     names and they resolve next to index.html in the final zip).
  3. Writes BRIEF.md into the job dir = brief + the copywriter's page copy + the exact
     image filenames + the exact OUTPUT path (job_dir/index.html).
  4. Sends the developer a PHOTO ALBUM (sendMediaGroup) of the images into his topic,
     captioned with his @mention, the round, and the SPEC:/OUTPUT: paths — so he SEES
     the visuals, knows where the full spec is, and where to write the HTML.

Revision rounds (the CEO has feedback on the developer's HTML): call again WITHOUT
--image, just --prompt "<feedback>". The script reuses the latest job dir, appends the
feedback to BRIEF.md, and pings the developer to rebuild index.html in place.

Hard loop cap: per-worker round counter in a state file. Auto-increments per call,
REFUSES after max_rounds (prints CAP_REACHED), resets after reset_gap seconds idle.
The developer is gated (require_mention=true) and only this script ever mentions him,
so an infinite CEO<->developer loop is structurally impossible.

Config: reads handoff.json sitting in the skill dir (one level up from scripts/):
  {"worker_mention": "@<dev>_bot", "thread_id": "<TOPIC_ID>",
   "max_rounds": 3, "reset_gap": 600}
Token + group chat id come from the CEO profile .env
  (TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ALLOWED_CHATS).

Usage:
  delegate.py --prompt "BRIEF" --copy "page copy" --image a.png --image b.png
  delegate.py --prompt "BRIEF" --copy-file /path/copy.txt --image a.png --image b.png
  delegate.py --prompt "feedback on the page"      # revision, no image
  delegate.py --reset
"""
import argparse
import json
import mimetypes
import os
import pathlib
import re
import shutil
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
# <profile>/skills/assign-to-<slug>/scripts/delegate.py  -> profile is three levels up.
PROFILE_DIR = HERE.parents[2]
CAPTION_LIMIT = 1000

HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or PROFILE_DIR)
LANDING_ROOT = HERMES_HOME / "cache" / "landing"


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
        return {"round": 0, "ts": 0, "jobdir": "", "brief": ""}


def _post_text(token, payload):
    data = urllib.parse.urlencode(payload).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=data, timeout=20) as r:
        return json.loads(r.read().decode("utf-8")).get("ok", False)


def _multipart(fields, files):
    """Build a multipart/form-data body. files: list of (name, path)."""
    boundary = "----hermes" + uuid.uuid4().hex
    body = bytearray()
    for k, v in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        body += f"{v}\r\n".encode()
    for name, path in files:
        p = pathlib.Path(path)
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"; filename="{p.name}"\r\n'.encode()
        body += f"Content-Type: {ctype}\r\n\r\n".encode()
        body += p.read_bytes()
        body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return boundary, bytes(body)


def _post_photo(token, chat_id, thread, caption, image_path):
    fields = {"chat_id": str(chat_id), "caption": caption}
    if thread and thread not in ("", "None", "1"):
        fields["message_thread_id"] = str(thread)
    boundary, body = _multipart(fields, [("photo", image_path)])
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    req = urllib.request.Request(url, data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8")).get("ok", False)


def _post_album(token, chat_id, thread, caption, image_paths):
    """sendMediaGroup with up to 10 photos; caption on the first item."""
    media, files = [], []
    for i, path in enumerate(image_paths):
        attach = f"file{i}"
        item = {"type": "photo", "media": f"attach://{attach}"}
        if i == 0 and caption:
            item["caption"] = caption
        media.append(item)
        files.append((attach, path))
    fields = {"chat_id": str(chat_id), "media": json.dumps(media)}
    if thread and thread not in ("", "None", "1"):
        fields["message_thread_id"] = str(thread)
    boundary, body = _multipart(fields, files)
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    req = urllib.request.Request(url, data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8")).get("ok", False)


def _write_brief(jobdir, prompt, copy_text, image_names, out_html, round_no, feedback=None):
    spec = jobdir / "BRIEF.md"
    if feedback is not None and spec.is_file():
        with spec.open("a", encoding="utf-8") as f:
            f.write(f"\n\n## Feedback (ROUND {round_no}) — revise index.html in place\n{feedback}\n")
        return spec
    first_img = image_names[0] if image_names else "image.png"
    # Use forward-slash (POSIX) paths everywhere the web dev will read them. A Windows path
    # like C:\Users\... contains \U, an INVALID JSON escape, which corrupts the model's
    # tool-call arguments ("Unrepairable tool_call ... replaced with empty object") so the
    # file never gets written. Forward slashes are valid JSON AND valid for open()/write on
    # Windows; on Linux/macOS as_posix() is a no-op (paths already use /). Cross-platform safe.
    out_posix = out_html.as_posix()
    spec_posix = spec.as_posix()
    lines = [
        "# Landing page build spec (for the web developer)",
        "",
        f"OUTPUT:{out_posix}",
        f"SPEC:{spec_posix}",
        "",
        "## Brief (from the human, via the CEO)",
        (prompt or "(no explicit brief — use the page copy below)").strip(),
        "",
        "## Available images (they sit in the SAME folder as index.html — use the BASENAME only)",
    ]
    lines += [f"- {n}" for n in image_names] if image_names else ["- (no images)"]
    lines += [
        "",
        "## Page copy (written by the copywriter — use THESE words on the page)",
        (copy_text or "(no copy received — write minimal copy coherent with the brief)").strip(),
        "",
        "## Rules",
        "- index.html = a single self-contained file (inline CSS, NO CDN / external fonts).",
        f'- Reference the images by basename (e.g. src="{first_img}").',
        "- Responsive + accessible (alt, semantic tags). Content language = the brief's language.",
        "- Build the page from THIS spec (filenames + copy). Do NOT call vision_analyze on the "
        "image paths — just reference each image by its basename in an <img> tag.",
        f"- Write the file EXACTLY at (forward slashes, valid on Windows): {out_posix}",
    ]
    spec.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return spec


def main():
    cfg = _load_cfg()
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt")
    ap.add_argument("--copy", help="the copywriter's page copy text (round 1)")
    ap.add_argument("--copy-file", help="path to a file with the page copy (round 1)")
    ap.add_argument("--image", action="append", default=[], help="image path (repeatable, round 1)")
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
        state_file.write_text(json.dumps({"round": 0, "ts": time.time(), "jobdir": "", "brief": ""}))
        print(f"RESET: round counter for {worker} cleared. Next delegation will be ROUND 1.")
        return

    if a.show_brief:
        brief = (_load_state(state_file) or {}).get("brief", "")
        if brief:
            print(f"CURRENT_BRIEF (criteriile pe care le-ai trimis workerului):\n{brief}")
        else:
            print("NO_BRIEF: niciun brief stocat (probabil n-ai delegat încă pentru acest task).")
        return

    if not a.prompt and not a.copy and not a.copy_file:
        raise SystemExit("ERROR: --prompt (and/or --copy) is required")

    token = _env_value("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("ERROR: no TELEGRAM_BOT_TOKEN in profile .env")
    chat_id = a.chat or (_env_value("TELEGRAM_GROUP_ALLOWED_CHATS") or "").split(",")[0].strip()
    if not chat_id:
        raise SystemExit("ERROR: no chat id (TELEGRAM_GROUP_ALLOWED_CHATS or --chat)")

    st = _load_state(state_file)
    now = time.time()
    if now - st.get("ts", 0) > a.reset_gap:
        st = {"round": 0, "ts": now, "jobdir": "", "brief": ""}

    nxt = st.get("round", 0) + 1
    if nxt > a.max_rounds:
        print(
            f"CAP_REACHED: {a.max_rounds} rounds already used for this task. "
            f"Do NOT delegate to {worker} again — take the best HTML so far, package it with the "
            "package-landing skill, and deliver the zip to the user in General."
        )
        return

    # Persist the ROUND 1 brief so the review turn (a SEPARATE topic session with NO General
    # context) can recall the criteria via --show-brief.
    brief = st.get("brief", "") or ""
    if nxt == 1:
        brief = a.prompt or ""

    copy_text = a.copy
    if not copy_text and a.copy_file:
        try:
            copy_text = pathlib.Path(a.copy_file).read_text(encoding="utf-8")
        except Exception as e:
            print(f"ERROR: could not read --copy-file: {e}")
            return

    try:
        if a.image:
            # ROUND 1 (with images): fresh job dir, copy images, write spec, send album.
            for img in a.image:
                if not pathlib.Path(img).is_file():
                    print(f"ERROR: image not found: {img}")
                    return
            LANDING_ROOT.mkdir(parents=True, exist_ok=True)
            jobdir = LANDING_ROOT / f"job_{int(now)}_{uuid.uuid4().hex[:6]}"
            jobdir.mkdir(parents=True, exist_ok=True)
            image_names = []
            for img in a.image:
                src = pathlib.Path(img)
                shutil.copyfile(src, jobdir / src.name)
                image_names.append(src.name)
            out_html = jobdir / "index.html"
            spec = _write_brief(jobdir, a.prompt, copy_text, image_names, out_html, nxt)
            caption = (
                f"{worker} ROUND {nxt}: Build the landing page.\n"
                f"SPEC:{spec.as_posix()}\nOUTPUT:{out_html.as_posix()}\n"
                "Read the spec, reference images by basename, write index.html at OUTPUT, "
                "and reply with HTML:<path>."
            )
            if len(caption) > CAPTION_LIMIT:
                caption = caption[: CAPTION_LIMIT - 1] + "…"
            ok = _post_album(token, chat_id, a.thread, caption, [str(jobdir / n) for n in image_names])
            st_jobdir = str(jobdir)
        else:
            # REVISION round (no images): reuse last job dir, append feedback, ping the dev.
            jobdir = pathlib.Path(st.get("jobdir") or "")
            if not jobdir.is_dir():
                print(
                    "ERROR: no existing job dir for a revision round. Re-run round 1 with --image "
                    "(and --copy) to start a fresh landing job."
                )
                return
            out_html = jobdir / "index.html"
            _write_brief(jobdir, a.prompt, copy_text, [], out_html, nxt, feedback=a.prompt)
            spec = jobdir / "BRIEF.md"
            text = (
                f"{worker} ROUND {nxt}: Revise the page. New feedback appended to the spec.\n"
                f"SPEC:{spec.as_posix()}\nOUTPUT:{out_html.as_posix()}\n"
                f"Feedback: {a.prompt}\nRewrite index.html at OUTPUT, then reply HTML:<path>."
            )
            payload = {"chat_id": chat_id, "text": text}
            if a.thread and a.thread not in ("", "None", "1"):
                payload["message_thread_id"] = a.thread
            ok = _post_text(token, payload)
            st_jobdir = str(jobdir)
    except Exception as e:
        print(f"ERROR: failed to send to Telegram: {e}")
        return

    if not ok:
        print("ERROR: Telegram rejected the message (check token / chat id / thread / images).")
        return

    state_file.write_text(json.dumps({"round": nxt, "ts": now, "jobdir": st_jobdir, "brief": brief}))
    kind = f"with {len(a.image)} image(s)" if a.image else "revision (feedback only)"
    print(f"DELEGATED ROUND {nxt} to {worker} ({kind}). (cap {a.max_rounds})")
    print(f"JOBDIR:{st_jobdir}")
    print("Now wait for the developer's reply (a line HTML:<path>).")


if __name__ == "__main__":
    main()
