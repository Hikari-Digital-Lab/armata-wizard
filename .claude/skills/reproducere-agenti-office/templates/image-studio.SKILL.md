---
name: image-studio
description: "Generează sau editează o imagine cu Google Gemini (Nano Banana Pro). Folosește când Michael îți cere să creezi sau să revizuiești o imagine. Produce un PNG și îl întoarce în grup prin tag-ul MEDIA:."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Image, Generation, Gemini, Creative]
---

# image-studio — pensula lui Pam

Transformă un brief în engleză (sau o notă de revizuire + imaginea anterioară) într-un PNG,
via Gemini `gemini-3-pro-image` (Nano Banana Pro), cu retry/backoff. Scriptul își ia singur
cheia din `.env` — nu trebuie să faci `source`.

La succes printează:
- `LAST_IMAGE:<cale_png_absolută>` — ține minte; o pasezi la `--edit-from` runda următoare.
- `MEDIA:<cale_png_absolută>` — **include linia asta VERBATIM în răspuns** ca Telegram să atașeze poza.

La eșec printează `IMAGE_ERROR: <motiv>` — anunță în cuvinte, NU intra în buclă.

## Imagine NOUĂ (runda 1)
```bash
<VENV_PYTHON> <CALE_SKILL>/scripts/gen_image.py --prompt "PROMPT ÎN ENGLEZĂ"
```

## EDITARE pe imaginea anterioară (runde de pushback, image-to-image)
```bash
<VENV_PYTHON> <CALE_SKILL>/scripts/gen_image.py \
  --prompt "feedback-ul lui Michael, în engleză" \
  --edit-from /cale/absolută/imagine_anterioară.png
```

## Contract de output
- Succes: stdout se termină cu `LAST_IMAGE:<cale>` apoi `MEDIA:<cale>`.
- Eșec: stdout se termină cu `IMAGE_ERROR: <motiv>`.

## Bune practici (învățate)
- **Text românesc pe imagine:** ține prompt-ul principal în engleză, dar pune textul românesc
  între ghilimele duble în prompt (ex. `including the elegant text "Îți asculți copilul interior?" at the top`).
  Astfel modelul randează corect diacriticele, dar beneficiază de înțelegerea promptului în engleză.
- O singură imagine pe rundă. Apoi așteaptă.
