---
name: adauga-copywriter
description: "Adaugă un agent COPYWRITER (worker text care primește imagine+brief și scrie textul de reclamă) peste o echipă Hermes existentă. Default Ryan Howard (The Office) cu fișiere gata-făcute; opțional persona custom (alt nume/caracter). Topologie hub: copywriter-ul e gated, raportează DOAR la CEO, fără buclă. Necesită un worker de imagini (artist). Wire-uiește lanțul AUTOMAT: CEO recunoaște o cerere de reclamă → artist (imagine) → copywriter (imagine+brief) → CEO livrează imagine+copy în General — fără ca omul să ceară explicit copy."
version: 1.0.2
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

Self-contained: `scripts/` (`delegate.py` cu suport `--image`, `manage.py`, `monitor.py`,
`patch_artist_delegate.py`), `templates/` (fișierele exacte ale lui Ryan + skeleton custom +
config-changes).

## CE FACE AUTOMAT (lecțiile de azi, baked-in) — nu re-depana
Acest skill nu doar adaugă botul copywriter; **wire-uiește lanțul imagine→copy ca să meargă
AUTONOM**, fără ca omul să ceară explicit „și scrie-mi un text":
1. **Decizie autonomă în CEO (PASUL 0 în SOUL):** când omul cere o **reclamă / poster / ad / anunț
   / banner / campanie / post de Facebook-Instagram**, CEO-ul tratează cererea implicit ca
   **IMAGINE + COPY** (nu doar imagine). Doar un vizual simplu fără text rămâne „doar imagine".
2. **Semnal cross-session prin `--note` (NEEDS_COPY):** CEO-ul decide în sesiunea General, dar
   aprobă imaginea în sesiunea Art (SEPARATĂ, fără brief-ul din General). De aceea la delegarea
   către artist atașează `--note "NEEDS_COPY — brief copy (RO): ..."`, care se **stochează în brief**
   (recuperabil cu `--show-brief`) dar **NU se trimite artistului** (n-o desenează). Patch-ul
   `patch_artist_delegate.py` adaugă acest `--note` (+ citire robustă a tokenului) în `delegate.py`
   al artistului, idempotent.
3. **Livrare condiționată:** dacă brief-ul conține `NEEDS_COPY`, CEO-ul **NU livrează imaginea
   goală**; ia calea imaginii din pointerul artistului (`last_image.txt`), deleagă copy-ul lui Ryan,
   apoi livrează O SINGURĂ DATĂ în General imaginea **cu copy-ul în caption**.
4. **Test în 2 trepte:** mecanic (delegare directă) **+** autonom (omul trimite o cerere reală de
   reclamă, tu monitorizezi tot lanțul și confirmi că copywriter-ul VEDE imaginea înainte să scrie).

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

## Pas 0 — Există deja un copywriter? (idempotență)
Verifică dacă echipa are deja un copywriter (un profil gated cu topic „Copywriting" sau un skill
`assign-to-*` al CEO-ului care țintește un copywriter). Dacă DA:

> APELEAZĂ AskUserQuestion:
> Î1 — „Există deja un copywriter (`<slug>`). Ce facem?"
>   opțiuni: ["Re-aplică doar patch-urile (SOUL + --note)"], ["Adaugă unul nou (alt slug)"], ["Ies"]

- „Re-aplică patch-urile" → sari peste crearea botului/profilului; mergi direct la Pas 6.5 (patch
  artist) + Pas 7 (SOUL CEO) + Pas 8 (test). Toate sunt idempotente.
- „Adaugă unul nou" → continuă normal cu un slug diferit.

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
- **Worker de imagini (artist) — OBLIGATORIU.** Lanțul imagine→copy are nevoie de un worker care
  produce imagini. Identifică candidații: profiluri gated al căror skill `assign-to-*` din profilul
  CEO-ului are **`deliver.py`** și un pointer **`cache/images/last_image.txt`** (sau skill
  `image-studio` / `gen_image.py`). Reține pentru artistul ales:
  - `<ARTIST_SLUG>` și calea `assign-to-<ARTIST_SLUG>/scripts/delegate.py` (ținta patch-ului);
  - calea `assign-to-<ARTIST_SLUG>/scripts/deliver.py` (livrarea imagine+caption);
  - `<ARTIST_IMAGES_DIR>` din `deliver.json` (unde e `last_image.txt`).

  **Confirmă/alege artistul prin AskUserQuestion** (chiar dacă pare evident un singur candidat):

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Care worker e artistul (sursa imaginilor pentru copy)?"
>   opțiuni: [<candidat_1>], [<candidat_2>], ... (dacă e unul singur, tot confirmă-l)

  **Dacă NU există niciun worker de imagini → OPREȘTE-TE** (lanțul automat depinde de el):

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Nu am găsit un worker de imagini. Copywriter-ul are nevoie de un artist (rulează întâi skill-ul adauga-artist). Ce facem?"
>   opțiuni: ["Mă opresc (adaug întâi artistul)"], ["Continuă oricum (copy-only, fără lanț automat)"]

  Implicit oprește-te; continuă DOAR dacă utilizatorul alege explicit „Continuă oricum".

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

## Pas 6.5 — Patch artistul (ca lanțul să meargă AUTONOM)
`delegate.py` al artistului (din `adauga-artist`) NU are `--note` și citește tokenul doar din
`HERMES_HOME/.env` (fragil). Rulează patcher-ul idempotent al acestui skill pe `delegate.py` al
artistului (calea reținută la Pas 1):

```bash
<venv_python> <acest_skill>/scripts/patch_artist_delegate.py \
  <CEO_PROFILE>/skills/assign-to-<ARTIST_SLUG>/scripts/delegate.py
```

- Adaugă `--note` (stocat în brief, recuperabil cu `--show-brief`, NU trimis artistului) + citire
  robustă a tokenului (`PROFILE_DIR/.env` apoi `HERMES_HOME/.env`).
- **Idempotent:** dacă e deja patch-uit → `ALREADY_PATCHED` (nicio schimbare). Validează că noul
  fișier compilează înainte să-l scrie.
- Dacă printează `ERROR: could not find ... anchor` (un `delegate.py` foarte diferit) → aplică
  manual cele 2 modificări (vezi comentariile din patcher) și NU continua orbește.

## Pas 7 — Actualizează CEO-ul (cheie! — aici trăiește decizia autonomă)
- **`.env` CEO:** adaugă `<TOPIC_ID>` la `TELEGRAM_ALLOWED_TOPICS` (ex. `1,2,<TOPIC_ID>`).
- **`SOUL.md` CEO — RESTRUCTUREAZĂ, nu doar adăuga.** Editarea trebuie să fie robustă: ancorează pe
  titlurile fluxului de imagine scris de `adauga-artist` („Cum lucrezi cu Pam/<artist>", pasul de
  livrare); dacă tiparul lipsește, **rescrie coerent întreaga secțiune de workflow ad**. Inserează,
  în limba echipei:

  **(a) Prezintă membrul nou** în „Your team": `<NAME>` — copywriter (`@<copywriter>`), topic
  „Copywriting", scrie textul de reclamă (headline/body/CTA) din imagine + brief; e SINGURUL om de
  copy; nu face imagini; vorbește DOAR cu CEO-ul.

  **(b) PASUL 0 — poartă de decizie (bloc proeminent, ÎNAINTEA fluxului de imagine):**
  - Cuvinte ca **reclamă / ad / advertising / poster / anunț / campanie / banner / promo / post de
    Facebook-Instagram** — sau cerere explicită de **text / slogan / headline / CTA / copy** →
    cererea e **„IMAGINE + COPY"** (implicit pentru reclame; în dubiu, presupune că vrea copy).
  - Doar un vizual simplu fără text de vânzare („o ilustrație cu…", „un desen", „o poză cu…") →
    **„DOAR IMAGINE"**.
  - **CEO-ul decide ce text merge PE imagine vs. ce duce Ryan:** dacă vrea text overlay pe imagine,
    îl pune în promptul (englez) al artistului; copy-ul de post/caption (RO) îl scrie Ryan.

  **(c) La delegarea către artist (runda 1), dacă e „IMAGINE + COPY": atașează `--note`** —
  reaminteșe-ți în sesiunea Art (separată) că urmează copy-ul:
  ```bash
  <venv_python> <CEO_PROFILE>/skills/assign-to-<ARTIST_SLUG>/scripts/delegate.py \
    --prompt "<prompt englez de imagine, fără copy-ul de post>" \
    --note "NEEDS_COPY — brief copy (RO): <ce slogan/headline/body/CTA vrea omul, ton, public>"
  ```

  **(d) La review-ul imaginii (sesiunea Art), recuperează brief-ul** cu
  `assign-to-<ARTIST_SLUG>/scripts/delegate.py --show-brief` (topicul Art n-are brief-ul din
  General). Fă MEREU cel puțin o rundă de rafinare a imaginii. **Verifică dacă brief-ul conține
  `NEEDS_COPY`.**

  **(e) Livrare CONDIȚIONATĂ — ramifică:**
  - ⛔ **Dacă brief-ul conține `NEEDS_COPY` → NU LIVRA imaginea acum.** Ia calea imaginii aprobate
    din pointer:
    ```bash
    <venv_python> -c "print(open(r'<ARTIST_IMAGES_DIR>/last_image.txt',encoding='utf-8').read().strip())"
    ```
    Deleagă copy-ul DOAR prin `assign-to-<slug>` cu `--image <calea de mai sus>` (runda 1; rundele
    de feedback fără `--image`). Folosește brief-ul copy (RO) de după `NEEDS_COPY —`. **Review copy
    AUTONOM** (limba corectă, se potrivește cu imaginea + brief-ul; cap per worker). Apoi
    **livrează O SINGURĂ DATĂ imaginea cu copy-ul în CAPTION**, prin `deliver.py` al artistului:
    ```bash
    <venv_python> <CEO_PROFILE>/skills/assign-to-<ARTIST_SLUG>/scripts/deliver.py \
      --caption "<headline> — <body> — <CTA>  (copy-ul final, în <LANGUAGE>)"
    ```
    Apoi **STOP**. (NU `MEDIA:` în proză — ai fi în topicul greșit.)
  - ✅ **Dacă brief-ul NU conține `NEEDS_COPY`** (cerere „DOAR IMAGINE") → livrezi imaginea normal,
    ca în fluxul artistului.

  **(f) LOOP GUARD — adaugă regula dură anti-livrare-goală (repetată în secțiunea LOOP GUARD):**
  „NICIODATĂ nu livra imaginea înainte de copy dacă brief-ul are `NEEDS_COPY` — dacă livrezi
  imaginea goală, ai ratat tot rostul copywriter-ului." Plus: ca să delegi copy rulează
  `assign-to-<slug>` cu `--image` (runda 1); NU tasta `@<copywriter>` în proză; cap **per worker**;
  workerii nu vorbesc între ei.

## Pas 8 — Înregistrează + repornește + verifică (mecanic + AUTONOM)
- Adaugă `<slug>` în **team.json-ul echipei LIVE** (cel găsit la Pas 1).
- `<venv_python> <live_manage.py> fresh` (restart + șterge sesiuni — necesar după persona/SOUL nou).
- Confirmă noul bot „✓ telegram connected", fără erori reale, și **fără** `📬 No home channel`.

> ⚠️ **HERMES_HOME la rularea scripturilor:** în producție fiecare gateway rulează cu
> `HERMES_HOME = profilul lui` (tokenul se ia din `HERMES_HOME/.env`, starea din `HERMES_HOME/cache`).
> Când rulezi TU `delegate.py`/`deliver.py` al unui worker pentru test, setează
> `HERMES_HOME=<CEO_PROFILE>` (profilul care deține skill-ul), altfel `delegate.py`-ul ne-patch-uit
> al artistului dă `ERROR: no TELEGRAM_BOT_TOKEN`. (Patcher-ul de la Pas 6.5 elimină fragilitatea
> asta pentru artist, dar nuanța rămâne validă pentru orice script de worker.)

- **Pornește monitorul auto-kill (în fundal):**
  `<venv_python> scripts/monitor.py --python <venv_python> --manage <live_manage.py> --profiles <ceo>,<artist>,<slug> --max-deliveries <cap+2> --window 300`

- **Treapta 1 — test MECANIC (delegare directă):** rulează `assign-to-<slug>/scripts/delegate.py
  --reset` apoi cu `--prompt` + `--image <o imagine de test existentă>`. În loguri confirmă:
  copywriter-ul **primește poza ȘI o VEDE** (caută `vision_analyze` / „native vision" / „image(s)
  attached inline" în logul lui), scrie copy în **limba corectă**, mențiune către CEO; CEO
  reacționează/livrează; **un singur** răspuns de la copywriter (fără buclă/chatter).

- **Treapta 2 — test AUTONOM (decizia CEO-ului, bug-ul real):** testul mecanic NU validează că CEO-ul
  *decide singur* să delege copy. Pentru asta, **cere utilizatorului să trimită o cerere reală** de
  reclamă în General, apoi monitorizează tot lanțul:

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Trimite în General o cerere de tip reclamă (ex. „fă-mi o reclamă 1:1 pentru un curs de fotografie, cu slogan și CTA"). Ai trimis?"
>   opțiuni: ["Da, am trimis"], ["Sari peste testul autonom"]

  Dacă „Da", verifică în loguri **lanțul complet**: CEO → `assign-to-<artist>` **cu `--note
  NEEDS_COPY`** (confirmă cu `--show-brief` că nota e în brief, iar logul artistului NU conține
  `NEEDS_COPY`) → imagine → review → `assign-to-<slug>` **cu `--image`** → Ryan VEDE poza + scrie
  copy (limba corectă) → CEO livrează imagine **cu copy în caption** în General → STOP. Fără buclă;
  monitorul nu a oprit echipa (≤ cap+2 livrări).

  Confirmă rezultatul cu userul:

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Cum a mers? (Reclama a venit cu imagine ȘI copy?)"
>   opțiuni: ["Merge — imagine+copy în General"], ["A livrat doar imaginea (fără copy)"], ["Nu răspunde / buclă / limbă greșită"]

  - „Merge" → succes. „Doar imaginea" → SOUL-ul nu a prins decizia: verifică PASUL 0 + `--note` +
    livrarea condiționată (`--show-brief` trebuie să arate `NEEDS_COPY`). Restul → inspectează loguri
    + monitor (gating/handoff/token/vision).
  - La final: `--reset` la contoarele ambilor workeri, șterge `<CEO_PROFILE>/cache/.delivered_image.json`
    și `fresh` pentru start curat.

## Reguli finale
- Copywriter nou = ÎNTOTDEAUNA gated în topicul „Copywriting". Doar CEO-ul e liber.
- Delegare DOAR prin `assign-to-<slug>` (mențiune+thread hardcodate + cap). Secretele doar în `.env` (`chmod 600`), niciodată în doc/git.
- **Necesită un artist** (worker de imagini): lanțul automat imagine→copy depinde de el. Patch-ul
  `patch_artist_delegate.py` (idempotent) adaugă `--note` + citire robustă a tokenului în
  `delegate.py` al artistului — NU rescrie alt comportament al artistului.
- **Decizia „reclamă = imagine+copy" + livrarea condiționată trăiesc în SOUL-ul CEO-ului** (PASUL 0
  + `NEEDS_COPY`). NICIODATĂ nu livra imaginea goală când brief-ul are `NEEDS_COPY`.
- **`--note` se atașează doar la runda 1** a delegării către artist (decizia se ia din start).
- NU atinge profilul `default`, NU modifica gating-ul celorlalți workeri.
- Idempotent: re-rularea pe o echipă cu copywriter existent doar re-aplică patch-urile (Pas 0).
- Acest skill adaugă **un singur** copywriter (rol fix: imagine+brief→copy); doar persona/limba diferă.
