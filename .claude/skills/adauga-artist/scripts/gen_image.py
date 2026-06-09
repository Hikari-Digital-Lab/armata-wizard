#!/usr/bin/env python3
"""Generate / edit an image via Google Gemini (Nano Banana Pro). Cross-platform.

Used by an image-worker agent (e.g. Pam). Writes a PNG into the profile's
cache/images/ (a media-delivery-safe root) and prints `MEDIA:<path>` so the
Hermes Telegram gateway attaches it as a native photo. On exhausted retries
prints `IMAGE_ERROR:<reason>`.

It ALSO writes a stable pointer file `cache/images/last_image.txt` containing the
absolute path of the most recent image. The CEO's deliver.py reads that pointer to
deliver the approved image to General — deterministic, no "newest *.png" guessing
(which broke when caches held .jpg or stale files).

Key handling: reads GOOGLE_API_KEY / GEMINI_API_KEY from the environment, and if
absent falls back to reading it directly from <HERMES_HOME>/.env. The agent does
NOT need to `source` anything (Hermes' terminal tool does not pass credentials to
subprocesses).

Aspect ratio: the TEXT prompt alone does NOT control output dimensions on Gemini —
it must be passed as an API parameter. This script sets it via ImageConfig, taken
from --aspect or AUTO-DETECTED from keywords in the prompt (1:1/square, 9:16/portrait,
16:9/landscape, etc.). Model override: set GEN_IMAGE_MODEL.

Usage:
  gen_image.py --prompt "an ENGLISH prompt"                       # new image
  gen_image.py --prompt "feedback" --edit-from /abs/prev.png      # image-to-image edit
  gen_image.py --prompt "... 1:1 ..." --aspect 1:1                # force aspect ratio
"""
import argparse
import os
import pathlib
import sys
import time
import uuid

# Make output safe on any console, incl. Windows cp1252 (error reasons may carry non-ASCII).
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MODEL = os.environ.get("GEN_IMAGE_MODEL", "gemini-3-pro-image")  # Nano Banana Pro
MAX_TRIES = 3            # initial + 2 retries
BASE_DELAY = 2.0         # exponential backoff: 2s, 4s

# The gateway sets HERMES_HOME to the worker's profile dir; fall back to CWD-independent.
HERMES_HOME = pathlib.Path(
    os.environ.get("HERMES_HOME") or pathlib.Path.home() / ".hermes"
)
OUT_DIR = HERMES_HOME / "cache" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)
POINTER = OUT_DIR / "last_image.txt"

VALID_ASPECTS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}


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


def _detect_aspect(prompt, explicit):
    """Resolve the target aspect ratio. Explicit --aspect wins; otherwise auto-detect
    from keywords in the prompt so a brief like '1:1' / 'square' / 'portrait' actually
    changes the OUTPUT dimensions (the Gemini text prompt alone does NOT control size)."""
    if explicit:
        e = explicit.strip()
        return e if e in VALID_ASPECTS else None
    low = (prompt or "").lower()
    for r in ("21:9", "16:9", "9:16", "4:5", "5:4", "3:4", "4:3", "2:3", "3:2", "1:1"):
        if r in low:
            return r
    if any(w in low for w in ("square", "1 by 1", "instagram post")):
        return "1:1"
    if any(w in low for w in ("portrait", "vertical", "story", "reel", "9 by 16")):
        return "9:16"
    if any(w in low for w in ("widescreen", "landscape", "horizontal", "16 by 9", "banner")):
        return "16:9"
    return None  # let the model use its default


def run(prompt, edit_from, aspect=None):
    from google.genai import types

    client = _client()
    if edit_from and os.path.isfile(edit_from):
        with open(edit_from, "rb") as fh:
            contents = [types.Part.from_bytes(data=fh.read(), mime_type="image/png"), prompt]
    else:
        contents = [prompt]

    ar = _detect_aspect(prompt, aspect)
    cfg = None
    if ar:
        cfg = types.GenerateContentConfig(image_config=types.ImageConfig(aspect_ratio=ar))
        print(f"ASPECT:{ar}")

    last_err = None
    for attempt in range(MAX_TRIES):
        try:
            resp = client.models.generate_content(model=MODEL, contents=contents, config=cfg)
            data = _extract_png_bytes(resp)
            if not data:
                raise RuntimeError("model returned no image data")
            out = OUT_DIR / f"img_{uuid.uuid4().hex[:12]}.png"
            out.write_bytes(data)
            try:
                POINTER.write_text(str(out), encoding="utf-8")  # stable pointer for deliver.py
            except Exception:
                pass
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
    ap.add_argument("--aspect", default=None,
                    help="aspect ratio, e.g. 1:1, 16:9, 9:16 (else auto-detected from the prompt)")
    a = ap.parse_args()
    sys.exit(run(a.prompt, a.edit_from, a.aspect))
