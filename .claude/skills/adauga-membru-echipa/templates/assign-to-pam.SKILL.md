---
name: assign-to-pam
description: "Deleagă un task de imagine (sau feedback) către Pam. ACESTA e SINGURUL mod în care Michael îi dă lucru lui Pam — garantează mențiunea corectă, topicul Art, numărul rundei și cap-ul dur de 3 runde. Nu tasta niciodată @pam tu însuți."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Delegation, Workflow, Telegram]
---

# assign-to-pam — handoff determinist Michael → Pam

Rulează scriptul cu calea ABSOLUTĂ a venv-python:
```bash
<VENV_PYTHON> <CALE_SKILL>/scripts/delegate.py \
  --prompt "PROMPT DE IMAGINE ÎN ENGLEZĂ (prima dată) sau feedback acționabil (pushback)"
```
Scriptul postează `@<PAM_USERNAME> ROUND <n>: <prompt>` în topicul Art (mențiune + thread din
`handoff.json`), cu contor de runde și cap dur. Tu NU scrii `@pam`.

## Output
- `DELEGATED ROUND <n> to ...` → așteaptă imaginea lui Pam, apoi evaluează.
- `CAP_REACHED: ...` → NU mai delega; livrează cea mai bună imagine în General și oprește-te.

## Task nou
Contorul se auto-resetează după ~10 min inactivitate. Ca să forțezi un start curat imediat:
```bash
<VENV_PYTHON> <CALE_SKILL>/scripts/delegate.py --reset
```

## Reguli & capcane (învățate)
- **Risc de ocolire:** ACESTA e singurul mod de delegare. Nu tasta niciodată `@<PAM_USERNAME>`
  în proza ta — ar ocoli cap-ul și ar risca o buclă.
- **Scurgere de contor între task-uri consecutive:** dacă omul îți dă un task NOU la scurt timp
  după unul terminat (sub 10 min), reset-ul automat n-a apucat să se declanșeze. Rulează MANUAL
  cu `--reset` înainte de prima rundă a noului task, altfel contorul continuă și ajungi la
  `CAP_REACHED` prematur.
- **Un singur handoff pe rundă.** După delegare, așteaptă imaginea lui Pam înainte de orice.
