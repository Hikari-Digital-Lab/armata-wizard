---
name: adauga-membru-echipa
description: Adaugă un agent (worker) NOU peste o echipă Hermes existentă — cu botul lui de Telegram, topicul lui și gating-ul corect — care raportează la CEO (ex. Michael). Inspectează setup-ul existent, creează profilul + skill-ul de delegare CEO→worker nou și ACTUALIZEAZĂ SOUL-ul CEO-ului ca să știe de noul agent. Topologie hub (totul prin CEO), fără buclă indiferent de câți agenți. Autonom cu pauze pentru pașii Telegram; cere secretele la rulare. Folosește când utilizatorul vrea să adauge un personaj/worker nou la echipa de boți.
---

# Adaugă membru în echipă (worker nou → raportează la CEO)

Adaugă UN worker nou peste o echipă existentă (construită cu `reproducere-agenti-office` sau
`echipa-boti-hermes`). Topologie **hub**: noul worker are botul + topicul lui, e **gated**, și
vorbește DOAR cu CEO-ul. Doar CEO-ul rămâne liber → fără buclă, oricâți agenți adaugi.

Scripturi partajate: `scripts/` (`delegate.py`, `gen_image.py`, `manage.py`).
Exemple: `templates/`. (În exemple, `<HERMES_HOME>` = calea ABSOLUTĂ a dir-ului Hermes —
`~/.hermes` expandat: Linux `/home/<user>/.hermes`, macOS `/Users/<user>/.hermes`, Windows
`C:/Users/<user>/.hermes`.)

## REGULĂ DE INTERACȚIUNE (obligatorie)
**Orice** întrebare către utilizator se pune prin tool-ul **AskUserQuestion**, niciodată text
liber: confirmarea CEO-ului, specificația noului worker, confirmarea pașilor Telegram, și
colectarea token-ului nou (valori libere → opțiunea „Other"). Grupează logic (max 4 per apel).

**Pattern pentru pași fizici (obligatoriu):** când utilizatorul trebuie să facă ceva manual
(BotFather, topic nou), NU trimite la documente externe — **afișează pașii compleți PE ECRAN**
(text neutru, numerotat, cu URL-uri exacte), apoi într-**un singur** apel AskUserQuestion confirmă
că a terminat („Gata, am terminat" / „Am nevoie de ajutor") **și** colectează token-ul (în „Other").
Dacă alege „Am nevoie de ajutor", afișează o variantă mai detaliată și re-întreabă cu ACELAȘI apel.
Valorile pe care le poți obține singur (topic id) le iei TU (rulezi `curl`), nu le ceri userului.

## Pas 1 — Inspectează setup-ul existent
- Citește **team.json LIVE** = `~/.hermes/team.json` (HERMES_HOME; fallback: copia seed de lângă `manage.py`) → lista de profiluri.
- Identifică **CEO-ul** = profilul cu `TELEGRAM_REQUIRE_MENTION=false` în `.env`
  (`grep -l 'TELEGRAM_REQUIRE_MENTION=false' ~/.hermes/profiles/*/.env`). Confirmă cu userul prin **AskUserQuestion**.
- Citește din `.env`-ul CEO-ului: `TELEGRAM_GROUP_ALLOWED_CHATS` (group id) și
  `TELEGRAM_ALLOWED_TOPICS` (topicurile actuale). Notează workerii existenți (skill-urile
  `assign-to-*` din profilul CEO-ului).

## Pas 2 — Întreabă specificația noului worker (prin AskUserQuestion)
Detectează limba din SOUL-ul CEO-ului și folosește aceeași limbă. Întreabă în runde de max 4:

> APELEAZĂ AskUserQuestion (exemplu literal — copiază, adaptează):
> Runda 1:
>   Î1 — „Cum se numește noul agent și ce slug de profil (lowercase) vrei?"  → „Other"
>   Î2 — „Ce tip de worker este?"            opțiuni: ["Imagini (Gemini)"], ["Text"]
>   Î3 — „Cum se numește topicul lui nou?"   (ex. „Copywriting") → „Other"
>   Î4 — „Câte runde maxim CEO↔worker?"      opțiuni: ["3 (recomandat)"]   (alt număr → „Other")
> Runda 2 (dacă e nevoie): rol/specialitate + personalitate + model creier/imagini (toate în „Other").

## Pas 3 — PAUZĂ: pașii Telegram pentru noul bot

> AFIȘEAZĂ userului (text neutru, pas-cu-pas) — înlocuiește „<TOPIC_NAME>" cu topicul ales la Pas 2:
> ─────────────────────────────────────────────────────────────
> Hai să creăm botul de Telegram pentru noul agent. Durează ~3 minute.
>
> A. Creează botul în BotFather
>   1. Deschide Telegram și scrie către BotFather: https://t.me/BotFather (bifă albastră).
>   2. Trimite comanda:  /newbot
>   3. Dă-i un nume afișat (ex. numele agentului).
>   4. Dă-i un username care se TERMINĂ obligatoriu în „bot".
>   5. BotFather îți trimite un TOKEN (șir lung cu „:"). Copiază-l — îl ceri mai jos.
>   6. Trimite:  /setprivacy  → alege botul → „Disable".
>   7. Trimite:  /mybots → alege botul → „Bot Settings" →
>      „Group Privacy / Bot-to-Bot Communication Mode" → ON.
>
> B. Adaugă botul în grupul existent
>   8. Deschide grupul echipei (cel cu Topicuri).
>   9. Setările grupului → Add member → caută username-ul botului → adaugă-l.
>  10. Setările grupului → Administrators → Add admin → alege botul → confirmă.
>
> C. Creează topicul lui și scrie un mesaj
>  11. În grup, lista de topicuri → „+" → creează un topic nou numit „<TOPIC_NAME>".
>  12. Intră în „<TOPIC_NAME>" și scrie un mesaj care menționează botul, ex.: @username_bot salut
>      (așa pot citi id-ul topicului chiar cu privacy on).
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
>   - Topicurile apar ca file/categorii sus în grup; „+" e la capătul listei.

> DUPĂ confirmare (NU afișa comenzile userului):
>   - Verifică tu token-ul cu `getMe` → reține `username`-ul real al botului.

## Pas 4 — Ia topic id-ul nou (Claude rulează singur — userul NU rulează curl)
Oprește gateway-urile (`manage.py stop`). Rulează TU `getUpdates` cu tokenul noului bot (sau al
CEO-ului) → extrage `message_thread_id` al mesajului din topicul nou = `<TOPIC_NOU_ID>`. NU afișa
comanda userului.

## Pas 5 — Creează profilul noului worker
`hermes profile create <slug> --clone --description "<rol>"`, apoi în `config.yaml`:
- `model` (ca echipa), `agent.restart_drain_timeout: 20`;
- **același bloc anti-chatter**: `display.busy_ack_enabled:false` + UN SINGUR bloc
  `display.platforms.telegram` consolidat cu `streaming:false`, `tool_progress:off`,
  `interim_assistant_messages:false`, `long_running_notifications:false`, `cleanup_progress:true`,
  `busy_ack_detail:false`, `show_reasoning:false` (consolidează duplicatele de `platforms:`, altfel YAML ignoră în tăcere).
`.env` (gated, own topic), `chmod 600`:
```dotenv
GOOGLE_API_KEY=<din .env existent>
GEMINI_API_KEY=<din .env existent>
TELEGRAM_BOT_TOKEN=<TOKEN_NOU>
TELEGRAM_GROUP_ALLOWED_CHATS=-100<GROUP_ID>
TELEGRAM_REQUIRE_MENTION=true
TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true
TELEGRAM_ALLOWED_TOPICS=<TOPIC_NOU_ID>
```
Dacă e worker de imagini: copiază `gen_image.py` în `skills/image-studio/scripts/` + `image-studio/SKILL.md`.
Scrie `SOUL.md` (persona + „lucrezi DOAR în topicul tău; raportezi CEO-ului; acționezi la
task/feedback, taci la aprobări"), în limba echipei.

## Pas 6 — Skill de delegare CEO → worker nou
În profilul CEO-ului, creează `skills/assign-to-<slug>/`:
- `scripts/delegate.py` (copie din `scripts/delegate.py`),
- `handoff.json` → `{"worker_mention":"@<worker_username>","thread_id":"<TOPIC_NOU_ID>","max_rounds":<cap>,"reset_gap":600}`,
- `SKILL.md` (adaptat din `templates/assign-to-pam.SKILL.md`, cu numele noului worker).

## Pas 7 — Actualizează CEO-ul (cheie!)
- **`.env` CEO:** adaugă noul topic la `TELEGRAM_ALLOWED_TOPICS` (ex. `1,2,<TOPIC_NOU_ID>`).
- **`SOUL.md` CEO:** adaugă o secțiune despre noul agent: cine e (nume/rol), ce face, în ce topic,
  ȘI instrucțiunea „ca să-i delegi, rulează skill-ul `assign-to-<slug>` (NU tasta handle-ul lui)".
  Păstrează regula LOOP GUARD. Astfel CEO-ul „știe" de noul membru și-l poate folosi.

## Pas 8 — Înregistrează + repornește + verifică
- Adaugă `<slug>` în **team.json LIVE** (`~/.hermes/team.json`).
- `manage.py restart` (sau `fresh` dacă vrei start curat). Confirmă noul bot „✓ telegram connected".
- Test (afișează instrucțiunea, apoi confirmă prin AUQ; ține monitor auto-kill ca plasă):

> AFIȘEAZĂ userului: „Scrie în topicul «General» un task care necesită noul agent (ex.: «{rol}, fă-mi X»)."

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Cum a mers?"
>   opțiuni: ["Merge — workerul a răspuns, CEO a livrat"], ["Nu răspunde"], ["Buclă / chatter / topic greșit"]

  - DACĂ „Merge": confirmă în loguri lanțul (CEO `assign-to-<slug>` → worker în topicul lui → CEO în General)
    și declară succesul. ALTFEL: inspectează loguri + monitor și remediază (gating/handoff/token).

## Reguli
- Worker nou = ÎNTOTDEAUNA gated (`require_mention=true`) în topicul lui. Doar CEO-ul e liber.
- Delegare DOAR prin skill (mențiune+thread hardcodate + cap). Secretele doar în `.env`.
- NU atinge profilul `default`. NU modifica gating-ul celorlalți workeri.
