---
name: contract-report
description: "Livrarea deterministă a unei verificări de contract: deliver_verdict.py ia analiza aprofundată salvată de avocat, o transformă în PDF stilizat (make_pdf.py, Chrome headless) ȘI postează în General un mesaj scurt Go/No-Go + 3-5 bullet-uri cu PDF-ul atașat — cu lock anti-duplicat. Folosit de manager la finalul fluxului de verificare contract."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Legal, Contracts, PDF, Report, Delivery]
---

# contract-report — livrare deterministă: PDF aprofundat + verdict scurt

Trăiește în profilul **managerului** (CEO). Două scripturi:
- `scripts/make_pdf.py` — Markdown → PDF stilizat via **Chrome headless** (printează `MEDIA:<pdf>`).
- `scripts/deliver_verdict.py` — **comanda principală**: ia analiza completă, cheamă `make_pdf.py`,
  apoi postează în General (prin tokenul managerului) mesajul scurt + PDF-ul ca document. Are **lock
  anti-duplicat** (aceeași analiză → `SKIP`).

## Comanda principală — `deliver_verdict.py`
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<CEO_PROFILE>/skills/contract-report/scripts/deliver_verdict.py \
  --decision "<GO|NO-GO|GO-CONDITII>" \
  --title "Analiză contract — <nume/obiect>" \
  --intro "<o linie scurtă, în caracter>" \
  --summary "- argument 1\n- argument 2\n- argument 3"
```
- **NU** pasezi analiza: e citită automat din fișierul salvat de avocat,
  `<HERMES_HOME>/profiles/<CEO_PROFILE>/workspace/contracts/avocat_analiza.md`.
  (Poți forța altă sursă cu `--md <fișier>` sau `--text "<markdown>"`.)
- PDF-ul conține analiza **APROFUNDATĂ** completă; `--summary` = DOAR cele 3-5 bullet-uri din chat.
- Guard: dacă analiza din fișier lipsește sau e < ~400 caractere, refuză (ca să nu iasă un PDF
  trunchiat) și-ți spune să salvezi analiza integrală.

## Output
- `DELIVERED: posted verdict + PDF to General. PDF=...` → gata, NU mai posta nimic.
- `SKIP: ... deja livrată ...` → lock anti-duplicat; nu retrimite (e normal dacă a doua sesiune încearcă).
- `ERROR: ...` → citește mesajul (fișier lipsă/scurt, Chrome lipsă, token lipsă) și corectează.

## Doar PDF-ul (fără postare), dacă vrei separat
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<CEO_PROFILE>/skills/contract-report/scripts/make_pdf.py \
  --md "<HERMES_HOME>/profiles/<CEO_PROFILE>/workspace/contracts/avocat_analiza.md" \
  --title "Analiză contract — <obiect>" --decision "NO-GO"
```
Printează `MEDIA:<pdf>` (livrare manuală — dar prefer `deliver_verdict.py`, e determinist + anti-duplicat).

## Dependențe
- **Chrome/Chromium** instalat (pentru randarea PDF). `make_pdf.py` îl caută automat (inclusiv
  `AGENT_BROWSER_EXECUTABLE_PATH`).
- Pachetul Python **`markdown`** (de obicei prezent în venv-ul Hermes; altfel PDF-ul cade pe text simplu).
