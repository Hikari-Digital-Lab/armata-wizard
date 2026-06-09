---
name: assign-to-<SLUG>
description: "Deleagă un email (nou sau răspuns) către <NAME>, secretara. ACESTA e SINGURUL mod în care CEO-ul îi dă lucru — garantează mențiunea, topicul <TOPIC_NAME>, numărul rundei și cap-ul dur. Nu tasta niciodată @<SLUG> tu însuți."
version: 1.0.0
author: silviu
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Delegation, Email, Secretariat, Telegram]
---

# assign-to-<SLUG> — handoff determinist CEO → <NAME> (email)
# Replace at install: <SLUG>, <NAME>, <VENV_PYTHON>, <CEO_PROFILE>, <SECRETARY_USERNAME>,
# <TOPIC_NAME>, <MAX_ROUNDS>.

Rulează scriptul cu calea ABSOLUTĂ a venv-python. Pune în `--prompt` emailul COMPLET, clar delimitat,
într-unul din cele DOUĂ formate:

**Răspuns la un email primit** (ai UID-ul din raportul „email nou (UID N)…"):
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py \
  --prompt "RĂSPUNDE LA MAIL | UID: N | BODY: Textul complet al răspunsului."
```

**Email nou către cineva:**
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py \
  --prompt "TRIMITE EMAIL | TO: client@example.com | SUBJECT: Subiectul exact | BODY: Textul complet."
```
Scriptul postează `@<SECRETARY_USERNAME> ROUND <n>: <prompt>` în topicul <TOPIC_NAME> (mențiune +
thread din `handoff.json`, care stă LÂNGĂ delegate.py în `scripts/`), cu contor de runde și cap dur.
Tu NU scrii `@<SLUG>`.

## Output
- `DELEGATED ROUND <n> to @<SECRETARY_USERNAME> ...` → așteaptă confirmarea secretarei („Am trimis"/
  „Am răspuns"), apoi spune-i omului scurt că s-a făcut.
- `CAP_REACHED: ...` → nu mai delega; spune-i omului ce s-a întâmplat.

## Task nou
Contorul se auto-resetează după ~10 min. Pentru un email nou la scurt timp după altul:
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py --reset
```

## Reguli & capcane
- **APROBARE:** trimite doar ce a aprobat omul (spiritul mesajului). Doar dacă omul cere explicit
  „arată-mi draftul", arată-i întâi; altfel compui și trimiți direct, apoi confirmi scurt.
- **Risc de ocolire:** ACESTA e singurul mod de a-i da de lucru secretarei. Nu tasta niciodată
  `@<SECRETARY_USERNAME>` în proză — ai ocoli cap-ul și ai risca o buclă.
- **Conținut complet:** pune în `--prompt` emailul ÎNTREG (TO/SUBJECT/BODY sau UID/BODY), nu un rezumat.
- Un singur handoff pe rundă; după delegare, așteaptă confirmarea secretarei.
