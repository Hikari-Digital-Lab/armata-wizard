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

## Review — recuperează criteriile (sesiunea <TOPIC_NAME> n-are brief-ul din General)
Topicul **<TOPIC_NAME>** e o conversație SEPARATĂ de General și NU conține brief-ul omului. La
review, rulează ÎNTÂI ca să-ți reamintești criteriile:
```bash
<VENV_PYTHON> <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py --show-brief
```
Apoi judecă copy-ul pe criterii (ton, public, mesaj, lungime, CTA). **Fă mereu cel puțin o rundă de
rafinare** înainte de livrare; cere TU îmbunătățiri prin `--prompt "<feedback>"`, autonom, fără să
aștepți omul. Oprește-te când e bun sau la `CAP_REACHED`.

## Livrare — imagine + copy în General, DETERMINIST
Copy-ul e TEXT (îl ai în mesajul copywriter-ului). Imaginea însă NU are calea în sesiunea curentă →
livreaz-o prin scriptul determinist al ARTISTULUI, punând copy-ul final drept caption:
```bash
<VENV_PYTHON> <CEO_PROFILE>/skills/assign-to-<ARTIST_SLUG>/scripts/deliver.py \
  --caption "<copy-ul final aprobat, în <LANGUAGE>>"
```
Asta postează imaginea + copy-ul în **General** (fără thread). NU folosi `MEDIA:` în proză (ești
declanșat în topicul copywriter-ului → ar ajunge în topicul greșit). După `DELIVERED ...` ai TERMINAT.

## Task nou
Livrarea resetează singură contoarele; backstop: auto-reset după ~10 min inactivitate. Start curat:
```bash
<VENV_PYTHON> <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py --reset
```

## Reguli & capcane
- **Risc de ocolire:** ACESTA e singurul mod de delegare. Nu tasta niciodată
  `@<COPYWRITER_USERNAME>` în proza ta — ar ocoli cap-ul și ar risca o buclă.
- **Imaginea o trimite scriptul.** Nu posta imaginea manual; dă calea ei prin `--image`.
- **Un singur handoff pe rundă.** După delegare, așteaptă copy-ul înainte de orice.
