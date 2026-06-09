---
name: adauga-avocat
description: "Adaugă un agent AVOCAT (worker care verifică contracte: cercetează legislația pe internet cu web_search, pe un flux de 3 runde CEO↔avocat, apoi livrează DETERMINIST un verdict Go/No-Go scurt + un PDF cu analiza aprofundată) peste o echipă Hermes existentă. Default Toby Flenderson (The Office) cu fișiere gata-făcute; opțional persona custom. Topologie hub: avocatul e gated, raportează DOAR la CEO, fără buclă. Standalone (escape-hatch ca adauga-membru-echipa), declanșat când CEO-ul e rugat să verifice un contract. Încorporează toate lecțiile: backend web_search (ddgs), cap de căutări, livrare prin script determinist cu lock anti-duplicat, PDF cu analiza completă (salvată de avocat), reguli anti-duplicat pe sesiunile per-topic ale CEO-ului."
version: 1.0.0
author: silviu
license: Apache-2.0
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Telegram, Agents, Delegation, Legal, Contracts, PDF, Onboarding]
---

# Adaugă avocat (worker juridic → raportează la CEO)

Adaugă **UN** worker avocat peste o echipă existentă (construită cu `adauga-ceo` /
`reproducere-agenti-office` / `echipa-boti-hermes` / `adauga-membru-echipa`). Avocatul primește de la
CEO **un contract** (text sau clauze), **cercetează legislația pe internet** (`web_search`/DuckDuckGo)
pe un flux de **3 runde** de întrebări, apoi scrie o **analiză juridică aprofundată**. CEO-ul livrează
omului, în General, un **mesaj scurt Go/No-Go + 3-5 bullet-uri** și **PDF-ul cu analiza completă** —
totul **determinist**, printr-un script (CEO-ul nu „scrie romane" și nu dublează).

Topologie **hub**: avocatul are botul + topicul lui, e **gated**, vorbește DOAR cu CEO-ul. Doar
CEO-ul rămâne liber → fără buclă. Skill **standalone** (escape-hatch, ca `adauga-membru-echipa`): NU
face parte din lanțul artist→copywriter→web-developer; se declanșează când CEO-ul e rugat să verifice
un contract.

Self-contained: `scripts/` (`delegate.py` text-first config-driven, `make_pdf.py` Markdown→PDF via
Chrome, `deliver_verdict.py` PDF+postare cu **lock anti-duplicat**, `manage.py`, `monitor.py`),
`templates/` (Toby gata-făcut + skeleton custom + assign-to + contract-report + env + handoff +
config-changes + ceo-soul-additions).

## REGULĂ DE INTERACȚIUNE (obligatorie)
**Orice** întrebare către utilizator se pune prin tool-ul **AskUserQuestion**, niciodată text liber:
confirmarea CEO-ului, alegerea persona (Toby vs custom), limba, numele topicului, cap-ul de runde,
confirmarea pașilor Telegram și colectarea token-ului (valori libere → opțiunea „Other"). Max 4 per apel.

**Pattern pentru pași fizici (obligatoriu):** când utilizatorul trebuie să facă ceva manual
(BotFather, instalare Chrome), NU trimite la documente externe — **afișează pașii compleți PE ECRAN**
(text neutru, numerotat, cu URL-uri exacte), apoi într-**un singur** apel AskUserQuestion confirmă
că a terminat („Gata, am terminat" / „Am nevoie de ajutor") **și** colectează token-ul (în „Other").
Dacă alege „Am nevoie de ajutor", afișează o variantă mai detaliată și re-întreabă cu ACELAȘI apel.
Ce poți face singur (topic via API, `getUpdates`, `pip install ddgs`) faci TU, nu ceri userului.

## ANTI-BUCLĂ (regula de aur) — nu o încălca
- Exact UN bot e „liber" (CEO: `TELEGRAM_REQUIRE_MENTION=false`). Avocatul e **gated**
  (`TELEGRAM_REQUIRE_MENTION=true`) în topicul lui. `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true` peste tot.
- Delegare CEO→avocat **DOAR** prin `assign-to-<slug>` (`delegate.py`): mențiune + thread hardcodate
  în `handoff.json` + **cap dur de runde**. CEO-ul NU tastează niciodată `@<avocat>` în proză.
- NU atinge gating-ul celorlalți workeri. NU atinge profilul `default`.

## ⚠️ LECȚII ÎNVĂȚATE (încorporează-le — altfel bug-urile se repetă)
1. **`web_search` n-are backend implicit** → întoarce gol, iar modelul improvizează cu `execute_code`.
   FIX: instalează `ddgs` (DuckDuckGo, fără cheie) în venv-ul Hermes + `web.search_backend: ddgs` în
   config-ul avocatului (Pas 5). Fără asta, „cercetarea pe internet" NU funcționează.
2. **Avocatul supra-caută** (a făcut 28 căutări). FIX: regula din SOUL „**max ~5 web_search/rundă**".
3. **CEO-ul lipea analiza lungă în chat („romane") și sărea peste PDF.** FIX: livrare DOAR prin
   `deliver_verdict.py` (script), care face PDF + postează mesaj scurt; `send_message` interzis.
4. **CEO-ul are sesiuni SEPARATE per topic** (General vs Juridic) → livra de 2 ori. FIX: (a) reguli
   anti-duplicat pe topic în SOUL-ul CEO (în General doar deleagă+confirmă; în Juridic livrează o dată),
   (b) **lock de idempotență** în `deliver_verdict.py` (aceeași analiză → `SKIP`).
5. **PDF-ul trebuie să conțină analiza APROFUNDATĂ, nu rezumatul.** FIX: avocatul își salvează analiza
   completă într-un fișier (`avocat_analiza.md`), iar `deliver_verdict.py` îl citește (cu guard de lungime).
6. **Topicul se poate crea via API** (CEO admin cu `can_manage_topics` → `createForumTopic`) — nu mai
   e nevoie de pas manual (Pas 4). Privacy=Disable + adăugarea botului în grup rămân manuale.

---

## Pas 1 — Inspectează echipa existentă
- **team.json LIVE** = `~/.hermes/team.json` (HERMES_HOME) — manifestul **canonic** al echipei,
  ținut în HERMES_HOME ca să rămână editabil și când skill-ul rulează dintr-un cache de plugin
  read-only. `manage.py` îl citește de acolo (fallback: seed-ul bundled de lângă `scripts/`, apoi
  env `HERMES_TEAM_PROFILES`). Pe ACELA îl actualizezi (`profiles`/`watchers`) și repornești echipa.
- Identifică **CEO-ul** = profilul cu `TELEGRAM_REQUIRE_MENTION=false`:
  `grep -l 'TELEGRAM_REQUIRE_MENTION=false' ~/.hermes/profiles/*/.env`. **Confirmă prin AskUserQuestion.**
- Din `.env`-ul CEO-ului citește `TELEGRAM_GROUP_ALLOWED_CHATS` (`<GROUP_ID>`) și
  `TELEGRAM_ALLOWED_TOPICS` (topicuri actuale). Notează workerii existenți (skill-urile `assign-to-*`).
- Detectează **limba** și **modelul creier** din SOUL-ul/config-ul echipei (ex. `gemini-3.5-flash`).
- **Coliziune slug:** verifică să nu existe deja un profil cu slug-ul ales (default `avocat`); dacă da,
  alege altul prin AskUserQuestion.

## Pas 2 — Alege persona & parametrii (prin AskUserQuestion)
Întreabă într-un apel (max 4):

> APELEAZĂ AskUserQuestion (exemplu literal — copiază, adaptează):
> Î1 — „Ce personaj vrei pentru avocat?"  opțiuni: ["Toby Flenderson (The Office)"], ["Alt personaj (custom)"]
> Î2 — „În ce limbă vorbește avocatul?"    opțiuni: ["Ca echipa"], ["Română"], ["Engleză"]   (alta → „Other")
> Î3 — „Cum se numește topicul lui?"        opțiuni: ["Juridic (recomandat)"]   (alt nume → „Other")
> Î4 — „Câte runde maxim CEO↔avocat?"       opțiuni: ["3 (recomandat)"]   (alt număr → „Other")

- **Slug** profil (lowercase): default **`avocat`** (neutru).
- Dacă a ales **custom**, fă o a doua rundă AUQ: **numele**, **slug-ul**, **descrierea
  caracterului/tonului** (în „Other"). Dacă **Toby**: slug implicit `avocat`, persona din `templates/toby.SOUL.md`.

## Pas 3 — PAUZĂ: pașii Telegram pentru botul nou
(Topicul „Juridic" îl creez EU automat la Pas 4 — aici userul face doar botul + adăugarea în grup.)

> AFIȘEAZĂ userului (text neutru, pas-cu-pas):
> ─────────────────────────────────────────────────────────────
> Hai să creăm botul de Telegram pentru avocat. Durează ~3 minute.
>
> A. Creează botul în BotFather
>   1. Deschide Telegram și scrie către BotFather: https://t.me/BotFather (bifă albastră).
>   2. Trimite comanda:  /newbot
>   3. Dă-i un nume afișat (ex. „Toby Flenderson").
>   4. Dă-i un username care se TERMINĂ obligatoriu în „bot" (ex. toby_avocat_bot).
>   5. BotFather îți trimite un TOKEN (șir lung cu „:"). Copiază-l — îl ceri mai jos.
>   6. Trimite:  /setprivacy  → alege botul → „Disable".
>   7. Trimite:  /mybots → alege botul → „Bot Settings" →
>      „Group Privacy / Bot-to-Bot Communication Mode" → ON.
>
> B. Adaugă botul în grupul existent
>   8. Deschide grupul echipei (cel cu Topicuri).
>   9. Setările grupului → Add member → caută username-ul botului → adaugă-l.
>  10. Setările grupului → Administrators → Add admin → alege botul → confirmă.
>      (Topicul „Juridic" NU trebuie creat manual — îl fac eu prin API după ce confirmi.)
> ─────────────────────────────────────────────────────────────

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Ai terminat pașii de mai sus?"
>   opțiuni: ["Gata, am terminat"], ["Am nevoie de ajutor"]
> Întrebarea 2 — „Lipește token-ul noului bot (de la BotFather)"  → user scrie în „Other"
> (Cheia Gemini NU se cere — o iei din `.env`-ul unui profil existent.)

> DACĂ a ales „Am nevoie de ajutor": afișează varianta detaliată, apoi re-întreabă cu ACELAȘI AUQ:
>   - BotFather îl găsești căutând „BotFather" în Telegram (bifă albastră).
>   - Dacă `/setprivacy` arată deja „Privacy: DISABLED", e gata.
>   - „Bot Settings" pe telefon = meniul cu trei puncte din conversația cu BotFather.
>   - Promovare admin pe mobil: numele grupului → Administrators → Add Administrator.

> DUPĂ confirmare (NU afișa comenzile userului):
>   - Verifică tu token-ul cu `getMe` → reține `username`-ul real `<LAWYER_USERNAME>`.
>     (`can_read_all_group_messages:false` = privacy încă on — delegarea merge oricum, dar pentru curățenie cere Disable.)

## Pas 4 — Creează topicul „Juridic" + ia topic id-ul (Claude rulează singur)
**Automat prin API** (recomandat): cu **tokenul CEO-ului** (admin cu `can_manage_topics`), rulează TU:
```bash
curl -s "https://api.telegram.org/bot<CEO_TOKEN>/createForumTopic" \
  --data-urlencode "chat_id=<GROUP_ID>" --data-urlencode "name=<TOPIC_NAME>"
```
→ răspunsul conține `message_thread_id` = **`<TOPIC_ID>`**. (Verifică întâi `getChatMember` că CEO-ul are
`can_manage_topics:true`.) NU afișa comanda userului.

**Fallback manual** (doar dacă CEO-ul nu e admin / API dă eroare):

> APELEAZĂ AskUserQuestion (exemplu literal — doar pe fallback):
> Întrebarea 1 — „Nu pot crea topicul automat. Creează te rog un topic nou numit „<TOPIC_NAME>" în grup și scrie în el un mesaj care menționează noul bot (ex. @toby_avocat_bot salut), apoi confirmă."
>   opțiuni: ["Gata, am creat topicul"], ["Am nevoie de ajutor"]

  După confirmare, oprește gateway-urile (`<venv_python> <live_manage.py> stop`) și rulează TU
  `getUpdates` cu tokenul noului bot → extrage `message_thread_id` = `<TOPIC_ID>`.

## Pas 5 — Creează profilul avocatului
1. `hermes profile create <slug> --clone --description "<rol juridic>"`.
2. **config.yaml** — urmează `templates/config-changes.md`: copiază config-ul unui worker gated existent
   SAU al CEO-ului (anti-chatter + modelul echipei + `restart_drain_timeout: 20`), apoi
   `kanban.dispatch_in_gateway: false`, menține gated, și **⭐ `web.search_backend: ddgs`**.
3. **⭐ Instalează `ddgs`** (Claude o face singur) + verifică Chrome:
   ```bash
   uv pip install --python <HERMES_HOME>/hermes-agent/venv/bin/python ddgs
   <venv_python> -c "import ddgs; print('ddgs', ddgs.__version__)"
   <venv_python> -c "import shutil,os; cands=[os.environ.get('AGENT_BROWSER_EXECUTABLE_PATH','').strip(),'google-chrome','google-chrome-stable','chromium','chromium-browser','chrome','/usr/bin/google-chrome','/usr/bin/chromium','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','C:/Program Files/Google/Chrome/Application/chrome.exe']; f=next((r for c in cands if c for r in [shutil.which(c) if not os.path.isabs(c) else (c if os.path.exists(c) else None)] if r), None); print('chrome:', f or 'NOT FOUND')"
   ```
   `ddgs` o instalezi TU (nu cere userului). **Chrome** e nivel-sistem — dacă lipsește, NU îl poți
   instala singur fără sudo; afișează instrucțiunea + întreabă prin AUQ:

> AFIȘEAZĂ userului (doar dacă Chrome lipsește): „PDF-ul cu analiza juridică se randează cu Google Chrome.
> Instalează-l de la https://www.google.com/chrome/ (sau pe Linux: `sudo apt install google-chrome-stable`)."

> APELEAZĂ AskUserQuestion (exemplu literal — doar dacă Chrome lipsește):
> Întrebarea 1 — „Chrome (necesar pentru PDF) nu e instalat. Cum procedăm?"
>   opțiuni: ["L-am instalat acum"], ["Am nevoie de ajutor"], ["Continuă fără PDF (doar verdict text)"]

   (Avocatul e worker de TEXT — NU copia `gen_image.py`, NU crea `image-studio`; păstrează tool-urile
   din `hermes-cli`, inclusiv web/browser.)
4. **.env** din `templates/avocat.env` — completează `<GEMINI_KEY>` (din `.env`-ul unui profil existent
   — NU inventa), `<TOKEN>`, `<GROUP_ID>`, `<TOPIC_ID>`, `<TOPIC_NAME>`; păstrează cele 3 chei anti-chatter.
   `chmod 600`.
5. **SOUL.md** (în TOATE template-urile de mai jos, înlocuiește și **`<HERMES_HOME>`** = calea
   ABSOLUTĂ a directorului Hermes — `~/.hermes` expandat; rădăcina care conține `hermes-agent/` și
   `profiles/`. Pe Linux `/home/<user>/.hermes`, macOS `/Users/<user>/.hermes`, Windows
   `C:/Users/<user>/.hermes`):
   - Toby → `templates/toby.SOUL.md`, înlocuiește `<HERMES_HOME>`, `<LANGUAGE>`, `<LAWYER_USERNAME>`,
     `<CEO_USERNAME>`, `<TOPIC_NAME>`, `<CEO_PROFILE>`, `<MAX_ROUNDS>`, `<SLUG>`.
   - Custom → `templates/avocat.SOUL.md`, înlocuiește și `<NAME>`, `<CHARACTER_DESCRIPTION>`, `<TONE>`.
   - Verifică: regula „max ~5 web_search/rundă" și calea fișierului `avocat_analiza.md` din SOUL pointează
     spre `profiles/<CEO_PROFILE>/workspace/contracts/avocat_analiza.md`.

## Pas 6 — Skill-uri în profilul CEO-ului
**a) `skills/assign-to-<slug>/`** (delegare CEO → avocat):
- `scripts/delegate.py` = copie din `scripts/delegate.py` (text-first, config-driven, cap din handoff).
- `handoff.json` din `templates/handoff.json` cu `<LAWYER_USERNAME>`, `<TOPIC_ID>`, `<MAX_ROUNDS>`.
- `SKILL.md` din `templates/assign-to-avocat.SKILL.md` cu placeholderele înlocuite (`<HERMES_HOME>`,
  `<SLUG>`, `<NAME>`, `<VENV_PYTHON>`, `<CEO_PROFILE>`, `<LAWYER_USERNAME>`, `<TOPIC_NAME>`, `<MAX_ROUNDS>`).

**b) `skills/contract-report/`** (livrarea deterministă — PDF + verdict):
- `scripts/make_pdf.py` = copie din `scripts/make_pdf.py`.
- `scripts/deliver_verdict.py` = copie din `scripts/deliver_verdict.py` (citește `avocat_analiza.md`
  din `<CEO_PROFILE>/workspace/contracts/`, are lock anti-duplicat).
- `SKILL.md` din `templates/contract-report.SKILL.md` cu `<HERMES_HOME>`, `<VENV_PYTHON>`, `<CEO_PROFILE>` înlocuite.

## Pas 7 — Actualizează CEO-ul (cheie!)
- **`.env` CEO:** adaugă `<TOPIC_ID>` la `TELEGRAM_ALLOWED_TOPICS`.
- **`SOUL.md` CEO:** injectează blocurile din `templates/ceo-soul-additions.md` (parametrizate —
  înlocuiește și `<HERMES_HOME>`, `<VENV_PYTHON>`, `<CEO_PROFILE>`, `<SLUG>`), MERGE
  în secțiunile existente (team, topicuri, LOOP GUARD) — nu duplica. Conțin: noul membru, topicul,
  **fluxul complet de verificare contract cu regulile ANTI-DUPLICAT pe topic** (General doar
  deleagă+confirmă; Juridic livrează o singură dată cu `deliver_verdict.py`; `send_message`/cercetare
  proprie interzise) și extinderea LOOP GUARD cu `@<LAWYER_USERNAME>` + topicul Juridic.

## Pas 8 — Înregistrează + repornește + verifică
- Adaugă `<slug>` în **team.json-ul echipei LIVE** (Pas 1).
- `<venv_python> <live_manage.py> fresh` (restart + șterge sesiuni — necesar după persona/SOUL nou și ca
  să dispară eventuale sesiuni vechi confuze).
- Confirmă „✓ telegram connected" (și pentru CEO, cu SOUL modificat), fără erori reale, **fără**
  `📬 No home channel`. Gating: exact UN bot liber (CEO), restul gated.
- **Test controlat + monitor auto-kill:**
  - Pornește monitorul în fundal:
    `<venv_python> scripts/monitor.py --python <venv_python> --manage <live_manage.py> --profiles <ceo>,<workeri>,<slug> --max-deliveries <cap+2> --window 240`
  - Declanșează un ciclu: `assign-to-<slug>/scripts/delegate.py --reset`, apoi `--prompt "<contract de
    test cu clauze + întrebare>"`. Verifică în loguri: avocatul folosește **`web_search`** (nu
    execute_code), salvează `avocat_analiza.md`, răspunde cu mențiune către CEO; rulează ultima rundă
    (FINAL), apoi `deliver_verdict.py` → în General apare **un singur** mesaj scurt + **PDF** (2+ pagini,
    analiza completă). Fără chatter, fără buclă, fără dublare. Monitorul oprește echipa la runaway.
  - Verifică idempotența: a doua rulare `deliver_verdict.py` cu aceeași analiză → `SKIP`.
  - Confirmă rezultatul cu userul:

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Cum a mers verificarea de contract?"
>   opțiuni: ["Merge — verdict + PDF livrate o singură dată"], ["Nu răspunde"], ["Dublare / fără PDF / fără cercetare"]

  - DACĂ „Merge": declară succesul. ALTFEL: inspectează loguri + monitor și remediază
    (ddgs/web_search, lock anti-duplicat, Chrome/PDF, gating/handoff).
  - La final, `--reset` la contoare și `fresh` pentru start curat.

## Reguli finale
- Avocat nou = ÎNTOTDEAUNA gated în topicul lui. Doar CEO-ul e liber.
- Delegare DOAR prin `assign-to-<slug>` (mențiune+thread+cap). Livrare DOAR prin `deliver_verdict.py`
  (determinist, anti-duplicat). Secretele doar în `.env` (`chmod 600`), niciodată în doc/git.
- NU atinge profilul `default`, NU modifica gating-ul celorlalți workeri.
- Acest skill adaugă **un singur** avocat (rol fix: contract→cercetare legislație→analiză→PDF); doar
  persona/limba/topic/cap diferă. **Standalone** — nu e parte din lanțul artist→copywriter→web-developer.
