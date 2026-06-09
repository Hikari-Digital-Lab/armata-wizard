# Upgrade the copywriter's `assign-to-<copywriter>` delegate to MULTI-IMAGE (Pas 7, if chaining)

For LANDING PAGE copy, the CEO must send the copywriter ALL 2–3 site images at once. The existing
copywriter delegate (`<CEO_PROFILE>/skills/assign-to-<COPYWRITER_SLUG>/scripts/delegate.py`) only
sends ONE image. Upgrade it to accept multiple `--image` (Telegram photo album), **backward
compatible**: 0 images → text, 1 image → photo (unchanged), >1 → album. This does NOT change the
existing ad-copy flow.

If the copywriter was created by `adauga-copywriter`/`adauga-membru-echipa`, its delegate matches
the structure below. Make these THREE edits:

## Edit 1 — make `--image` repeatable
Change the `--image` argument (help text may vary slightly between builders), e.g.:
```python
    ap.add_argument("--image", help="local path to the image to send the copywriter (round 1)")
```
to:
```python
    ap.add_argument("--image", action="append", default=[],
                    help="image path (round 1); repeatable for 2-3 site images")
```

## Edit 2 — add an album sender (paste after the existing `_post_photo` function)
```python
def _post_album(token, chat_id, thread, caption, image_paths):
    """sendMediaGroup with multiple photos; caption on the first item."""
    boundary = "----hermes" + uuid.uuid4().hex
    media, file_parts = [], []
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
```
(Ensure `import mimetypes` and `import uuid` are present — they usually already are.)

## Edit 3 — branch on the number of images at the send site
Change the block:
```python
        if a.image:
            img = pathlib.Path(a.image)
            if not img.is_file():
                print(f"ERROR: image not found: {a.image}")
                return
            caption = text if len(text) <= CAPTION_LIMIT else text[: CAPTION_LIMIT - 1] + "…"
            ok = _post_photo(token, chat_id, a.thread, caption, str(img))
        else:
```
to:
```python
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
```

## Verify
`python3 -m py_compile <.../assign-to-<COPYWRITER_SLUG>/scripts/delegate.py)` must pass, and the
existing single-image ad flow must still work (1 `--image` → photo, as before).

> If the copywriter's delegate does NOT match this structure (different builder), inspect it and
> apply the equivalent change: accept multiple `--image` and send an album when there is more than
> one. The CEO's `assign-to-<COPYWRITER_SLUG>` SKILL.md may also be updated to mention passing
> several `--image` for page copy.
