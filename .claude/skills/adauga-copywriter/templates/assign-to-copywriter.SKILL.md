---
name: assign-to-<SLUG>
description: "Deleagă scrierea textului de advertisement (copy) către <NAME>. ACESTA e SINGURUL mod în care managerul îi dă lucru — îi trimite imaginea + brief-ul în topicul <TOPIC_NAME>, cu mențiunea corectă, numărul rundei și cap-ul dur de <MAX_ROUNDS> runde. Nu tasta niciodată @<COPYWRITER_USERNAME> tu însuți."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Delegation, Workflow, Telegram, Copywriting]
---

# assign-to-<SLUG> — handoff determinist manager → <NAME> (copywriter)

Folosește acest skill DUPĂ ce ai imaginea finală (de la workerul de imagini sau trimisă de
tine). Trimite-i copywriter-ului imaginea (o vede efectiv) + brief-ul, ca să scrie textul de
advertisement. Rulează cu calea ABSOLUTĂ a venv-python:

```bash
<VENV_PYTHON> \
  <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py \
  --prompt "BRIEF + ce text vrea omul (<LANGUAGE>), ton, public țintă" \
  --image "<calea locală a imaginii finale>"
```

- **Runda 1 (cu imagine):** dă MEREU `--image <cale>` ca să vadă vizualul.
- **Runde de revizuire (feedback):** rulează doar cu `--prompt "<feedback acționabil>"`
  (fără `--image`) — își revizuiește copy-ul precedent.

Scriptul postează `@<COPYWRITER_USERNAME> ROUND <n>: <brief>` în topicul **<TOPIC_NAME>** (ca
foto cu caption când dai `--image`), cu mențiune + thread din `handoff.json`, contor de runde și
cap dur. Tu NU scrii `@<COPYWRITER_USERNAME>` în proză.

## Output
- `DELEGATED ROUND <n> to @<COPYWRITER_USERNAME> (...)` → așteaptă copy-ul, apoi evaluează.
- `CAP_REACHED: ...` → NU mai delega; ia cel mai bun copy de până acum, livrează imaginea +
  copy-ul în General și oprește-te.

## Task nou
Contorul se auto-resetează după ~10 min inactivitate. Ca să forțezi un start curat imediat:
```bash
<VENV_PYTHON> <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py --reset
```

## Reguli & capcane
- **Risc de ocolire:** ACESTA e singurul mod de delegare. Nu tasta niciodată
  `@<COPYWRITER_USERNAME>` în proza ta — ar ocoli cap-ul și ar risca o buclă.
- **Imaginea o trimite scriptul.** Nu posta imaginea manual; dă calea ei prin `--image`.
- **Scurgere de contor între task-uri consecutive:** dacă primești un brief NOU sub 10 min după
  unul terminat, rulează MANUAL cu `--reset` înainte de prima rundă.
- **Un singur handoff pe rundă.** După delegare, așteaptă copy-ul înainte de orice.
