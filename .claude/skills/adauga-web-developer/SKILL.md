---
name: adauga-web-developer
description: "Adaugă un agent WEB DEVELOPER (worker care primește 2-3 imagini + copy-ul paginii și construiește un index.html self-contained) peste o echipă Hermes existentă. Default Dwight Schrute (The Office) cu fișiere gata-făcute; opțional persona custom. Topologie hub: dev-ul e gated, raportează DOAR la CEO, fără buclă. Lanț: CEO → artist (2-3 imagini) → copywriter (copy pagină) → dev (HTML) → CEO împachetează un .zip (index.html + imagini) și-l livrează în General. Wire-uiește lanțul peste artistul + copywriter-ul existenți (le actualizează SOUL-ul; upgrade multi-imagine la delegarea copywriter-ului)."
version: 1.0.0
author: silviu
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Telegram, Agents, Delegation, WebDev, Landing, Onboarding]
---

# Adaugă web developer (worker HTML → raportează la CEO)

Adaugă **UN** worker web developer peste o echipă existentă (construită cu `adauga-ceo` +
`adauga-artist` + `adauga-copywriter`, sau `reproducere-agenti-office` / `echipa-boti-hermes`).
Dev-ul primește **2-3 imagini** (de la artist) + **copy-ul paginii** (de la copywriter) + brief-ul
și întoarce **un singur `index.html` self-contained** (CSS inline, fără CDN, imagini prin basename).
CEO-ul împachetează `index.html` + imaginile într-un **`.zip`** și-l livrează omului în General.
Topologie **hub**: dev-ul are botul + topicul lui, e **gated**, vorbește DOAR cu CEO-ul. Doar
CEO-ul rămâne liber → fără buclă.

Self-contained: `scripts/` (`delegate.py` cu job dir + spec + album multi-imagine, `package.py`
zip idempotent, `manage.py`, `monitor.py`), `templates/` (Dwight gata-făcut + skeleton custom +
`assign-to-webdev.SKILL.md` + `package-landing.SKILL.md` + env + handoff + config-changes +
**snippet-uri de injectat** în SOUL-urile CEO/copywriter/artist + nota de upgrade multi-imagine).

## REGULĂ DE INTERACȚIUNE (obligatorie)
**Orice** întrebare către utilizator se pune prin tool-ul **AskUserQuestion**, niciodată text
liber: confirmarea CEO-ului, alegerea persona (Dwight vs custom), limba, numele topicului, ce
artist/copywriter intră în lanț, sursa copy-ului, nr. de imagini, cap-ul de runde, confirmarea
pașilor Telegram și colectarea token-ului (valori libere → opțiunea „Other"). Max 4 per apel.

**Pattern pentru pași fizici (obligatoriu):** când utilizatorul trebuie să facă ceva manual
(BotFather, topic nou), NU trimite la documente externe — **afișează pașii compleți PE ECRAN**
(text neutru, numerotat, cu URL-uri exacte), apoi într-**un singur** apel AskUserQuestion confirmă
că a terminat („Gata, am terminat" / „Am nevoie de ajutor") **și** colectează token-ul (în „Other").
Dacă alege „Am nevoie de ajutor", afișează o variantă mai detaliată și re-întreabă cu ACELAȘI apel.
Valorile pe care le poți obține singur (topic id, group id) le iei TU (rulezi `curl`), nu le ceri userului.

## ANTI-BUCLĂ (regula de aur) — nu o încălca
- Exact UN bot e „liber" (CEO: `TELEGRAM_REQUIRE_MENTION=false`). Dev-ul e **gated**
  (`TELEGRAM_REQUIRE_MENTION=true`) în topicul lui. `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true` peste tot.
- Delegare CEO→dev **DOAR** prin `assign-to-<slug>` (`delegate.py`): mențiune + thread hardcodate în
  `handoff.json` + **cap dur de runde**. CEO-ul NU tastează niciodată `@<dev>` în proză.
- NU atinge gating-ul celorlalți workeri. NU atinge profilul `default`.

---

## Pas 1 — Inspectează echipa existentă
- Găsește **team.json-ul echipei LIVE** (folosit de gateway-urile care rulează), în ordine: lângă
  `adauga-ceo/scripts/` (fundația — sursa canonică), apoi `reproducere-agenti-office/scripts/`, apoi
  `echipa-boti-hermes`, apoi `adauga-membru-echipa/scripts/`. Reține calea lui + a `manage.py`-ului
  de lângă el — pe ACELA îl actualizezi și repornești (copia proprie din `scripts/` e fallback).
- Identifică **CEO-ul** = profilul cu `TELEGRAM_REQUIRE_MENTION=false`:
  `grep -l 'TELEGRAM_REQUIRE_MENTION=false' ~/.hermes/profiles/*/.env`. **Confirmă prin AskUserQuestion.**
- Din `.env`-ul CEO-ului citește `TELEGRAM_GROUP_ALLOWED_CHATS` (group id) și
  `TELEGRAM_ALLOWED_TOPICS` (topicuri actuale).
- **Detectează upstream:** în profilul CEO caută skill-urile `assign-to-*`. Identifică **artistul**
  (worker cu `image-studio`/`gen_image.py`) și **copywriter-ul** (worker text). Reține slug-urile +
  username-urile lor — la Pas 7 wire-uiești lanțul cu ei.
- **Lipsă upstream:** dacă NU există artist și/sau copywriter, avertizează (degradare elegantă):

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Lipsește {artist/copywriter} din echipă. Instalez dev-ul oricum? Va lucra pe imagini/copy trimise direct de CEO (sau, fără copywriter, își scrie singur copy-ul din brief)."
>   opțiuni: ["Da, instalează dev-ul"], ["Nu, mă opresc"]

  Continuă doar dacă a ales „Da".

## Pas 2 — Alege persona & parametrii (prin AskUserQuestion)
Sunt >4 valori → fă **2 runde** AUQ:

> APELEAZĂ AskUserQuestion — Runda 1 (exemplu literal):
> Î1 — „Ce personaj vrei pentru web developer?"  opțiuni: ["Dwight Schrute (The Office)"], ["Alt personaj (custom)"]
> Î2 — „În ce limbă vorbește dev-ul?"             opțiuni: ["Ca echipa"], ["Română"], ["Engleză"]   (alta → „Other")
> Î3 — „Cum se numește topicul lui?"               opțiuni: ["Dezvoltare Web (recomandat)"]   (alt nume → „Other")
> Î4 — „Câte runde maxim CEO↔dev?"                 opțiuni: ["3 (recomandat)"]   (alt număr → „Other")

> APELEAZĂ AskUserQuestion — Runda 2 (exemplu literal):
> Î1 — „Câte imagini pe pagină?"     opțiuni: ["2-3, CEO decide după brief (recomandat)"]   (număr fix → „Other")
> Î2 — „De unde vine copy-ul paginii?"  opțiuni: ["Prin copywriter (dacă există)"], ["Dev-ul scrie singur copy + HTML"]
> (Dacă a ales custom la Runda 1: adaugă întrebări pentru nume + slug + descriere caracter → „Other".)

- Dacă **Dwight**: slug implicit `dwight`, persona din `templates/dwight.SOUL.md`.
- **Model creier**: implicit modelul echipei (ex. `gemini-3.5-flash`, detectat dintr-un worker; întreabă doar dacă userul ridică subiectul).
- ⚠️ Indiferent de limbă, **codul (HTML/CSS) rămâne în engleză**; conținutul paginii e în limba brief-ului.

## Pas 3 — PAUZĂ: pașii Telegram pentru botul nou

> AFIȘEAZĂ userului (text neutru, pas-cu-pas) — înlocuiește „<TOPIC_NAME>" cu topicul ales (default „Dezvoltare Web"):
> ─────────────────────────────────────────────────────────────
> Hai să creăm botul de Telegram pentru web developer. Durează ~3 minute.
>
> A. Creează botul în BotFather
>   1. Deschide Telegram și scrie către BotFather: https://t.me/BotFather (bifă albastră).
>   2. Trimite comanda:  /newbot
>   3. Dă-i un nume afișat (ex. „Dwight Schrute").
>   4. Dă-i un username care se TERMINĂ obligatoriu în „bot" (ex. dwight_webdev_bot).
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
>  12. Intră în „<TOPIC_NAME>" și scrie un mesaj care MENȚIONEAZĂ botul, ex.: @dwight_webdev_bot salut
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
>   - Verifică tu token-ul cu `getMe` → reține `username`-ul real al dev-ului.

## Pas 4 — Ia topic id-ul nou (Claude rulează singur — userul NU rulează curl)
Oprește gateway-urile (`<venv_python> <live_manage.py> stop`). Rulează TU `getUpdates` cu **tokenul
noului bot**: `curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"` → extrage `message_thread_id`
al mesajului din topicul nou = `<TOPIC_ID>`. NU afișa comanda userului. **Dacă privacy e on și
buffer-ul e gol**, încearcă tu cu tokenul CEO-ului (citește tot). Dacă tot nu apare, cere userului să mai posteze:

> APELEAZĂ AskUserQuestion (exemplu literal — doar dacă nu poți citi id-ul singur):
> Întrebarea 1 — „Mai scrie te rog un mesaj în topicul nou care menționează botul (ex. @username_bot salut), apoi confirmă."
>   opțiuni: ["Gata, am scris"], ["Am nevoie de ajutor"]

Reține `<TOPIC_ID>` și `<GROUP_ID>`.

## Pas 5 — Creează profilul dev-ului
1. `hermes profile create <slug> --clone --description "<rol>"`.
2. **config.yaml** — urmează `templates/config-changes.md`: copiază config-ul unui worker gated
   existent SAU al CEO-ului (anti-chatter + modelul creier al echipei + `restart_drain_timeout: 20`),
   apoi **`kanban.dispatch_in_gateway: false`** și menține gated. (Dev-ul e worker de TEXT/cod — NU
   copia `gen_image.py`, NU crea `image-studio`; păstrează tool-urile de fișiere din `hermes-cli`.)
3. **.env** din `templates/webdev.env` — completează `<GEMINI_KEY>` (din `.env`-ul unui profil
   existent — NU inventa), `<TOKEN>`, `<GROUP_ID>`, `<TOPIC_ID>`, `<TOPIC_NAME>`; păstrează cele 3
   chei anti-chatter (`TELEGRAM_HOME_CHANNEL`, `..._NAME=<TOPIC_NAME>`, `..._CRON_THREAD_ID=<TOPIC_ID>`).
   `chmod 600`.
4. **SOUL.md**:
   - Dwight → `templates/dwight.SOUL.md`, înlocuiește `<LANGUAGE>`, `<DEV_USERNAME>`, `<CEO_USERNAME>`,
     `<TOPIC_NAME>`.
   - Custom → `templates/web-developer.SOUL.md`, înlocuiește și `<NAME>`, `<CHARACTER_DESCRIPTION>`, `<TONE>`.
   - Dacă **dev-ul scrie singur copy-ul** (fără copywriter): adaugă în SOUL o notă că, atunci când
     spec-ul nu conține „page copy", scrie el textul paginii din brief + imagini.

## Pas 6 — Skill-uri în profilul CEO-ului
**a) `skills/assign-to-<slug>/`** (delegare CEO → dev):
- `scripts/delegate.py` = copie din `scripts/delegate.py` al acestui skill (job dir + spec + album).
- `handoff.json` din `templates/handoff.json` cu `<DEV_USERNAME>`, `<TOPIC_ID>`, `<MAX_ROUNDS>`.
- `SKILL.md` din `templates/assign-to-webdev.SKILL.md` cu placeholderele înlocuite (`<SLUG>`,
  `<NAME>`, `<VENV_PYTHON>`, `<CEO_PROFILE>`, `<DEV_USERNAME>`, `<TOPIC_NAME>`, `<LANGUAGE>`, `<MAX_ROUNDS>`).

**b) `skills/package-landing/`** (împachetare zip — livrare):
- `scripts/package.py` = copie din `scripts/package.py` al acestui skill (zip idempotent).
- `SKILL.md` din `templates/package-landing.SKILL.md` cu `<VENV_PYTHON>`, `<CEO_PROFILE>`, `<SLUG>` înlocuite.

## Pas 7 — Actualizează CEO-ul + wire-uiește lanțul (cheie!)
- **`.env` CEO:** adaugă `<TOPIC_ID>` la `TELEGRAM_ALLOWED_TOPICS`.
- **`SOUL.md` CEO:** injectează blocurile din `templates/ceo-soul-additions.md` (în limba echipei),
  MERGE în secțiunile existente (team, topicuri, LOOP GUARD) — nu duplica. Conțin: noul membru,
  topicul, cum delegi prin `assign-to-<slug>`, cum faci zip-ul cu `package-landing`, workflow-ul de
  landing complet (artist→copywriter→dev→zip), și extinderea LOOP GUARD cu noul handle.
- **Wire-uirea lanțului.** Dacă sunt MAI MULȚI artiști/copywriteri, întreabă care intră în lanț:

> APELEAZĂ AskUserQuestion (exemplu literal — doar dacă există >1 candidat):
> Î1 — „Care artist intră în lanțul de landing?"      opțiuni: [listează slug-urile găsite]
> Î2 — „Care copywriter intră în lanțul de landing?"  opțiuni: [listează slug-urile găsite]

  Apoi:
  - **Copywriter (dacă în lanț):** injectează `templates/copywriter-soul-additions.md` în SOUL-ul
    copywriter-ului (modul „copy de pagină"); și **upgrade la multi-imagine** al delegării
    copywriter-ului urmând `templates/copywriter-delegate-multiimage.md` (backward-compatible).
  - **Artist (dacă în lanț):** injectează `templates/artist-soul-additions.md` în SOUL-ul artistului
    (modul „set de 2-3 imagini").
  - **Lipsă upstream:** sari peste injecțiile lipsă; în SOUL-ul CEO notează că imaginile/copy-ul vin
    direct de la CEO (sau dev-ul scrie copy-ul), restul fluxului identic.

## Pas 8 — Înregistrează + repornește + verifică
- Adaugă `<slug>` în **team.json-ul echipei LIVE** (Pas 1).
- `<venv_python> <live_manage.py> fresh` (restart + șterge sesiuni — necesar după persona/SOUL nou).
- Confirmă „✓ telegram connected" (și pentru workerii cu SOUL modificat), fără erori reale, **fără**
  `📬 No home channel`. Gating: exact UN bot liber (CEO), restul gated.
- **Test controlat + monitor auto-kill:**
  - Pornește monitorul în fundal:
    `<venv_python> scripts/monitor.py --python <venv_python> --manage <live_manage.py> --profiles <ceo>,<artist>,<copywriter>,<slug> --max-deliveries <cap+2> --window 240`
  - Declanșează: cere CEO-ului în General o pagină de landing (temă + brief). Verifică în loguri (sau
    prin fișiere): artistul livrează 2-3 imagini (`MEDIA:`), copywriter-ul scrie copy de pagină, dev-ul
    primește album + spec și scrie `index.html` (`HTML:<cale>`), CEO rulează `package-landing` și
    livrează `MEDIA:<zip>` în General. Confirmă: zip conține index.html + imagini, HTML referă
    imaginile prin basename, fără chatter, fără buclă. Monitorul oprește echipa la runaway.
  - Confirmă rezultatul cu userul:

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Cum a mers testul de landing?"
>   opțiuni: ["Merge — .zip livrat în General"], ["Nu răspunde"], ["Buclă / chatter / lipsesc imagini sau copy"]

  - DACĂ „Merge": declară succesul. ALTFEL: inspectează loguri + monitor și remediază (lanț/gating/handoff/token).
  - La final, `--reset` la contoarele de handoff și `fresh` pentru start curat.

## Reguli finale
- Web developer nou = ÎNTOTDEAUNA gated în topicul lui. Doar CEO-ul e liber.
- Delegare DOAR prin `assign-to-<slug>` (mențiune+thread hardcodate + cap). Codul rămâne în engleză.
- Secretele doar în `.env` (`chmod 600`), niciodată în doc/git. NU atinge profilul `default`; nu
  schimba gating-ul altor workeri (doar SOUL-ul lor + delegarea multi-imagine a copywriter-ului).
- Acest skill adaugă **un singur** web developer (rol fix: imagini+copy→HTML→zip); persona/limba/
  topic/cap/nr-imagini diferă. E **Pas 4** în lanțul standard (după ceo→artist→copywriter).
