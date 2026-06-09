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
- `CAP_REACHED: ...` → NU mai delega; ia cea mai bună imagine de până acum și livreaz-o în General (vezi „Livrare").

## Review — recuperează criteriile (sesiunea Art n-are brief-ul din General)
Topicul **<TOPIC_NAME>** e o conversație SEPARATĂ de General și NU conține brief-ul omului. La review,
rulează ÎNTÂI ca să-ți reamintești criteriile pe care le-ai trimis:
```bash
<VENV_PYTHON> <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py --show-brief
```
Apoi bifează imaginea pe fiecare criteriu (subiect, stil, **aspect/format**, text, calitate) și, dacă
ceva poate fi mai bun, dă feedback prin `--prompt "<feedback ENGLEZ>"`. Fă mereu cel puțin o rundă de
rafinare înainte de livrare; oprește-te când e bună sau la `CAP_REACHED`. **Tu faci review-ul singur,
nu aștepta omul.**

## Livrare — în General, DETERMINIST (NU `MEDIA:` în proză)
Ești declanșat în sesiunea <TOPIC_NAME> și NU cunoști calea fișierului imaginii (vision native = doar
pixeli). Livrează prin scriptul determinist, care ia imaginea aprobată (pointer `last_image.txt`),
o pune în **General** (fără thread) prin tokenul tău și resetează contorul:
```bash
<VENV_PYTHON> <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/deliver.py \
  --caption "o legendă scurtă, mândră, în limba echipei"
```
- `DELIVERED to General: ...` → ai TERMINAT. NU mai posta nimic (nici în Art, nici în General).
- `SKIP: ...` (anti-duplicat) → imaginea era deja livrată; nu insista.
- Are lock anti-duplicat (cele două sesiuni per-topic pot ajunge amândouă la livrare). Override la
  imagine cu `--file <cale absolută>`.

## Task nou
`deliver.py` resetează singur contorul după livrare, deci următorul brief pornește de la ROUND 1.
Backstop: contorul se auto-resetează și după ~10 min inactivitate. Ca să forțezi un start curat:
```bash
<VENV_PYTHON> <CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py --reset
```

## Reguli & capcane
- **Risc de ocolire:** ACESTA e singurul mod de delegare. Nu tasta niciodată `@<ARTIST_USERNAME>`
  în proza ta — ar ocoli cap-ul și ar risca o buclă.
- **Promptul în engleză.** Compune un prompt de imagine clar, în engleză, din brief-ul omului; include
  formatul (ex. „1:1 aspect ratio") dacă omul a cerut unul.
- **Un singur handoff pe rundă.** După delegare, așteaptă imaginea înainte de orice.
