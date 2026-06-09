---
name: assign-to-<SLUG>
description: "Deleagă crearea unei imagini (sau feedback de revizuire) către <NAME>. ACESTA e SINGURUL mod în care managerul îi dă lucru — pune mențiunea + topicul <TOPIC_NAME> + numărul rundei și impune un cap dur de <MAX_ROUNDS> runde. Nu tasta niciodată @<ARTIST_USERNAME> tu însuți."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Delegation, Workflow, Telegram, Image]
---

# assign-to-<SLUG> — handoff determinist manager → <NAME> (artist)

Rulează scriptul cu calea ABSOLUTĂ a venv-python. Promptul este în ENGLEZĂ (modelul de imagini
randează cel mai bine prompturi engleze); textul în altă limbă pe imagine se pune între ghilimele
duble în prompt.

```bash
<VENV_PYTHON> \
  <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py \
  --prompt "PROMPT DE IMAGINE ÎN ENGLEZĂ (runda 1) sau FEEDBACK acționabil (pushback)"
```

Scriptul postează `@<ARTIST_USERNAME> ROUND <n>: <prompt>` în topicul **<TOPIC_NAME>** (mențiune +
thread din `handoff.json`), cu contor de runde și cap dur. Tu NU scrii `@<ARTIST_USERNAME>`.
Artistul generează imaginea (la pushback editează imaginea precedentă cu `--edit-from`).

## Output
- `DELEGATED ROUND <n> to @<ARTIST_USERNAME> ...` → așteaptă imaginea, apoi evaluează (ai vision).
- `CAP_REACHED: ...` → NU mai delega; ia cea mai bună imagine de până acum și livreaz-o în General.

## Task nou
Contorul se auto-resetează după ~10 min inactivitate. Ca să forțezi un start curat imediat:
```bash
<VENV_PYTHON> <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py --reset
```

## Reguli & capcane
- **Risc de ocolire:** ACESTA e singurul mod de delegare. Nu tasta niciodată `@<ARTIST_USERNAME>`
  în proza ta — ar ocoli cap-ul și ar risca o buclă.
- **Promptul în engleză.** Compune un prompt de imagine clar, în engleză, din brief-ul omului.
- **Scurgere de contor între task-uri consecutive:** brief NOU sub 10 min după unul terminat →
  rulează MANUAL cu `--reset` înainte de prima rundă.
- **Un singur handoff pe rundă.** După delegare, așteaptă imaginea înainte de orice.
