---
name: adauga-artist
description: "Adaugă un agent ARTIST (worker care generează imagini cu Google Gemini Nano Banana Pro) peste o echipă Hermes existentă. Default Pam Beesly (The Office) cu fișiere gata-făcute; opțional persona custom (alt nume/caracter). Topologie hub: artistul e gated, raportează DOAR la CEO, fără buclă. Flux: CEO → assign-to-<slug> cu prompt englez → artistul generează imaginea → CEO o livrează în General (și, dacă există un copywriter, poate înlănțui imagine→copy)."
version: 1.0.0
author: silviu
license: Apache-2.0
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Telegram, Agents, Delegation, Image, Gemini, Onboarding]
---

# Adaugă artist (worker de imagini → raportează la CEO)

Adaugă **UN** worker artist peste o echipă existentă (construită cu `reproducere-agenti-office` /
`echipa-boti-hermes` / `adauga-membru-echipa`). Artistul primește un **prompt în engleză** de la
CEO și întoarce o **imagine** (PNG via Gemini Nano Banana Pro), cu revizuiri prin `--edit-from`.
Topologie **hub**: artistul are botul + topicul lui, e **gated**, vorbește DOAR cu CEO-ul. Doar
CEO-ul rămâne liber → fără buclă.

Self-contained: `scripts/` (`delegate.py` text-only config-driven, `gen_image.py`, `deliver.py`
livrare deterministă în General, `manage.py`, `monitor.py`), `templates/` (fișierele exacte ale lui
Pam + skeleton custom + config-changes).

## LECȚII ÎNCORPORATE (de ce skill-ul arată așa) — nu le regresa
1. **Livrarea în General se face DETERMINIST prin `deliver.py`, nu prin `MEDIA:` în proză.** Când
   artistul pune imaginea în topicul Art, CEO-ul e declanșat în sesiunea **Art** și, cu vision
   native, primește doar **pixelii**, NU calea fișierului → nu poate cross-posta `MEDIA:`. `deliver.py`
   ia imaginea aprobată (prin pointer-ul `last_image.txt` scris de `gen_image.py`) și o pune în
   General prin tokenul CEO-ului. Are **lock anti-duplicat** (cele două sesiuni per-topic ale CEO-ului
   pot ajunge amândouă la livrare).
2. **Sesiuni separate per-topic → CEO-ul N-ARE brief-ul în sesiunea Art.** `delegate.py` persistă
   brief-ul rundei 1; CEO-ul rulează `delegate.py --show-brief` la review ca să-și reamintească
   criteriile și să evalueze imaginea pe ele — **autonom, fără să aștepte omul**.
3. **Aspect ratio (1:1 etc.) NU se controlează din textul promptului** la Gemini — `gen_image.py` îl
   setează ca parametru API (`ImageConfig`), auto-detectat din prompt sau via `--aspect`.
4. **Counter-leak între task-uri:** `deliver.py` resetează contorul de runde după livrare → următorul
   brief pornește curat de la ROUND 1.
5. **Mediu cross-platform:** detectează HERMES_HOME real (poate fi `%LOCALAPPDATA%\\hermes` pe Windows,
   nu `~/.hermes`), venv python (`Scripts/python.exe` vs `bin/python`), și instalează `google-genai`
   cu `uv pip` dacă venv-ul e uv-managed (fără `pip`).

## REGULĂ DE INTERACȚIUNE (obligatorie)
**Orice** întrebare către utilizator se pune prin tool-ul **AskUserQuestion**, niciodată text
liber: confirmarea CEO-ului, alegerea persona (Pam vs custom), limba, numele topicului, eventuala
înlănțuire cu un copywriter, confirmarea pașilor Telegram și colectarea token-ului (valori libere
→ opțiunea „Other"). Grupează logic (max 4 per apel), mai multe runde dacă e nevoie.

**Pattern pentru pași fizici (obligatoriu):** când utilizatorul trebuie să facă ceva manual
(BotFather, topic nou), NU trimite la documente externe — **afișează pașii compleți PE ECRAN**
(text neutru, numerotat, cu URL-uri exacte), apoi într-**un singur** apel AskUserQuestion confirmă
că a terminat („Gata, am terminat" / „Am nevoie de ajutor") **și** colectează token-ul (în „Other").
Dacă alege „Am nevoie de ajutor", afișează o variantă mai detaliată și re-întreabă cu ACELAȘI apel.
Valorile pe care le poți obține singur (topic id, group id) le iei TU (rulezi `curl`), nu le ceri userului.

## ANTI-BUCLĂ (regula de aur) — nu o încălca
- Exact UN bot e „liber" (CEO: `TELEGRAM_REQUIRE_MENTION=false`). Artistul e **gated**
  (`TELEGRAM_REQUIRE_MENTION=true`) în topicul lui. `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true` peste tot.
- Delegare CEO→artist **DOAR** prin skill-ul `assign-to-<slug>` (`delegate.py`): mențiune + thread
  hardcodate în `handoff.json` + **cap dur de runde**. CEO-ul NU tastează niciodată
  `@<artist>` în proză.
- NU atinge gating-ul celorlalți workeri. NU atinge profilul `default`.

---

## Pas 0 — Detectează mediul (cross-platform) + dependențe
Înainte de orice, stabilește căile REALE (nu presupune `~/.hermes`):
- **HERMES_HOME:** ia `$HERMES_HOME`/`$env:HERMES_HOME` dacă e setat; altfel `~/.hermes`
  (Linux/macOS) sau `%LOCALAPPDATA%\hermes` (Windows). Toate căile (`profiles/`, `team.json`,
  `cache/`) sunt sub HERMES_HOME. Reține `<HERMES_HOME>`.
- **venv python (`<venv_python>`):** `which hermes` → de obicei venv-ul Hermes e lângă el. Caută
  `<HERMES_HOME>/hermes-agent/venv/Scripts/python.exe` (Windows) sau
  `<HERMES_HOME>/hermes-agent/venv/bin/python` (Linux/macOS). Reține calea ABSOLUTĂ.
- **`<live_manage.py>`:** dacă nu există un `manage.py` live persistent, copiază
  `scripts/manage.py` + `scripts/monitor.py` în `<HERMES_HOME>/` (lângă `team.json`) și folosește-le
  de acolo (citesc `team.json` din HERMES_HOME).
- **Dependențe Python în venv:** `gen_image.py` are nevoie de `google-genai`. Testează:
  `<venv_python> -c "from google import genai"`. Dacă lipsește, instalează-l TU:
  - venv uv-managed (fără pip): `<uv> pip install --python <venv_python> google-genai`
    (uv e de obicei `<HERMES_HOME>/bin/uv` sau pe PATH).
  - venv clasic: `<venv_python> -m pip install google-genai`.
  Reconfirmă importul. (`psutil` e folosit de `manage.py` — verifică-l la fel, instalează dacă lipsește.)

## Pas 1 — Inspectează echipa existentă
- **team.json LIVE** = `~/.hermes/team.json` (HERMES_HOME) — manifestul **canonic** al echipei,
  ținut în HERMES_HOME ca să rămână editabil și când skill-ul rulează dintr-un cache de plugin
  read-only. `manage.py` îl citește de acolo (fallback: seed-ul bundled de lângă `scripts/`, apoi
  env `HERMES_TEAM_PROFILES`). Pe ACELA îl actualizezi (`profiles`/`watchers`) și repornești echipa.
- Identifică **CEO-ul** = profilul cu `TELEGRAM_REQUIRE_MENTION=false`:
  `grep -l 'TELEGRAM_REQUIRE_MENTION=false' ~/.hermes/profiles/*/.env`. **Confirmă prin AskUserQuestion.**
- Din `.env`-ul CEO-ului citește `TELEGRAM_GROUP_ALLOWED_CHATS` (group id) și
  `TELEGRAM_ALLOWED_TOPICS` (topicuri actuale).
- **Există deja un copywriter?** Caută în profilul CEO-ului un skill `assign-to-*` al cărui worker
  e copywriter (text). Dacă da, reține-l — la Pas 7 întrebi dacă înlănțui imagine→copy.

## Pas 2 — Alege persona (prin AskUserQuestion)
Întreabă într-un apel (max 4):

> APELEAZĂ AskUserQuestion (exemplu literal — copiază, adaptează):
> Î1 — „Ce personaj vrei pentru artist?"   opțiuni: ["Pam Beesly (The Office)"], ["Alt personaj (custom)"]
> Î2 — „În ce limbă vorbește artistul?"    opțiuni: ["Ca echipa"], ["Română"], ["Engleză"]   (alta → „Other")
> Î3 — „Cum se numește topicul lui?"        opțiuni: ["Art (recomandat)"]   (alt nume → „Other")
> Î4 — „Câte runde maxim CEO↔artist?"       opțiuni: ["3 (recomandat)"]     (alt număr → „Other")

- Dacă a ales **custom**, fă o a doua rundă AUQ: **numele**, **slug-ul** (lowercase), **descrierea
  caracterului/tonului** (în „Other"). Dacă **Pam**: slug implicit `pam`, persona din `templates/pam.SOUL.md`.
- **Model imagini**: default `gemini-3-pro-image` (configurabil prin `GEN_IMAGE_MODEL` în `.env`; întreabă doar dacă userul ridică subiectul).
- ⚠️ Indiferent de limbă, **prompturile de imagine rămân în ENGLEZĂ** (calitate); textul în altă
  limbă pe imagine se pune între ghilimele duble în prompt.

## Pas 3 — PAUZĂ: pașii Telegram pentru botul nou

> AFIȘEAZĂ userului (text neutru, pas-cu-pas) — înlocuiește „<TOPIC_NAME>" cu topicul ales (default „Art"):
> ─────────────────────────────────────────────────────────────
> Hai să creăm botul de Telegram pentru artist. Durează ~3 minute.
>
> A. Creează botul în BotFather
>   1. Deschide Telegram și scrie către BotFather: https://t.me/BotFather (bifă albastră).
>   2. Trimite comanda:  /newbot
>   3. Dă-i un nume afișat (ex. „Pam Beesly").
>   4. Dă-i un username care se TERMINĂ obligatoriu în „bot" (ex. pam_beesly_art_bot).
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
>  12. Intră în „<TOPIC_NAME>" și scrie un mesaj care MENȚIONEAZĂ botul, ex.: @pam_beesly_art_bot salut
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
>   - Topicurile apar ca file/categorii sus în grup; „+" e la capătul listei.
>   - Mențiunea (@…_bot) e obligatorie în mesajul de test, altfel nu pot citi id-ul topicului cu privacy on.

> DUPĂ confirmare (NU afișa comenzile userului):
>   - Verifică tu token-ul cu `getMe` → reține `username`-ul real al artistului.

## Pas 4 — Ia topic id-ul nou (Claude rulează singur — userul NU rulează curl)
Oprește gateway-urile (`<venv_python> <live_manage.py> stop`). Rulează TU `getUpdates` cu **tokenul
noului bot**: `curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"` → extrage `message_thread_id`
al mesajului din topicul nou = `<TOPIC_ID>`. NU afișa comanda userului. Reține `<TOPIC_ID>` și `<GROUP_ID>`.

## Pas 5 — Creează profilul artistului
1. `hermes profile create <slug> --clone --description "<rol>"`.
2. **config.yaml** — urmează `templates/config-changes.md`: copiază config-ul unui worker gated
   existent SAU al CEO-ului peste cel clonat (anti-chatter + modelul creier al echipei +
   `restart_drain_timeout: 20`), apoi **`kanban.dispatch_in_gateway: false`** și menține gated.
3. **.env** din `templates/artist.env` — completează `<GEMINI_KEY>` (din `.env`-ul unui profil
   existent — NU inventa), `<TOKEN>`, `<GROUP_ID>`, `<TOPIC_ID>`, `<TOPIC_NAME>`; păstrează cele 3
   chei anti-chatter; (opțional `GEN_IMAGE_MODEL`). `chmod 600`.
4. **image-studio skill**: creează `skills/image-studio/` în profilul artistului:
   - `scripts/gen_image.py` = copie din `scripts/gen_image.py` al acestui skill.
   - `SKILL.md` din `templates/image-studio.SKILL.md` cu `<VENV_PYTHON>`, `<ARTIST_PROFILE>` înlocuite.
5. **SOUL.md**:
   - Pam → `templates/pam.SOUL.md`, înlocuiește `<LANGUAGE>`, `<ARTIST_USERNAME>`,
     `<CEO_USERNAME>`, `<TOPIC_NAME>`, `<VENV_PYTHON>`, `<ARTIST_PROFILE>`.
   - Custom → `templates/artist.SOUL.md`, înlocuiește și `<NAME>`, `<CHARACTER_DESCRIPTION>`, `<TONE>`.

## Pas 6 — Skill de delegare + livrare CEO → artist
În profilul CEO-ului creează `skills/assign-to-<slug>/scripts/` cu:
- `delegate.py` = copie din `scripts/delegate.py` al acestui skill (text-only, config-driven).
- `deliver.py` = copie din `scripts/deliver.py` al acestui skill (livrare deterministă în General).
- **`handoff.json` (LÂNGĂ delegate.py, în `scripts/`)** din `templates/handoff.json` cu
  `<ARTIST_USERNAME>`, `<TOPIC_ID>`, `<MAX_ROUNDS>`. ⚠️ `delegate.py` îl citește din `scripts/` —
  NU îl pune în rădăcina skill-ului.
- **`deliver.json` (în `scripts/`)** din `templates/deliver.json`:
  - `artist_images_dir` = `<HERMES_HOME>/profiles/<slug>/cache/images` (de unde `gen_image.py`
    scrie imaginile + pointer-ul `last_image.txt`).
  - `worker_mention` = `@<ARTIST_USERNAME>` (ca `deliver.py` să reseteze contorul corect după livrare).
  - `general_thread_id` = `""` (General = fără thread).
- `SKILL.md` din `templates/assign-to-artist.SKILL.md` cu placeholderele înlocuite
  (`<SLUG>`, `<NAME>`, `<VENV_PYTHON>`, `<CEO_PROFILE>`, `<ARTIST_USERNAME>`, `<TOPIC_NAME>`, `<MAX_ROUNDS>`).

## Pas 7 — Actualizează CEO-ul (cheie!)
- **`.env` CEO:** adaugă `<TOPIC_ID>` la `TELEGRAM_ALLOWED_TOPICS`.
- **`SOUL.md` CEO — fluxul de imagine** (în limba echipei), păstrând LOOP GUARD. Scrie un flux EXACT
  ca acesta (adaptează căile/numele), fiindcă fiecare pas rezolvă o capcană reală:
  1. **Prezintă** noul membru (nume/rol/topic, `@<artist>`). Subliniază: General = vorbești cu omul;
     Art = atelierul privat cu artistul. Le ții SEPARATE.
  2. **CLARIFY (General):** la o cerere de imagine, pune 1–2 întrebări scurte — inclusiv **FORMATUL**
     (post 1:1 / story 9:16 / banner 16:9), dacă omul nu l-a spus. Întreabă o singură dată.
  3. **BRIEF + CRITERII (General):** spune-i omului că te ocupi; fixează-ți 2–4 criterii concrete
     (subiect, stil, atmosferă/culori, **format/aspect**, text exact dacă e cerut).
  4. **DELEAGĂ (Art):** rulează `assign-to-<slug>/scripts/delegate.py --prompt "<prompt ENGLEZ>"`.
     Include formatul în prompt (ex. „..., 1:1 aspect ratio"). Skill-ul postează mențiunea + ROUND n.
     Tu NU scrii `@<artist>` în proză.
  5. **REVIEW CRITIC — TU singur, NU aștepta omul:** când apare imaginea în Art:
     - rulează ÎNTÂI `delegate.py --show-brief` (sesiunea Art **n-are** brief-ul din General → așa îți
       reamintești criteriile);
     - bifează imaginea pe FIECARE criteriu (inclusiv aspect, text, proporții, calitate);
     - **fă mereu cel puțin o rundă de rafinare**: dacă ceva poate fi mai bun → `delegate.py --prompt
       "<feedback ENGLEZ concret>"` (skill-ul avansează runda, artistul editează cu `--edit-from`).
       Dacă imaginea e deja clar excelentă, poți livra. Continuă până e bună sau până la `CAP_REACHED`.
  6. **LIVREAZĂ în General — DETERMINIST:** când imaginea e aprobată (sau la `CAP_REACHED`), NU o
     re-posta în Art și NU folosi `MEDIA:` (n-ai calea). Rulează:
     `assign-to-<slug>/scripts/deliver.py --caption "<legendă scurtă, în limba echipei>"`.
     Scriptul ia imaginea aprobată (pointer `last_image.txt`), o pune în General, resetează contorul.
     Apoi **STOP** — nu mai posta nimic.
  7. **Regula dură (LOOP GUARD):** ca să delegi/dai feedback, rulează `delegate.py`; NU tasta
     `@<artist>` în proză. Cap **per worker**; workerii nu vorbesc între ei.
- **Înlănțuire cu copywriter (dacă există — Pas 1):** întreabă prin AskUserQuestion:

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Am găsit un copywriter în echipă. Înlănțuiesc imagine→copy (CEO trimite imaginea la copywriter înainte de livrare)?"
>   opțiuni: ["Da, înlănțuie"], ["Nu, doar imaginea"]

  Dacă DA, în SOUL-ul CEO, după ce imaginea e bună, **înainte** de livrare:
  *trimite imaginea + brief-ul la copywriter prin `assign-to-<copywriter_slug>` cu `--image <calea
  MEDIA:>` → review copy → livrează **imagine + copy** în General*. Dacă NU, livrează doar imaginea.

## Pas 8 — Înregistrează + repornește + verifică
- Adaugă `<slug>` în **team.json-ul echipei LIVE** (Pas 1).
- `<venv_python> <live_manage.py> fresh` (restart + șterge sesiuni — necesar după persona/SOUL nou).
- Confirmă „✓ telegram connected", fără erori reale, **fără** `📬 No home channel`.
- **Test controlat + monitor auto-kill:**
  - Pornește monitorul în fundal:
    `<venv_python> scripts/monitor.py --python <venv_python> --manage <live_manage.py> --profiles <ceo>,<workeri>,<slug> --max-deliveries <cap+2> --window 180`
  - Declanșează: `assign-to-<slug>/scripts/delegate.py --reset` apoi cu `--prompt "<prompt englez de
    test, cu un format clar ex. 1:1>"`. Verifică în loguri: artistul generează o imagine (`ASPECT:`
    corect + `MEDIA:`), o postează cu mențiune către CEO; CEO o vede (vision), rulează `--show-brief`,
    face **cel puțin o rundă de feedback autonom** (ROUND 2 fără mesaj uman între), apoi livrează în
    **General** prin `deliver.py`; fără chatter, fără buclă. Monitorul (citește HERMES_HOME) oprește
    echipa la runaway (> cap+2 livrări). `deliver.py` resetează singur contorul după livrare.
  - Confirmă rezultatul cu userul:

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Cum a mers testul de imagine?"
>   opțiuni: ["Merge — imagine livrată în General"], ["Nu răspunde"], ["Buclă / chatter / topic greșit"]

  - DACĂ „Merge": declară succesul. ALTFEL: inspectează loguri + monitor și remediază (gating/handoff/token/vision).
  - La final, `--reset` la contoare și `fresh` pentru start curat.

## Reguli finale
- Artist nou = ÎNTOTDEAUNA gated în topicul lui. Doar CEO-ul e liber.
- Delegare DOAR prin `assign-to-<slug>` (mențiune+thread hardcodate + cap). Prompturile de imagine în ENGLEZĂ.
- Secretele doar în `.env` (`chmod 600`), niciodată în doc/git. NU atinge profilul `default`, NU modifica gating-ul altora.
- Acest skill adaugă **un singur** artist (rol fix: prompt→imagine); doar persona/limba diferă.
