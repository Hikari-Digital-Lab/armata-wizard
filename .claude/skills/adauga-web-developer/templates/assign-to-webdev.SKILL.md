---
name: assign-to-<SLUG>
description: "Deleagă construirea paginii de landing (HTML) către <NAME>. ACESTA e SINGURUL mod în care managerul îi dă lucru — îi pregătește un job dir (imaginile + un BRIEF.md cu brief-ul + copy-ul + numele fișierelor + calea OUTPUT) și-i trimite albumul + spec-ul în topicul <TOPIC_NAME>, cu mențiunea corectă, numărul rundei și cap-ul dur de <MAX_ROUNDS> runde. Nu tasta niciodată @<DEV_USERNAME> tu însuți."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Delegation, Workflow, Telegram, WebDev, Landing]
---

# assign-to-<SLUG> — handoff determinist manager → <NAME> (web developer)

Folosește acest skill DUPĂ ce ai (1) imaginile finale (de la artist) și (2) copy-ul paginii (de
la copywriter). Scriptul pregătește singur un **job dir**: copiază imaginile acolo (cu basename),
scrie un `BRIEF.md` (brief + copy + numele fișierelor + calea unde să scrie `index.html`) și-i
trimite dev-ului imaginile ca **album** + calea spec-ului. Rulează cu calea ABSOLUTĂ a venv-python:

```bash
<VENV_PYTHON> \
  <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py \
  --prompt "BRIEF (<LANGUAGE>): temă, scop, public, ton" \
  --copy "COPY-UL EXACT al copywriter-ului (HERO / SECȚIUNI / CTA)" \
  --image "<imagine 1>" --image "<imagine 2>" [--image "<imagine 3>"]
```

- **Runda 1 (cu imagini + copy):** dă MEREU 2–3 `--image <cale>` (din liniile `MEDIA:` ale
  artistului) ȘI `--copy "<copy-ul paginii>"`. Dacă copy-ul e foarte lung, poți folosi
  `--copy-file <cale_fișier>` în loc de `--copy`.
- **Runde de revizuire (feedback):** rulează doar cu `--prompt "<feedback acționabil>"` (fără
  `--image`) — refolosește același job dir, adaugă feedback-ul în spec și dev-ul rescrie
  `index.html` pe loc.

Scriptul postează `@<DEV_USERNAME> ROUND <n>: ...` în topicul **<TOPIC_NAME>** (album cu caption la
runda 1), cu mențiune + thread din `handoff.json`, contor de runde și cap dur. Tu NU scrii
`@<DEV_USERNAME>` în proză.

## Output (citește-l!)
- `DELEGATED ROUND <n> to @<DEV_USERNAME> (...)` → așteaptă răspunsul dev-ului cu o linie
  `HTML:<cale>`.
- `JOBDIR:<cale>` → **ține minte calea asta**; o dai mai târziu la skill-ul `package-landing` ca
  să faci zip-ul (sau lași package-landing să ia automat ultimul job).
- `CAP_REACHED: ...` → NU mai delega; ia cel mai bun `index.html` de până acum, fă zip-ul cu
  `package-landing` și livrează-l în General.

## Task nou
Contorul se auto-resetează după ~10 min inactivitate. Pentru start curat imediat:
```bash
<VENV_PYTHON> <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py --reset
```

## Reguli & capcane
- **Risc de ocolire:** ACESTA e singurul mod de delegare către dev. Nu tasta niciodată
  `@<DEV_USERNAME>` în proza ta — ar ocoli cap-ul și ar risca o buclă.
- **Imaginile + spec-ul le pregătește scriptul.** Tu nu posta nimic manual în <TOPIC_NAME>; dă
  căile prin `--image` + textul prin `--copy` și scriptul face restul.
- **Un singur handoff pe rundă.** După delegare, așteaptă răspunsul dev-ului (`HTML:<cale>`)
  înainte de orice.
- Imaginile date la `--image` sunt cele FINALE aprobate (din liniile `MEDIA:` ale artistului).
