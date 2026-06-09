---
name: package-landing
description: "Împachetează pagina de landing finită (index.html-ul scris de dev + imaginile artistului) într-un .zip descărcabil și îți dă o linie MEDIA:<zip> de livrat omului în General. Folosește DUPĂ ce dev-ul a răspuns cu HTML:<cale>."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Packaging, Workflow, Telegram, Landing]
---

# package-landing — fă zip-ul final (HTML + imagini) pentru om

Folosește-l DUPĂ ce dev-ul ți-a trimis `HTML:<cale>` (pagina e scrisă în job dir, lângă imaginile
artistului). Scriptul pune `index.html` + imaginile într-un `.zip` (toate la același nivel, ca
src-urile relative să meargă) și-ți dă linia `MEDIA:<zip>`.

```bash
<VENV_PYTHON> \
  <CEO_PROFILE>/skills/package-landing/scripts/package.py
```

- Fără argumente → împachetează **ultimul** job de landing (cel mai recent). În mod normal asta
  vrei imediat după ce dev-ul a livrat.
- Explicit: `--jobdir "<calea JOBDIR de la assign-to-<SLUG>>"`.
- **Idempotent:** zip-ul are nume determinist per job; dacă există deja și e la zi, e refolosit (nu
  se creează duplicate). Se reconstruiește doar dacă `index.html` s-a schimbat (după o revizuire).

## Output
- `PACKAGED <n> files (...)` sau `REUSED existing zip ...` → confirmare.
- `MEDIA:<cale .zip>` → **postează linia asta în topicul General** (cu `send_message`, fără thread
  id) împreună cu un mesaj scurt, în caracter. Gateway-ul atașează zip-ul ca document, iar omul
  îl descarcă.
- `ERROR: ... index.html not found` → dev-ul n-a scris încă pagina; așteaptă răspunsul lui
  `HTML:<cale>` înainte să împachetezi.

## Reguli
- Livrarea finală (zip-ul) merge DOAR în **General**, către om. Nu posta zip-ul în topicurile de
  lucru.
- După livrare în General, te oprești: fără alte skill-uri, fără handle-uri, fără chatter.
