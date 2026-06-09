---
name: assign-to-erin
description: "Deleagă un email de trimis către Erin, secretara. ACESTA e SINGURUL mod în care Michael îi dă lucru lui Erin — garantează mențiunea corectă, topicul Secretariat, numărul rundei și cap-ul dur de 3 runde. Folosește-l DOAR după ce omul a aprobat draftul emailului. Nu tasta niciodată @erin tu însuți."
version: 1.0.0
author: silviu
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Delegation, Email, Secretariat, Telegram]
---

# assign-to-erin — handoff determinist Michael → Erin (trimitere email)

Folosește-l NUMAI după ce ai arătat omului draftul emailului în General și el a spus „trimite".
Rulează scriptul cu calea ABSOLUTĂ a venv-python; pune în `--prompt` emailul aprobat, clar
delimitat, ca Erin să extragă exact destinatarul / subiectul / corpul.
(`<HERMES_HOME>` = calea absolută a dir-ului Hermes — `~/.hermes` expandat.)

```bash
<HERMES_HOME>/hermes-agent/venv/bin/python \
  <HERMES_HOME>/profiles/michael/skills/assign-to-erin/scripts/delegate.py \
  --prompt "TRIMITE EMAIL | TO: client@example.com | SUBJECT: Subiectul exact | BODY: Textul complet, exact cum l-a aprobat omul."
```
Scriptul postează `@erin_hannon_office_bot ROUND <n>: <prompt>` în topicul Secretariat
(mențiune + thread din `handoff.json`), cu contor de runde și cap dur. Tu NU scrii `@erin`.

## Output
- `DELEGATED ROUND <n> to @erin_hannon_office_bot ...` → așteaptă confirmarea lui Erin
  („Am trimis emailul..."), apoi spune-i omului în General că a plecat.
- `CAP_REACHED: ...` → nu mai delega; spune-i omului ce s-a întâmplat.

## Task nou
Contorul se auto-resetează după ~10 min inactivitate. Pentru un email nou la scurt timp după
altul, forțează start curat:
```bash
<HERMES_HOME>/hermes-agent/venv/bin/python \
  <HERMES_HOME>/profiles/michael/skills/assign-to-erin/scripts/delegate.py --reset
```

## Reguli & capcane
- **APROBARE întâi:** nu delega niciodată un email înainte ca omul să confirme draftul în General.
  Emailul către clienți reali e ireversibil.
- **Risc de ocolire:** ACESTA e singurul mod de a-i da de lucru lui Erin. Nu tasta niciodată
  `@erin_hannon_office_bot` în proza ta — ai ocoli cap-ul și ai risca o buclă.
- **Conținut, nu doar intenție:** pune în `--prompt` emailul COMPLET (TO/SUBJECT/BODY), nu un
  rezumat — Erin trimite verbatim ce primește.
- Un singur handoff pe rundă; după delegare, așteaptă confirmarea lui Erin.
