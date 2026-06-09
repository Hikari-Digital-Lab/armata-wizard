---
name: adauga-secretara
description: "Adaugă un agent SECRETARĂ (worker care trimite și primește email pe mailbox-ul biroului — Gmail sau Yahoo — la cererea CEO-ului) peste o echipă Hermes existentă. Default Erin Hannon (The Office) cu fișiere gata-făcute; opțional persona custom. Topologie hub: secretara e gated, raportează DOAR la CEO, fără buclă. Standalone (escape-hatch ca adauga-avocat): NU e în lanțul artist→copywriter→web-developer; se declanșează când CEO-ul e rugat să scrie/citească email. Outbound: CEO compune → secretara trimite (send_email.py); răspunsurile merg pe ACELAȘI thread (reply_email.py, Re:+In-Reply-To). Inbound: watcher auto-poll → secretara FILTREAZĂ → raportează CEO-ului cu UID. Încorporează toate lecțiile: MAILBOX_* (dezactivează canalul email nativ Hermes), directivă-în-trezire, aprobare-o-dată, watcher în manage.py, capcanele App Password."
version: 1.0.0
author: silviu
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Telegram, Agents, Delegation, Email, Gmail, Yahoo, Secretariat, Onboarding]
---

# Adaugă secretară (worker de email → raportează la CEO)

Adaugă **UN** worker secretar(ă) peste o echipă existentă (construită cu `adauga-ceo` /
`reproducere-agenti-office` / `echipa-boti-hermes` / `adauga-membru-echipa`). Secretara are un
**mailbox** (Gmail sau Yahoo) pe care:
- **trimite** emailuri la cererea CEO-ului (`send_email.py`), iar **răspunsurile** merg pe **ACELAȘI
  thread** (`reply_email.py`, cu `Re:` + `In-Reply-To`/`References`);
- **ascultă** inbox-ul printr-un **watcher** auto-poll, **FILTREAZĂ** (important vs promo/spam) și
  raportează CEO-ului DOAR ce contează, cu **UID**-ul (ca să poată cere un răspuns pe thread).

Topologie **hub**: secretara are botul + topicul ei, e **gated**, vorbește DOAR cu CEO-ul. Doar
CEO-ul rămâne liber → fără buclă. Skill **standalone** (escape-hatch, ca `adauga-avocat`): NU face
parte din lanțul artist→copywriter→web-developer; se declanșează când CEO-ul e rugat să scrie/citească email.

Self-contained: `scripts/` (`send_email.py`, `reply_email.py`, `check_inbox.py`, `inbox_watcher.py`,
`delegate.py` text-only config-driven, `manage.py` cu suport watchers, `monitor.py`), `templates/`
(Erin gata-făcută + skeleton custom + assign-to + email-studio + env + handoff + config-changes +
ceo-soul-additions).

## REGULĂ DE INTERACȚIUNE (obligatorie)
**Orice** întrebare către utilizator se pune prin tool-ul **AskUserQuestion**, niciodată text liber:
confirmarea CEO-ului, alegerea persona (Erin vs custom), **providerul (Gmail vs Yahoo)**, limba,
numele topicului, cap-ul de runde, confirmarea pașilor Telegram, colectarea token-ului noului bot +
a adresei + a App Password-ului (valori libere → opțiunea „Other"). Max 4 per apel.

**Pattern pentru pași fizici (obligatoriu):** când utilizatorul trebuie să facă ceva manual
(BotFather, generare App Password), NU trimite la documente externe — **afișează pașii compleți PE
ECRAN** (text neutru, numerotat, cu URL-uri exacte), apoi într-**un singur** apel AskUserQuestion
confirmă că a terminat („Gata, am terminat" / „Am nevoie de ajutor") **și** colectează secretele
(token/adresă/App Password în „Other"). Dacă alege „Am nevoie de ajutor", afișează o variantă mai
detaliată și re-întreabă cu ACELAȘI apel. Ce poți face singur (topic via API, `getUpdates`) faci TU.

## ANTI-BUCLĂ (regula de aur) — nu o încălca
- Exact UN bot e „liber" (CEO: `TELEGRAM_REQUIRE_MENTION=false`). Secretara e **gated**
  (`TELEGRAM_REQUIRE_MENTION=true`) în topicul ei. `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true` peste tot.
- Delegare CEO→secretară **DOAR** prin `assign-to-<slug>` (`delegate.py`): mențiune + thread hardcodate
  în `handoff.json` + **cap dur de runde**. CEO-ul NU tastează niciodată `@<secretară>` în proză.
- Watcher-ul de inbox postează trezirea prin **tokenul CEO-ului** (`TELEGRAM_NOTIFY_TOKEN`) cu
  mențiune **exclusivă** către secretară → doar ea reacționează, CEO-ul ignoră dump-ul brut. Watcher-ul
  e un script one-shot (nu un gateway reactiv) → nu poate face buclă.
- NU atinge gating-ul celorlalți workeri. NU atinge profilul `default`.

## ⚠️ LECȚII ÎNVĂȚATE (încorporează-le — altfel bug-urile se repetă)
1. **Canalul email NATIV Hermes fură inbox-ul.** Dacă `.env` are `EMAIL_ADDRESS`+`EMAIL_PASSWORD`+
   `EMAIL_IMAP_HOST`+`EMAIL_SMTP_HOST`, Hermes pornește gateway-ul lui de email (IMAP poll + auto-reply),
   care se bate cu scripturile pe inbox și răspunde clienților FĂRĂ aprobare. **FIX:** folosește
   variabile **`MAILBOX_*`** (nu `EMAIL_*`) — Hermes nu le detectează, canalul nativ rămâne OFF.
   Verifică după start: `grep -c platforms.email` în gateway.log-ul secretarei = **0**, iar log-ul spune
   `Gateway running with 1 platform(s)`.
2. **Pe sesiune nouă, Gemini se PREZINTĂ în loc să raporteze** mailul. **FIX:** directiva de triere
   („NU te prezenta, raportează cu UID în formatul …") e băgată **în mesajul de trezire** al watcher-ului
   (`check_inbox.py`), nu doar în SOUL. (SOUL singur NU e suficient — verificat azi.)
3. **Răspunsul trebuie pe ACELAȘI thread**, nu email nou. **FIX:** `check_inbox.py` salvează per-UID
   `Message-ID`+expeditor în `cache/inbox/<UID>.json`; `reply_email.py --uid N` construiește `Re:` +
   `In-Reply-To`/`References` + destinatarul corect. Niciodată email nou ca răspuns.
4. **Aprobare prea zgomotoasă.** Omul aprobă **spiritul O dată**, apoi CEO-ul compune + trimite, fără
   să mai afișeze draftul și fără a doua întrebare — DOAR dacă omul cere explicit „arată-mi draftul".
5. **Raportul secretarei TREBUIE să conțină UID-ul** (altfel CEO-ul nu poate delega un răspuns pe thread).
6. **„📬 No home channel".** Setează `TELEGRAM_HOME_CHANNEL=<GROUP_ID>` + `TELEGRAM_CRON_THREAD_ID=<TOPIC_ID>`
   (home channel = topicul ei) ca să nu apară notificarea și ca orice `send_message` să rămână în topic.
7. **`handoff.json` stă LÂNGĂ `delegate.py` în `scripts/`** (delegate.py îl citește din directorul lui),
   NU în rădăcina skill-ului `assign-to-*`.
8. **Watcher-ul pornește/oprește cu echipa** prin `manage.py` (lista `watchers` din `team.json`). La PRIMA
   rulare, `check_inbox.py --baseline` ca să nu inunde cu tot istoricul.
9. **App Password capcane:** necesită 2FA pornit. Gmail: `myaccount.google.com/apppasswords`. Yahoo:
   butonul „Create app password" e sub **External connections** și e adesea **grayed out** până te
   re-loghezi (incognito/desktop). NU parola normală — App Password-ul de 16 caractere.
10. **Topicul se poate crea via API** (CEO admin cu `can_manage_topics` → `createForumTopic`) — Pas 4.
    Privacy=Disable + adăugarea botului în grup rămân manuale.

---

## Pas 1 — Inspectează echipa existentă
- Găsește **team.json-ul echipei LIVE** (folosit de gateway-urile care rulează), în ordine: lângă
  `adauga-ceo/scripts/`, apoi `reproducere-agenti-office/scripts/`, apoi `echipa-boti-hermes`, apoi
  `adauga-membru-echipa/scripts/`. Reține calea lui + a `manage.py`-ului de lângă el — pe ACELA îl
  actualizezi și repornești (copia proprie din `scripts/` e fallback).
- Identifică **CEO-ul** = profilul cu `TELEGRAM_REQUIRE_MENTION=false`:
  `grep -l 'TELEGRAM_REQUIRE_MENTION=false' ~/.hermes/profiles/*/.env`. **Confirmă prin AskUserQuestion.**
- Din `.env`-ul CEO-ului citește `TELEGRAM_GROUP_ALLOWED_CHATS` (`<GROUP_ID>`), `TELEGRAM_ALLOWED_TOPICS`
  (topicuri actuale) și **`TELEGRAM_BOT_TOKEN` (`<CEO_TOKEN>` — pentru `TELEGRAM_NOTIFY_TOKEN`)**.
- Detectează **limba** și **modelul creier** (ex. `gemini-3.5-flash`) din SOUL-ul/config-ul echipei.
- **Coliziune slug:** verifică să nu existe deja un profil cu slug-ul ales (default `erin`); dacă da,
  alege altul prin AskUserQuestion.

## Pas 2 — Alege persona, providerul & parametrii (prin AskUserQuestion)
Întreabă într-un apel (max 4):

> APELEAZĂ AskUserQuestion (exemplu literal — copiază, adaptează):
> Î1 — „Ce personaj vrei pentru secretară?"  opțiuni: ["Erin Hannon (The Office)"], ["Alt personaj (custom)"]
> Î2 — „Ce provider de email folosește?"      opțiuni: ["Gmail"], ["Yahoo"]   (FĂRĂ default — userul alege)
> Î3 — „În ce limbă vorbește secretara?"      opțiuni: ["Ca echipa"], ["Română"], ["Engleză"]   (alta → „Other")
> Î4 — „Câte runde maxim CEO↔secretară?"      opțiuni: ["3 (recomandat)"]   (alt număr → „Other")

- **Numele topicului**: default **„Secretariat"** — întreabă într-o a doua rundă doar dacă vrei să-l schimbi.
- Reține host-urile providerului:
  - Gmail → `MAILBOX_IMAP_HOST=imap.gmail.com`, `MAILBOX_SMTP_HOST=smtp.gmail.com`.
  - Yahoo → `MAILBOX_IMAP_HOST=imap.mail.yahoo.com`, `MAILBOX_SMTP_HOST=smtp.mail.yahoo.com`.
  (Ambele: porturi 993 IMAP / 465 SMTP-SSL.)
- Dacă a ales **custom**, fă o a doua rundă AUQ: **numele**, **slug-ul** (default `erin`), **descrierea
  caracterului/tonului** (în „Other").

## Pas 3 — PAUZĂ: pașii Telegram + App Password
(Topicul „Secretariat" îl creez EU automat la Pas 4 — aici userul face botul, adăugarea în grup și App Password-ul.)

> AFIȘEAZĂ userului (text neutru, pas-cu-pas) — la secțiunea D afișează DOAR providerul ales la Pas 2:
> ─────────────────────────────────────────────────────────────
> Hai să creăm botul de Telegram + mailbox-ul pentru secretară. Durează ~5 minute.
>
> A. Creează botul în BotFather
>   1. Deschide Telegram și scrie către BotFather: https://t.me/BotFather (bifă albastră).
>   2. Trimite comanda:  /newbot
>   3. Dă-i un nume afișat (ex. „Erin Hannon").
>   4. Dă-i un username care se TERMINĂ obligatoriu în „bot" (ex. erin_secretariat_bot).
>   5. BotFather îți trimite un TOKEN (șir lung cu „:"). Copiază-l — îl ceri mai jos.
>   6. Trimite:  /setprivacy  → alege botul → „Disable".
>   7. Trimite:  /mybots → alege botul → „Bot Settings" →
>      „Group Privacy / Bot-to-Bot Communication Mode" → ON.
>
> B. Adaugă botul în grupul existent
>   8. Deschide grupul echipei (cel cu Topicuri).
>   9. Setările grupului → Add member → caută username-ul botului → adaugă-l.
>  10. Setările grupului → Administrators → Add admin → alege botul → confirmă.
>      (Topicul „Secretariat" NU trebuie creat manual — îl fac eu prin API după ce confirmi.)
>
> C. Pornește 2FA pe contul de email (obligatoriu pentru App Password)
>  11. App Password-ul funcționează DOAR cu verificarea în doi pași (2FA) activă pe cont.
>      Dacă nu ai 2FA pornit, activează-l întâi din setările de securitate ale contului.
>
> D-Gmail. Generează App Password (DOAR dacă ai ales Gmail)
>  12. Intră pe: https://myaccount.google.com/apppasswords
>  13. La „App name" scrie un nume (ex. „Secretara Hermes") → „Create".
>  14. Google îți arată o parolă de 16 caractere (4 grupuri de 4). Copiaz-o FĂRĂ spații — asta e App Password-ul.
>
> D-Yahoo. Generează App Password (DOAR dacă ai ales Yahoo)
>  12. Intră pe: https://login.yahoo.com/account/security/app-passwords
>  13. Butonul „Create app password" e sub secțiunea „External connections".
>      ⚠️ Dacă apare GRI/inactiv: deconectează-te și reloghează-te (fereastră incognito sau pe desktop)
>      după ce ai activat 2FA — abia atunci devine activ.
>  14. Dă-i un nume → „Create" → Yahoo îți arată o parolă de 16 caractere. Copiaz-o FĂRĂ spații.
>
> (Ai nevoie de: adresa de email + App Password-ul de 16 caractere — NU parola normală a contului.)
> ─────────────────────────────────────────────────────────────

> APELEAZĂ AskUserQuestion (exemplu literal — 4 întrebări, toate într-un apel):
> Întrebarea 1 — „Ai terminat pașii de mai sus?"
>   opțiuni: ["Gata, am terminat"], ["Am nevoie de ajutor"]
> Întrebarea 2 — „Lipește token-ul noului bot (de la BotFather)"  → user scrie în „Other"
> Întrebarea 3 — „Lipește adresa de email a mailbox-ului"          → user scrie în „Other"
> Întrebarea 4 — „Lipește App Password-ul (16 caractere, fără spații)"  → user scrie în „Other"
> (Cheia Gemini NU se cere — o iei din `.env`-ul unui profil existent.)

> DACĂ a ales „Am nevoie de ajutor": afișează varianta detaliată, apoi re-întreabă cu ACELAȘI AUQ:
>   - BotFather îl găsești căutând „BotFather" în Telegram (bifă albastră).
>   - Promovare admin pe mobil: numele grupului → Administrators → Add Administrator.
>   - 2FA Gmail: https://myaccount.google.com/security → „2-Step Verification".
>   - 2FA Yahoo: https://login.yahoo.com/account/security → „Two-step verification".
>   - App Password NU e parola contului; e un cod de 16 caractere generat special, care apare o singură dată — copiază-l imediat.
>   - Yahoo „grayed out": e cea mai frecventă capcană — reloghează-te în incognito după ce 2FA e activ.

> DUPĂ confirmare (NU afișa comenzile userului):
>   - Verifică tu token-ul cu `getMe` → reține `username`-ul real `<SECRETARY_USERNAME>`.

## Pas 4 — Creează topicul „Secretariat" + ia topic id-ul (Claude rulează singur)
**Automat prin API** (recomandat): cu **tokenul CEO-ului** (admin cu `can_manage_topics`), rulează TU:
```bash
curl -s "https://api.telegram.org/bot<CEO_TOKEN>/createForumTopic" \
  --data-urlencode "chat_id=<GROUP_ID>" --data-urlencode "name=<TOPIC_NAME>"
```
→ răspunsul conține `message_thread_id` = **`<TOPIC_ID>`**. NU afișa comanda userului.

**Fallback manual** (doar dacă API dă eroare):

> APELEAZĂ AskUserQuestion (exemplu literal — doar pe fallback):
> Întrebarea 1 — „Nu pot crea topicul automat. Creează te rog un topic nou numit „<TOPIC_NAME>" în grup și scrie în el un mesaj care menționează noul bot, apoi confirmă."
>   opțiuni: ["Gata, am creat topicul"], ["Am nevoie de ajutor"]

  După confirmare, oprește gateway-urile (`<venv_python> <live_manage.py> stop`) și rulează TU
  `getUpdates` cu tokenul noului bot → `message_thread_id` (golește bufferul cu `?offset=<max_update_id+1>`
  dacă vezi doar mesaje vechi).

## Pas 5 — Creează profilul secretarei
1. `hermes profile create <slug> --clone --description "<rol secretar>"`.
2. **config.yaml** — urmează `templates/config-changes.md`: copiază config-ul unui worker gated existent
   SAU al CEO-ului (anti-chatter + modelul echipei + `restart_drain_timeout: 20`), apoi
   `kanban.dispatch_in_gateway: false`, menține gated. **⛔ NU activa canalul email nativ** (Lecția 1).
   (Secretara e worker de TEXT — NU copia `gen_image.py`, NU crea `image-studio` de imagini.)
3. **email-studio skill**: creează `skills/email-studio/scripts/` în profilul secretarei și copiază toate
   cele 4 scripturi din `scripts/` al acestui skill: `send_email.py`, `reply_email.py`, `check_inbox.py`,
   `inbox_watcher.py`. Plus `SKILL.md` din `templates/email-studio.SKILL.md` (înlocuiește `<HERMES_HOME>`,
   `<VENV_PYTHON>`, `<SECRETARY_PROFILE>`).
   > **`<HERMES_HOME>`** = calea ABSOLUTĂ a directorului Hermes (`~/.hermes` expandat; rădăcina care
   > conține `hermes-agent/` și `profiles/`). Linux `/home/<user>/.hermes`, macOS `/Users/<user>/.hermes`,
   > Windows `C:/Users/<user>/.hermes`. Înlocuiește-l în TOATE template-urile de mai jos.
4. **.env** din `templates/secretara.env` — completează `<GEMINI_KEY>` (din `.env`-ul unui profil existent
   — NU inventa), `<TOKEN>`, `<GROUP_ID>`, `<TOPIC_ID>`, `<TOPIC_NAME>`, `<CEO_TOKEN>` (→ NOTIFY),
   `<SECRETARY_USERNAME>`, `<MAILBOX_ADDRESS>`, `<MAILBOX_APP_PASSWORD>`, și **host-urile providerului ales**
   (`<MAILBOX_IMAP_HOST>`/`<MAILBOX_SMTP_HOST>`). `chmod 600`.
5. **SOUL.md**:
   - Erin → `templates/erin.SOUL.md`, înlocuiește `<HERMES_HOME>`, `<LANGUAGE>`, `<CEO_NAME>`,
     `<SECRETARY_USERNAME>`, `<TOPIC_NAME>`, `<VENV_PYTHON>`, `<SECRETARY_PROFILE>`.
   - Custom → `templates/secretara.SOUL.md`, înlocuiește și `<NAME>`, `<CHARACTER_DESCRIPTION>`, `<TONE>`.
6. **⭐ TEST credențiale** (HERMES_HOME = profilul secretarei): `check_inbox.py --baseline` (login IMAP +
   setează baseline, fără notificări) și `send_email.py --to <MAILBOX_ADDRESS> --subject "Test" --body "ok"`
   (login SMTP + self-send). Ambele trebuie să meargă ÎNAINTE de a continua. Dacă pică login → App Password
   greșit/provider host greșit; corectează.

## Pas 6 — Skill de delegare CEO → secretară
În profilul CEO-ului creează `skills/assign-to-<slug>/`:
- `scripts/delegate.py` = copie din `scripts/delegate.py` al acestui skill (text-only, config-driven).
- `scripts/handoff.json` (⚠️ **în `scripts/`, lângă delegate.py** — Lecția 7) din `templates/handoff.json`
  cu `<SECRETARY_USERNAME>`, `<TOPIC_ID>`, `<MAX_ROUNDS>`.
- `SKILL.md` din `templates/assign-to-secretara.SKILL.md` cu placeholderele înlocuite (`<HERMES_HOME>`,
  `<SLUG>`, `<NAME>`, `<VENV_PYTHON>`, `<CEO_PROFILE>`, `<SECRETARY_USERNAME>`, `<TOPIC_NAME>`, `<MAX_ROUNDS>`).

## Pas 7 — Actualizează CEO-ul (cheie!)
- **`.env` CEO:** adaugă `<TOPIC_ID>` la `TELEGRAM_ALLOWED_TOPICS`.
- **`SOUL.md` CEO:** injectează blocurile din `templates/ceo-soul-additions.md` (parametrizate, în limba
  echipei — înlocuiește și `<HERMES_HOME>`, `<VENV_PYTHON>`, `<CEO_PROFILE>`, `<SLUG>`), MERGE în secțiunile existente (team, topicuri, LOOP GUARD) — nu duplica. Conțin: noul membru,
  topicul, **cele două formate de delegare** (RĂSPUNDE LA MAIL | UID / TRIMITE EMAIL), **EMAIL workflow cu
  aprobare-o-dată** (fără draft repetat, exceptând cererea explicită), regula de relay a raportului cu UID
  în General, și extinderea LOOP GUARD cu `@<SECRETARY_USERNAME>` + topicul.

## Pas 8 — Înregistrează watcher-ul + repornește + verifică
- **team.json LIVE:** adaugă `<slug>` la `"profiles"` ȘI calea absolută a watcher-ului la `"watchers"`
  (`<HERMES_HOME>` = calea absolută reală a dir-ului `.hermes`):
  `"<HERMES_HOME>/profiles/<slug>/skills/email-studio/scripts/inbox_watcher.py"`.
- **Asigură suport watchers în `manage.py`-ul LIVE:** `grep -q watchers <live_manage.py>`. Dacă LIPSEȘTE,
  adaugă funcția (copiază feature-ul din `scripts/manage.py` al acestui skill: `watchers()`, `_watcher_procs()`,
  și pornirea/oprirea/statusul lor în `start/stop/status`). Fără asta, watcher-ul NU pornește cu echipa.
- `<venv_python> <live_manage.py> fresh` (restart + șterge sesiuni — necesar după persona/SOUL nou).
- Confirmă „✓ telegram connected" (și pentru CEO), **`Gateway running with 1 platform(s)`** (Lecția 1:
  `grep -c platforms.email` = 0), fără erori reale, **fără** `📬 No home channel`. Gating: exact UN bot liber (CEO).
- **Test end-to-end + monitor auto-kill:**
  - Pornește monitorul: `<venv_python> scripts/monitor.py --python <venv_python> --manage <live_manage.py>
    --profiles <ceo>,<workeri>,<slug> --max-deliveries <cap+2> --window 240`.
  - **Outbound:** `assign-to-<slug>/scripts/delegate.py --reset`, apoi `--prompt "TRIMITE EMAIL | TO:
    <MAILBOX_ADDRESS> | SUBJECT: Test | BODY: ..."`. Verifică: secretara rulează `send_email.py` (`EMAIL_SENT ✓`),
    confirmă; CEO relayează în General. **Reply pe thread:** după ce watcher-ul prinde un mail (vezi mai jos)
    și raportează cu UID, `--prompt "RĂSPUNDE LA MAIL | UID: N | BODY: ..."` → `reply_email.py` → verifică în
    folderul **Sent** că răspunsul are `Re:` + `In-Reply-To`.
  - **Inbound:** trimite un email de test către `<MAILBOX_ADDRESS>`; în ≤interval watcher-ul postează `📨 MAIL
    NOU (UID N)` (mențiune exclusivă), secretara FILTREAZĂ și raportează cu UID („📬 … (UID N) …", FĂRĂ să se
    prezinte), CEO relayează în General. Fără chatter, fără buclă. Monitorul oprește echipa la runaway.
  - Confirmă rezultatul cu userul:

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Cum a mers testul de email?"
>   opțiuni: ["Merge — trimite și raportează inbox-ul"], ["Login email eșuat"], ["Buclă / canal email nativ pornit / nu raportează"]

  - DACĂ „Merge": declară succesul. DACĂ „Login email eșuat": App Password/host greșit — recolectează prin AUQ și reia testul de la Pas 5.6.
    ALTFEL: inspectează loguri + monitor (`grep -c platforms.email`=0, gating, watcher) și remediază.
  - La final, `--reset` la contoare, `check_inbox.py --baseline` (curăță mailurile de test), `fresh`.

## Reguli finale
- Secretară nouă = ÎNTOTDEAUNA gated în topicul ei. Doar CEO-ul e liber.
- Delegare DOAR prin `assign-to-<slug>` (mențiune+thread+cap). Trimitere DOAR prin `send_email.py`/
  `reply_email.py`. Secretele (token, App Password) doar în `.env` (`chmod 600`), niciodată în doc/git.
- `MAILBOX_*` (nu `EMAIL_*`) — canalul email nativ rămâne OFF. NU atinge profilul `default`, NU modifica
  gating-ul altora.
- Acest skill adaugă **o singură** secretară (rol fix: email send/receive + filtrare); persona/provider/
  limba/topic/cap diferă. **Standalone** — nu e parte din lanțul artist→copywriter→web-developer.
