#!/usr/bin/env python3
"""Generate / edit an image via Google Gemini (Nano Banana Pro). Cross-platform.

Used by an image-worker agent (e.g. Pam). Writes a PNG into the profile's
cache/images/ (a media-delivery-safe root) and prints `MEDIA:<path>` so the
Hermes Telegram gateway attaches it as a native photo. On exhausted retries
prints `IMAGE_ERROR:<reason>`.

Key handling: reads GOOGLE_API_KEY / GEMINI_API_KEY from the environment, and if
absent falls back to reading it directly from <HERMES_HOME>/.env. The agent does
NOT need to `source` anything (Hermes' terminal tool does not pass credentials to
subprocesses).

Model override: set GEN_IMAGE_MODEL to use a different Gemini image model.

Usage:
  gen_image.py --prompt "an ENGLISH prompt"                     # new image
  gen_image.py --prompt "feedback" --edit-from /abs/prev.png    # image-to-image edit
"""
import argparse
import os
import pathlib
import sys
import time
import uuid

MODEL = os.environ.get("GEN_IMAGE_MODEL", "gemini-3-pro-image")  # Nano Banana Pro
MAX_TRIES = 3            # initial + 2 retries
BASE_DELAY = 2.0         # exponential backoff: 2s, 4s

# The gateway sets HERMES_HOME to the worker's profile dir; fall back to CWD-independent.
HERMES_HOME = pathlib.Path(
    os.environ.get("HERMES_HOME") or pathlib.Path.home() / ".hermes"
)
OUT_DIR = HERMES_HOME / "cache" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _key_from_env_file():
    env_file = HERMES_HOME / ".env"
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
                v = v.strip().strip('"').strip("'")
                if v and not v.startswith("__FILL"):
                    return v
    except Exception:
        pass
    return None


def _client():
    from google import genai

    key = (
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or _key_from_env_file()
    )
    if not key:
        raise RuntimeError("No GOOGLE_API_KEY / GEMINI_API_KEY (env or profile .env)")
    return genai.Client(api_key=key)


def _extract_png_bytes(resp):
    for cand in getattr(resp, "candidates", []) or []:
        content = getattr(cand, "content", None)
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return inline.data
    return None


def run(prompt, edit_from):
    from google.genai import types

    client = _client()
    if edit_from and os.path.isfile(edit_from):
        with open(edit_from, "rb") as fh:
            contents = [types.Part.from_bytes(data=fh.read(), mime_type="image/png"), prompt]
    else:
        contents = [prompt]

    last_err = None
    for attempt in range(MAX_TRIES):
        try:
            resp = client.models.generate_content(model=MODEL, contents=contents)
            data = _extract_png_bytes(resp)
            if not data:
                raise RuntimeError("model returned no image data")
            out = OUT_DIR / f"img_{uuid.uuid4().hex[:12]}.png"
            out.write_bytes(data)
            print(f"LAST_IMAGE:{out}")
            print(f"MEDIA:{out}")
            return 0
        except Exception as e:  # quota / 429 / network / etc.
            last_err = e
            if attempt < MAX_TRIES - 1:
                time.sleep(BASE_DELAY * (2 ** attempt))

    reason = str(last_err) or "unknown error"
    low = reason.lower()
    if "429" in reason or "quota" in low or "resource" in low or "exhaust" in low:
        reason = "Gemini free-tier / quota limit hit (try again later)."
    print(f"IMAGE_ERROR: {reason}")
    return 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--edit-from", default=None)
    a = ap.parse_args()
    sys.exit(run(a.prompt, a.edit_from))
