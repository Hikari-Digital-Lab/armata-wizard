---
name: adauga-ceo
description: "PRIMUL skill când construiești o echipă de boți Telegram pe Hermes — pune fundația. Creează un agent CEO/manager STAND-ALONE (default Michael Scott din The Office; opțional persona custom), botul lui liber care răspunde pe toate topicurile grupului + DM. Te ghidează să-ți creezi un GRUP Telegram cu Topicuri (forum) și botul în BotFather. Stabilește team.json-ul canonic + manage.py pe care skill-urile de workeri (adauga-artist / adauga-copywriter) le folosesc apoi. CEO = singurul bot liber (require_mention=false) → baza anti-buclei."
version: 1.0.0
author: silviu
license: Apache-2.0
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Telegram, Agents, CEO, Foundation, Onboarding]
---

# Adaugă CEO (fundația echipei — primul skill)

Creează agentul **CEO/manager** și pune bazele echipei Telegram. Rezultat: un bot **liber**
(`TELEGRAM_REQUIRE_MENTION=false`) care răspunde în topicurile grupului + DM, **stand-alone** (fără
workeri încă). Default persona: **Michael Scott**. După acest skill, adaugi workeri cu
`adauga-artist` / `adauga-copywriter`, care extind SOUL-ul CEO-ului cu fluxurile de delegare.

Self-contained: `scripts/` (`manage.py`, `monitor.py`), `templates/` (persona Michael + skeleton
custom + `ceo.config.yaml` verificat + `ceo.env` + `config-changes.md` + `telegram-setup.md`).

## REGULĂ DE INTERACȚIUNE (obligatorie)
**Orice** întrebare către utilizator se pune prin **AskUserQuestion**, niciodată text liber:
alegerea persona (Michael vs custom), limba, confirmarea pașilor Telegram, colectarea cheii Gemini
+ token-ului CEO (valori libere → „Other"). Max 4 per apel, mai multe runde.

**Pattern pentru pași fizici (obligatoriu):** când utilizatorul trebuie să facă ceva manual
(BotFather, grup, topic), NU trimite la documente externe — **afișează pașii compleți PE ECRAN**
(text neutru, numerotat, cu URL-uri exacte), apoi într-**un singur** apel AskUserQuestion confirmă
că a terminat („Gata, am terminat" / „Am nevoie de ajutor") **și** colectează secretele (token/cheie
în „Other"). Dacă alege „Am nevoie de ajutor", afișează o variantă mai detaliată și re-întreabă cu
ACELAȘI apel. Valorile pe care le poți obține singur (group id, topic id) le iei TU (rulezi `curl`),
nu le ceri userului.

## ANTI-BUCLĂ (regula de aur) — se pune AICI baza
- CEO-ul e **singurul** bot liber: `TELEGRAM_REQUIRE_MENTION=false`. Orice worker adăugat ulterior
  va fi **gated**. `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true` peste tot.
- Doi boți liberi în același topic = buclă. De aceea CEO-ul rămâne unicul liber.
- NU atinge profilul `default`.

---

## Pas 1 — Alege persona (prin AskUserQuestion)
Întreabă într-un apel (max 4 întrebări):

> APELEAZĂ AskUserQuestion (exemplu literal — copiază, adaptează):
> Întrebarea 1 — „Ce personaj vrei pentru CEO?"
>   opțiuni: ["Michael Scott (The Office)"], ["Alt personaj (custom)"]
> Întrebarea 2 — „În ce limbă să vorbească echipa?"
>   opțiuni: ["Română"], ["Engleză"]   (alta → „Other")
> Întrebarea 3 — „Ce model folosim pentru creier?"
>   opțiuni: ["gemini-3.5-flash (recomandat)"]   (altul → „Other")

- **Slug** profil: implicit `michael` (Michael) sau cerut pentru custom (lowercase).
- Dacă a ales **custom**, fă o a doua rundă AUQ: cere **numele** personajului, **slug-ul** profilului
  și o **descriere** a caracterului/tonului (toate în „Other").

## Pas 2 — PAUZĂ: creează grupul Telegram cu Topicuri + botul CEO

> AFIȘEAZĂ userului (text neutru, pas-cu-pas):
> ─────────────────────────────────────────────────────────────
> Hai să creăm botul CEO și grupul de Telegram. Durează ~5 minute.
>
> A. Creează botul în BotFather
>   1. Deschide Telegram și scrie către BotFather: https://t.me/BotFather
>      (e contul oficial cu bifă albastră, nu o aplicație separată).
>   2. Trimite comanda:  /newbot
>   3. Dă-i un nume afișat (ex. „Michael Scott").
>   4. Dă-i un username care se TERMINĂ obligatoriu în „bot" (ex. michael_scott_dm_bot).
>   5. BotFather îți trimite un TOKEN (un șir lung cu „:"). Copiază-l — îl ceri mai jos.
>   6. Trimite:  /setprivacy  → alege botul → apasă „Disable"
>      (ca să vadă toate mesajele din grup, nu doar pe cele care îl menționează).
>   7. Trimite:  /mybots → alege botul → „Bot Settings" →
>      „Group Privacy / Bot-to-Bot Communication Mode" → pune-l pe ON
>      (ca să poată vorbi mai târziu cu boții workeri).
>
> B. Creează grupul CU Topicuri (mod forum)
>   8. În Telegram creează un GRUP NOU (te poți adăuga doar pe tine la început).
>   9. Deschide grupul → Edit → activează „Topics" (devine supergrup-forum cu un topic „General").
>      Pe telefon: setările grupului → comutatorul „Topics".
>  10. Adaugă botul CEO în grup și promovează-l ADMIN
>      (setările grupului → Administrators → Add admin → alege botul).
>  11. Scrie un mesaj oarecare în topicul „General" (ca să pot citi id-ul grupului).
> ─────────────────────────────────────────────────────────────

> APELEAZĂ AskUserQuestion (exemplu literal — copiază, înlocuiește placeholderele):
> Întrebarea 1 — „Ai terminat pașii de mai sus?"
>   opțiuni: ["Gata, am terminat"], ["Am nevoie de ajutor"]
> Întrebarea 2 — „Lipește token-ul botului CEO (de la BotFather)"  → user scrie în „Other"
> Întrebarea 3 — „Lipește cheia API Google Gemini"                 → user scrie în „Other"

> DACĂ a ales „Am nevoie de ajutor": afișează varianta detaliată de mai jos, apoi re-întreabă cu ACELAȘI AUQ:
>   - BotFather îl găsești căutând „BotFather" în bara de căutare Telegram (are bifă albastră).
>   - După `/setprivacy`, dacă scrie deja „Privacy: DISABLED", e gata — nu mai trebuie schimbat.
>   - „Bot Settings" pe telefon e în meniul cu trei puncte din conversația cu BotFather.
>   - „Topics" la grup: dacă nu vezi opțiunea, grupul trebuie să fie supergrup — activarea Topics îl convertește automat.
>   - Ca să promovezi botul admin pe mobil: apasă pe numele grupului → Administrators → Add Administrator → alege botul.
>   - Cheia Gemini o obții de la https://aistudio.google.com/apikey („Create API key").

> DUPĂ confirmare (NU afișa nicio comandă userului):
>   - Verifică tu token-ul cu `getMe` (`curl -s "https://api.telegram.org/bot<TOKEN>/getMe"`) → reține `username`-ul real al CEO-ului.

## Pas 3 — Ia group id-ul (Claude rulează singur — userul NU rulează curl)
După ce userul a confirmat că a scris în „General", rulează TU:
`curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"` → extrage `chat.id` (un `-100…`) = `<GROUP_ID>`.
Topicul **General** are id **1**. NU afișa comanda userului. (Detalii extra opționale în
`templates/telegram-setup.md`.)

## Pas 4 — Creează profilul CEO
1. `hermes profile create <slug> --clone --description "CEO/manager"`.
2. **config.yaml**: urmează `templates/config-changes.md` — copiază `templates/ceo.config.yaml`
   peste config-ul clonat (aduce anti-chatter verificat + `restart_drain_timeout:20` +
   `kanban.dispatch_in_gateway:false`). Dacă ai ales alt model, editează `model.default`.
3. **.env** din `templates/ceo.env` — completează `<GEMINI_KEY>`, `<TOKEN>`, `<GROUP_ID>`. Păstrează
   `TELEGRAM_REQUIRE_MENTION=false`, `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true`,
   `TELEGRAM_ALLOWED_TOPICS=1` (General; workerii adaugă topicurile lor mai târziu), home channel pe
   General, DM deschis (fără `TELEGRAM_ALLOWED_USERS`). `chmod 600`.
4. **SOUL.md**:
   - Michael → `templates/michael.SOUL.md`, înlocuiește `<LANGUAGE>`, `<CEO_USERNAME>`, `<GROUP_NAME>`.
   - Custom → `templates/ceo.SOUL.md`, înlocuiește și `<NAME>`, `<CHARACTER_DESCRIPTION>`.
   (SOUL-ul e STANDALONE, fără referințe la workeri — skill-urile de workeri îl extind ulterior.)

## Pas 5 — team.json canonic + scripturi
- Creează **`~/.hermes/team.json`** (HERMES_HOME) = `{"profiles": ["<slug>"]}` — acesta devine
  manifestul **canonic** al echipei live, ținut în HERMES_HOME ca să rămână editabil și când
  skill-urile rulează dintr-un cache de plugin read-only. `manage.py` îl citește de acolo (fallback:
  seed-ul bundled `<acest_skill>/scripts/team.json`). Poți lăsa și o copie seed în `scripts/team.json`.
- (Skill-urile `adauga-artist` / `adauga-copywriter` / etc. citesc acest team.json LIVE — vezi Pas 1-ul lor.)

## Pas 6 — Pornește + verifică
- `<venv_python> <acest_skill>/scripts/manage.py fresh` (sau `start`). Confirmă „✓ telegram
  connected", fără erori reale, **fără** `📬 No home channel`.
- **Test + monitor auto-kill:**
  - Monitor în fundal:
    `<venv_python> scripts/monitor.py --python <venv_python> --manage <acest_skill>/scripts/manage.py --profiles <slug> --max-deliveries 4 --window 120`
  - Cere testul afișând pe ecran instrucțiunea, apoi confirmă prin AUQ:

> AFIȘEAZĂ userului: „Scrie un mesaj în topicul «General» (ex.: «salut, cine ești?») și, opțional, un DM către bot."

> APELEAZĂ AskUserQuestion (exemplu literal):
> Întrebarea 1 — „Cum a mers testul?"
>   opțiuni: ["Merge — a răspuns corect"], ["Nu răspunde deloc"], ["Răspunde greșit (limbă/topic/buclă)"]

  - DACĂ „Merge": confirmă în loguri (persona/limba corectă, topicul corect, fără chatter) și declară succesul.
    ALTFEL: inspectează logurile + monitorul, remediază (token/gating/`📬 No home channel`) și reia testul.
    (CEO n-are workeri de delegat încă — testul validează doar că e viu și răspunde curat.)

## Pas 7 — Pașii următori (informează utilizatorul)
Spune-i că fundația e gata și că poate adăuga membri:
- `adauga-artist` — worker de imagini (default Pam) în topicul lui.
- `adauga-copywriter` — worker de copy (default Ryan) în topicul lui.
Acele skill-uri vor extinde automat SOUL-ul + allowlist-ul CEO-ului și vor folosi acest team.json.

## Reguli finale
- CEO = ÎNTOTDEAUNA singurul bot liber. Secretele doar în `.env` (`chmod 600`), niciodată în doc/git.
- NU atinge profilul `default`. Persona/limba sunt singurele lucruri variabile; rolul e „CEO/manager standalone".
