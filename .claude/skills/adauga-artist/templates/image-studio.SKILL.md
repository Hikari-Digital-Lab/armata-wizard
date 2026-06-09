---
name: image-studio
description: "Generate or edit an image with Google Gemini (Nano Banana Pro). Use whenever the manager asks the artist to create or revise an image. Produces a PNG and returns it to the Telegram group via a MEDIA: tag."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Image, Generation, Gemini, Creative]
---

# image-studio — the artist's brush

<!-- Installed into <ARTIST_PROFILE>/skills/image-studio/. Replace <VENV_PYTHON> at install. -->

Turns an English brief (or a revision note + the previous image) into a PNG, via Gemini
`gemini-3-pro-image` (Nano Banana Pro) by default — override with the `GEN_IMAGE_MODEL` env var.
Retries with backoff. The script loads the API key itself from the profile `.env` — you do NOT
need to `source` anything.

On success it prints two lines:
- `LAST_IMAGE:<absolute_png_path>` — remember it; pass it to `--edit-from` next round.
- `MEDIA:<absolute_png_path>` — **emit this line VERBATIM in your reply** so Telegram attaches the image.

On exhausted retries it prints `IMAGE_ERROR: <reason>` — announce the failure in words, do NOT loop.

## New image (round 1)
```bash
<VENV_PYTHON> <ARTIST_PROFILE>/skills/image-studio/scripts/gen_image.py --prompt "ENGLISH PROMPT"
```

## Edit the previous image (pushback rounds, image-to-image)
```bash
<VENV_PYTHON> <ARTIST_PROFILE>/skills/image-studio/scripts/gen_image.py \
  --prompt "the manager's feedback, in English" \
  --edit-from /abs/path/to/previous.png
```

## Output contract
- Success: stdout ends with `LAST_IMAGE:<path>` then `MEDIA:<path>`.
- Failure: stdout ends with `IMAGE_ERROR: <human reason>` (e.g. quota exhausted).

## Best practices (learned)
- **Text in another language on the image:** keep the main prompt in English, but put the exact
  text in double quotes inside the prompt (e.g. `including the elegant text "Îți asculți copilul
  interior?" at the top`). The model renders the diacritics correctly while benefiting from
  English prompt comprehension.
- Always craft the prompt in ENGLISH. Generate exactly ONE image per round.
