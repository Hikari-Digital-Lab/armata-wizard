---
name: assign-to-<SLUG>
description: "Gestionează și deleagă verificarea unui contract către <NAME> (avocatul echipei) în topicul <TOPIC_NAME>, pe fluxul de <MAX_ROUNDS> runde, și livrează DETERMINIST un verdict Go/No-Go scurt + PDF cu analiza aprofundată în General. NU tasta niciodată @<LAWYER_USERNAME> în proză; livrarea se face DOAR cu deliver_verdict.py."
version: 1.0.0
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Delegation, Workflow, Telegram, Legal, Contracts, Contract-Review]
---

# assign-to-<SLUG> — handoff determinist (manager) → <NAME> (avocat)

Folosește când omul îți cere să verifici/analizezi un contract înainte de semnare. Tu ești hub-ul:
<NAME> face analiza juridică detaliată + cercetează legislația pe internet; tu o livrezi printr-un
**mesaj scurt Go/No-Go + PDF cu analiza completă**, determinist.

## ⛔⛔ ANTI-DUPLICAT — ai un „creier" separat pe fiecare topic
- **În topicul General** (omul îți scrie): NU analiza contractul, NU livra, NU scrie concluzii.
  Faci DOAR: delegi runda 1 la <NAME> (`delegate.py`) și spui o linie scurtă „<NAME> se ocupă, revin".
  Apoi te OPREȘTI. Livrarea NU se face din General.
- **În topicul <TOPIC_NAME>** (<NAME> ți-a răspuns): conduci rundele și, la final, rulezi
  `deliver_verdict.py` O SINGURĂ DATĂ — el postează singur rezultatul în General.
- `deliver_verdict.py` are lock anti-duplicat (aceeași analiză → `SKIP` a doua oară). NU reposta manual.
- NICIODATĂ `send_message` pentru analiză; NICIODATĂ `web_search`/`terminal` ca să cercetezi tu legea.

## Fluxul (cap dur de <MAX_ROUNDS> runde)
### 1. Obține contractul (General)
Cere textul/clauzele + contextul (cine e clientul, scopul, ce-l îngrijorează). O singură dată, apoi
deleagă. (Dacă omul trimite un **PDF**, extrage-i textul cu pypdf/terminal DOAR ca input pentru <NAME>
— nu-l analiza tu.)

### 2. Runda 1 — delegare la <NAME> (<TOPIC_NAME>)
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py \
  --prompt "CONTRACT: <clauzele de analizat> + context: <scop, client, îngrijorări>"
```
<NAME> cercetează legislația și răspunde cu prima listă de riscuri + întrebări.

### 3. Rundele 2..(<MAX_ROUNDS>-1) — răspunde & aprofundează (<TOPIC_NAME>)
Răspunde la întrebările lui <NAME> (din ce ți-a spus omul; întreabă-l o singură dată în General doar
dacă e esențial), apoi rulează din nou `delegate.py --prompt "<răspunsuri/follow-up>"`.

### 4. Runda <MAX_ROUNDS> (FINAL) — cere analiza finală (<TOPIC_NAME>)
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py \
  --prompt "FINAL: dă-mi analiza finală — ce trebuie verificat cu clientul înainte de semnare"
```
<NAME> scrie analiza completă (REZUMAT / DE VERIFICAT / TEMEI LEGAL / CONCLUZIE) ȘI o salvează în
`<HERMES_HOME>/profiles/<CEO_PROFILE>/workspace/contracts/avocat_analiza.md`.
La `CAP_REACHED`, oprește delegările și treci la livrare cu cea mai bună analiză de până atunci.

### 5. Livrarea — O SINGURĂ comandă deterministă (General)
NU lipi analiza în chat. Rulează `deliver_verdict.py` O SINGURĂ DATĂ; el ia analiza aprofundată din
fișierul salvat de <NAME>, face PDF-ul și postează în General mesajul scurt + PDF-ul:
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<CEO_PROFILE>/skills/contract-report/scripts/deliver_verdict.py \
  --decision "<GO|NO-GO|GO-CONDITII>" \
  --title "Analiză contract — <nume/obiect>" \
  --intro "<o linie scurtă în stil personaj>" \
  --summary "- argument 1\n- argument 2\n- argument 3"
```
- `--decision` din CONCLUZIA lui <NAME>. `--summary` = DOAR 3–5 bullet-uri scurte (chat = scurt,
  PDF = aprofundat). NU pasezi analiza — e citită automat din fișier.
- Dacă dă eroare că fișierul lipsește/e prea scurt: salvează analiza completă a lui <NAME> în
  `avocat_analiza.md` cu `write_file` și reia.
- La `DELIVERED: ...`, **ești gata** — nu mai posta nimic.

## Task nou / reset contor
Contorul se auto-resetează după ~10 min. Pentru start curat imediat:
```bash
<VENV_PYTHON> \
  <HERMES_HOME>/profiles/<CEO_PROFILE>/skills/assign-to-<SLUG>/scripts/delegate.py --reset
```

## Reguli
- Singurul mod de delegare către <NAME> e `delegate.py` (mențiune+thread+cap din `handoff.json`).
  Nu tasta `@<LAWYER_USERNAME>` în proză.
- Cap <MAX_ROUNDS> runde; la `CAP_REACHED` te oprești din delegat.
- Un singur handoff pe rundă (așteaptă răspunsul lui <NAME> înainte de următorul).
- Secretele doar în `.env`.
