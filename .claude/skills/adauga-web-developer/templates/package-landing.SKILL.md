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
src-urile relative să meargă) ȘI îl **livrează DETERMINIST în General** prin tokenul tău:

```bash
<VENV_PYTHON> \
  <CEO_PROFILE>/skills/package-landing/scripts/package.py \
  --caption "mesaj scurt, mândru, în caracter"
```

- Fără `--jobdir` → împachetează **ultimul** job de landing. Explicit: `--jobdir "<JOBDIR>"`.
- **De ce livrează scriptul (nu `MEDIA:` în proză):** ești declanșat în sesiunea topicului dev-ului;
  un `MEDIA:` în răspunsul tău ar ajunge în ACEL topic, nu în General (cross-topic). Scriptul
  postează `.zip`-ul în General prin `sendDocument`, exact ca `deliver.py` al artistului.
- **Idempotent + anti-duplicat:** zip determinist per job; lock care nu retrimite același zip în 30
  min. După livrare resetează contoarele de runde (următorul landing pornește curat).
- Legacy: `--no-deliver` doar construiește zip-ul și printează `MEDIA:` (dacă vrei să-l livrezi altfel).

## Review înainte de împachetare (recuperează criteriile)
Sesiunea topicului dev-ului NU are brief-ul din General. La review-ul HTML-ului, rulează ÎNTÂI
`assign-to-<SLUG>/scripts/delegate.py --show-brief` ca să-ți reamintești criteriile, judecă pagina pe
ele și cere TU revizuiri (autonom) prin `delegate.py --prompt "<feedback>"` până e bună sau `CAP_REACHED`.

## Output
- `DELIVERED to General: <zip> ...` → ai TERMINAT. Nu mai posta nimic.
- `SKIP: ... (anti-duplicat)` → era deja livrat; nu insista.
- `ERROR: ... index.html not found` → dev-ul n-a scris încă pagina; așteaptă `HTML:<cale>`.

## Reguli
- Livrarea finală (zip-ul) merge DOAR în **General**, prin script. Nu posta zip-ul în topicurile de lucru.
- După livrare te oprești: fără alte skill-uri, fără handle-uri, fără chatter.
