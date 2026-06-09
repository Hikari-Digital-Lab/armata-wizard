---
name: adauga-copywriter
description: "Adaugă un agent COPYWRITER (worker text care primește imagine+brief și scrie textul de reclamă) peste o echipă Hermes existentă. Default Ryan Howard (The Office) cu fișiere gata-făcute; opțional persona custom (alt nume/caracter). Topologie hub: copywriter-ul e gated, raportează DOAR la CEO, fără buclă. Flux: CEO → worker imagini → copywriter (imagine+brief) → CEO livrează imagine+copy."
version: 1.0.0
author: silviu
license: Apache-2.0
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Telegram, Agents, Delegation, Copywriting, Onboarding]
---

# Adaugă copywriter (worker text → raportează la CEO)

Adaugă **UN** worker copywriter peste o echipă existentă (construită cu
`reproducere-agenti-office` / `echipa-boti-hermes` / `adauga-membru-echipa`). Copywriter-ul
primește o **imagine** (trimisă de CEO în topicul lui) + un **brief** și întoarce **textul de
advertisement** (headline / body / CTA). Topologie **hub**: copywriter-ul are botul + topicul
lui, e **gated**, vorbește DOAR cu CEO-ul. Doar CEO-ul rămâne liber → fără buclă.

Self-contained: `scripts/` (`delegate.py` cu suport `--image`, `manage.py`, `monitor.py`),
`templates/` (fișierele exacte ale lui Ryan + skeleton custom + config-changes).

## REGULĂ DE INTERACȚIUNE (obligatorie)
**Orice** întrebare către utilizator se pune prin tool-ul **AskUserQuestion**, niciodată text
liber: confirmarea CEO-ului, alegerea persona (Ryan vs custom), limba, specificația, confirmarea
pașilor Telegram și colectarea token-ului (valori libere → opțiunea „Other"). Grupează logic
(max 4 per apel), mai multe runde dacă e nevoie.

**Pattern pentru pași fizici (obligatoriu):** când utilizatorul trebuie să facă ceva manual
(BotFather, topic nou), NU trimite la documente externe — **afișează pașii compleți PE ECRAN**
(text neutru, numerotat, cu URL-uri exacte), apoi într-**un singur** apel AskUserQuestion confirmă
că a terminat („Gata, am terminat" / „Am nevoie de ajutor") **și** colectează token-ul (în „Other").
Dacă alege „Am nevoie de ajutor", afișează o variantă mai detaliată și re-întreabă cu ACELAȘI apel.
Valorile pe care le poți obține singur (topic id, group id) le iei TU (rulezi `curl`), nu le ceri userului.

## ANTI-BUCLĂ (regula de aur) — nu o încălca
- Exact UN bot e „liber" (CEO: `TELEGRAM_REQUIRE_MENTION=false`). Copywriter-ul e **gated**
  (`TELEGRAM_REQUIRE_MENTION=true`) în topicul lui. `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true` peste tot.
- Delegare CEO→copywriter **DOAR** prin skill-ul `assign-to-<slug>` (`delegate.py`): mențiune +
  thread hardcodate în `handoff.json` + **cap dur de runde**. CEO-ul NU tastează niciodată
  `@<copywriter>` în proză.
- NU atinge gating-ul celorlalți workeri. NU atinge profilul `default`.

---

## Pas 1 — Inspectează echipa existentă
- **team.json LIVE** = `~/.hermes/team.json` (HERMES_HOME) — manifestul **canonic** al echipei,
  ținut în HERMES_HOME ca să rămână editabil și când skill-ul rulează dintr-un cache de plugin
  read-only. `manage.py` îl citește de acolo (fallback: seed-ul bundled de lângă `scripts/`, apoi
  env `HERMES_TEAM_PROFILES`). Pe ACELA îl actualizezi (`profiles`/`watchers`) și repornești echipa.
- Identifică **CEO-ul** = profilul cu `TELEGRAM_REQUIRE_MENTION=false`:
  `grep -l 'TELEGRAM_REQUIRE_MENTION=false' ~/.hermes/profiles/*/.env`. **Confirmă prin AskUserQuestion.**
- Din `.env`-ul CEO-ului citește: `TELEGRAM_GROUP_ALLOWED_CHATS` (group id) și
  `TELEGRAM_ALLOWED_TOPICS` (topicuri actuale). Notează workerii existenți (skill-urile
  `assign-to-*` din profilul CEO-ului).
- **Worker de imagini (upstream)?** Verifică dacă există un worker care produce imagini (ex. unul
  cu skill `image-studio` / `gen_image.py`). Dacă NU există, avertizează utilizatorul:

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Nu am găsit un worker de imagini. Fluxul imagine→copy nu va avea sursă automată (copywriter-ul lucrează doar pe imagini trimise direct de CEO). Continuăm?"
>   opțiuni: ["Da, continuă"], ["Nu, mă opresc"]

  Continuă doar dacă a ales „Da".

## Pas 2 — Alege persona (prin AskUserQuestion)
Topicul copywriter-ului este **fix „Copywriting" — NU întreba**. Întreabă restul într-un apel:

> APELEAZĂ AskUserQuestion (exemplu literal — copiază, adaptează):
> Î1 — „Ce personaj vrei pentru copywriter?"  opțiuni: ["Ryan Howard (The Office)"], ["Alt personaj (custom)"]
> Î2 — „În ce limbă scrie copywriter-ul?"      opțiuni: ["Ca echipa"], ["Română"], ["Engleză"]   (alta → „Other")
> Î3 — „Câte runde maxim CEO↔copywriter?"      opțiuni: ["3 (recomandat)"]   (alt număr → „Other")

- Dacă a ales **custom**, fă o a doua rundă AUQ: **numele**, **slug-ul** (lowercase), **descrierea
  caracterului/tonului** (în „Other"). Dacă **Ryan**: slug implicit `ryan`, persona din `templates/ryan.SOUL.md`.

## Pas 3 — PAUZĂ: pașii Telegram pentru botul nou

> AFIȘEAZĂ userului (text neutru, pas-cu-pas):
> ─────────────────────────────────────────────────────────────
> Hai să creăm botul de Telegram pentru copywriter. Durează ~3 minute.
>
> A. Creează botul în BotFather
>   1. Deschide Telegram și scrie către BotFather: https://t.me/BotFather (bifă albastră).
>   2. Trimite comanda:  /newbot
>   3. Dă-i un nume afișat (ex. „Ryan Howard").
>   4. Dă-i un username care se TERMINĂ obligatoriu în „bot" (ex. ryan_howard_copy_bot).
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
> C. Creează topicul „Copywriting" și scrie un mesaj
>  11. În grup, lista de topicuri → „+" → creează un topic nou numit exact „Copywriting".
>  12. Intră în „Copywriting" și scrie un mesaj care MENȚIONEAZĂ botul, ex.: @ryan_howard_copy_bot salut
>      (mesajul cu mențiune îmi permite să citesc id-ul topicului chiar cu privacy on).
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
>   - Topicul trebuie numit exact „Copywriting"; „+" e la capătul listei de topicuri.
>   - Mențiunea (@…_bot) e obligatorie în mesajul de test, altfel nu pot citi id-ul topicului cu privacy on.

> DUPĂ confirmare (NU afișa comenzile userului):
>   - Verifică tu token-ul cu `getMe` → reține `username`-ul real al copywriter-ului.

## Pas 4 — Ia topic id-ul nou (Claude rulează singur — userul NU rulează curl)
Oprește gateway-urile (`<venv_python> <live_manage.py> stop`). Rulează TU `getUpdates` cu **tokenul
noului bot**: `curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"` → extrage `message_thread_id`
al mesajului din topicul „Copywriting" (cel cu mențiune) = `<TOPIC_ID>`. NU afișa comanda userului.
Reține `<TOPIC_ID>` și `<GROUP_ID>`.

## Pas 5 — Creează profilul copywriter-ului
1. `hermes profile create <slug> --clone --description "<rol>"`.
2. **config.yaml** — urmează `templates/config-changes.md`: copiază config-ul unui **worker gated
   existent** (ex. workerul de imagini) SAU al CEO-ului peste cel clonat (ca să iei blocul
   anti-chatter verificat + modelul echipei + `restart_drain_timeout: 20`), apoi setează
   **`kanban.dispatch_in_gateway: false`** și asigură-te că rămâne gated.
3. **.env** din `templates/copywriter.env` — completează `<GEMINI_KEY>` (reutilizat din `.env`-ul
   unui profil existent — NU inventa), `<TOKEN>`, `<GROUP_ID>`, `<TOPIC_ID>`; păstrează cele 3
   chei anti-chatter (`TELEGRAM_HOME_CHANNEL`, `TELEGRAM_HOME_CHANNEL_NAME=Copywriting`,
   `TELEGRAM_CRON_THREAD_ID=<TOPIC_ID>`). `chmod 600`.
4. **SOUL.md**:
   - Ryan → copiază `templates/ryan.SOUL.md` și înlocuiește `<LANGUAGE>`, `<COPYWRITER_USERNAME>`,
     `<CEO_USERNAME>`, `<TOPIC_NAME>` (=Copywriting).
   - Custom → copiază `templates/copywriter.SOUL.md` și înlocuiește `<NAME>`,
     `<CHARACTER_DESCRIPTION>`, `<TONE>`, `<LANGUAGE>` + aceleași username/topic.
   (Copywriter-ul e worker de TEXT — NU copia `gen_image.py` și NU crea `image-studio`.)

## Pas 6 — Skill de delegare CEO → copywriter
În profilul CEO-ului creează `skills/assign-to-<slug>/`:
- `scripts/delegate.py` = copie din `scripts/delegate.py` al acestui skill (suport `--image`).
- `handoff.json` din `templates/handoff.json` cu `<COPYWRITER_USERNAME>`, `<TOPIC_ID>`, `<MAX_ROUNDS>`.
- `SKILL.md` din `templates/assign-to-copywriter.SKILL.md` cu placeholderele înlocuite
  (`<SLUG>`, `<NAME>`, `<VENV_PYTHON>`, `<CEO_PROFILE>`, `<COPYWRITER_USERNAME>`, `<TOPIC_NAME>`, `<LANGUAGE>`, `<MAX_ROUNDS>`).

## Pas 7 — Actualizează CEO-ul (cheie!)
- **`.env` CEO:** adaugă `<TOPIC_ID>` la `TELEGRAM_ALLOWED_TOPICS` (ex. `1,2,<TOPIC_ID>`).
- **`SOUL.md` CEO:** adaugă fluxul **secvențial complet** (în limba echipei), păstrând LOOP GUARD:
  1. prezintă noul membru (nume/rol/topic Copywriting, `@<copywriter>`);
  2. flux: *brief → worker imagini → `assign-to-<slug>` cu **imaginea+brief** (calea din linia
     `MEDIA:`/`LAST_IMAGE:`) → **review copy AUTONOM** (recuperează criteriile cu
     `assign-to-<slug>/scripts/delegate.py --show-brief`, fiindcă topicul Copywriting n-are brief-ul
     din General; fă mereu cel puțin o rundă de rafinare, cere TU îmbunătățiri fără să aștepți omul;
     cap) → **livrează imagine + copy DETERMINIST în General**: rulează `deliver.py` al ARTISTULUI cu
     copy-ul final drept caption (`assign-to-<artist_slug>/scripts/deliver.py --caption "<copy>"`) —
     NU `MEDIA:` în proză (ai fi în topicul greșit) → apoi STOP*;
  3. regula dură: „ca să delegi copy, rulează skill-ul `assign-to-<slug>` cu `--image` (prima
     rundă); NU tasta `@<copywriter>` în proză"; cap **per worker**; workerii nu vorbesc între ei.

## Pas 8 — Înregistrează + repornește + verifică
- Adaugă `<slug>` în **team.json-ul echipei LIVE** (cel găsit la Pas 1).
- `<venv_python> <live_manage.py> fresh` (restart + șterge sesiuni — necesar după persona/SOUL nou).
- Confirmă noul bot „✓ telegram connected", fără erori reale, și **fără** `📬 No home channel`.
- **Test controlat + monitor auto-kill:**
  - Pornește în fundal monitorul:
    `<venv_python> scripts/monitor.py --python <venv_python> --manage <live_manage.py> --profiles <ceo>,<workeri>,<slug> --max-deliveries <cap+2> --window 180`
  - Declanșează un ciclu: rulează `assign-to-<slug>/scripts/delegate.py --reset` apoi cu `--prompt`
    + `--image` (o imagine de test existentă). Verifică în loguri: copywriter-ul primește poza,
    rulează vision, scrie copy (limba corectă), mențiune către CEO; CEO reacționează/livrează;
    fără chatter, fără buclă. Monitorul oprește echipa dacă apar > cap+2 livrări (runaway).
  - Confirmă rezultatul cu userul:

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Cum a mers testul de copy?"
>   opțiuni: ["Merge — copy livrat în General"], ["Nu răspunde"], ["Buclă / chatter / limbă greșită"]

  - DACĂ „Merge": declară succesul. ALTFEL: inspectează loguri + monitor și remediază (gating/handoff/token/vision).
  - La final, `--reset` la contoare și `fresh` pentru start curat.

## Reguli finale
- Copywriter nou = ÎNTOTDEAUNA gated în topicul „Copywriting". Doar CEO-ul e liber.
- Delegare DOAR prin `assign-to-<slug>` (mențiune+thread hardcodate + cap). Secretele doar în `.env` (`chmod 600`), niciodată în doc/git.
- NU atinge profilul `default`, NU modifica gating-ul celorlalți workeri.
- Acest skill adaugă **un singur** copywriter (rol fix: imagine+brief→copy); doar persona/limba diferă.
