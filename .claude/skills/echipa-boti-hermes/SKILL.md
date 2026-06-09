---
name: echipa-boti-hermes
description: Builder generic „ca la carte" pentru o echipă de agenți Telegram colaborativi pe Hermes Agent (un manager/CEO + unul sau mai mulți workeri), parametrizabil (nume/roluri/personalități, limbă/temă, modele LLM și de imagini, topologie/cap de runde). Încorporează din fabrică toate fix-urile verificate: anti-chatter, gating asimetric, handoff determinist + cap, reset sesiuni la schimbare limbă/persona. Autonom cu pauze pentru pașii Telegram; cere secretele la rulare. Folosește când utilizatorul vrea să construiască de la zero o echipă de boți care colaborează, corect, fără problemele clasice.
---

# Builder generic — echipă de agenți Telegram (Hermes)

Construiește, „ca la carte", o echipă **manager (CEO) → workeri** care colaborează pe Telegram,
încorporând din fabrică TOATE lecțiile din `~/coding/projects/agenti-office/RUNBOOK.md` (anti-chatter, gating asimetric,
handoff determinist + cap, reset sesiuni). Lucrezi autonom, cu pauze pentru pașii Telegram, și
ceri secretele la rulare (doar în `.env`, niciodată în git).

Scripturi cross-platform partajate: `scripts/` (`gen_image.py`, `delegate.py`, `manage.py`).
Exemple de SOUL/sub-skill: `templates/`.

## REGULĂ DE INTERACȚIUNE (obligatorie)
**Orice** întrebare către utilizator se pune prin tool-ul **AskUserQuestion**, niciodată text
liber. Pentru valori libere (nume, token-uri, chei, id-uri) folosește AskUserQuestion și
utilizatorul le introduce în opțiunea „Other". Grupează logic (max 4 întrebări per apel); pune
mai multe runde dacă specificația e bogată.

## Pas 1 — Strânge specificația echipei (prin AskUserQuestion)
Întreabă utilizatorul (prin AskUserQuestion, în runde de câte 4) și notează:
- **Limba** conversației și **tema** (ex. Office, piraterie, corporate neutru).
- **Managerul/CEO**: nume + personalitate. (Exact UN bot e „liber".)
- **Workerii** (1+): pentru fiecare — nume, rol/specialitate, personalitate, și dacă e
  **worker de imagini** (folosește Gemini) sau **worker text** (alt tip de output).
- **Modele**: creier (recomandat `gemini-3.5-flash`, multimodal/ieftin) + model imagini
  (recomandat `gemini-3-pro-image`) dacă există worker de imagini.
- **Topologie**: implicit **hub** (un grup-forum; topicul General = user↔CEO; câte un topic
  per worker = CEO↔worker). Workerii NU vorbesc între ei — totul prin CEO.
- **Cap de runde** de pushback per task (implicit 3) + reset_gap (implicit 600s).

## Pas 2 — PAUZĂ: pașii Telegram (per bot)
Ghidează utilizatorul (vezi RUNBOOK §3, are screenshot-uri). Pentru FIECARE bot (CEO + fiecare worker):
1. `@BotFather /newbot` → username terminat în `bot`; salvează token-ul.
2. `/setprivacy → Disable` + activează **Bot-to-Bot Communication Mode**.
Apoi: creează un **grup-forum**, adaugă TOȚI boții, promovează-i **admini**, și creează câte
un **topic per worker** (plus General). Confirmarea că a terminat + colectarea secretelor (cheia
Gemini + toate token-urile) se fac prin **AskUserQuestion** (valori în opțiunea „Other").

## Pas 3 — Group id + topic ids
Cu gateway-urile oprite, după ce userul trimite câte un mesaj în fiecare topic:
`curl -s "https://api.telegram.org/bot<CEO_TOKEN>/getUpdates"` → extrage `chat.id` (-100…) și
`message_thread_id` pentru fiecare topic de worker. General = `1`.

## Pas 4 — Profiluri (clonate din `default`, neatins)
Pentru CEO și fiecare worker: `hermes profile create <slug> --clone --description "<rol>"`.

## Pas 5 — Config per profil (REGULI BAKED-IN, nu le sări)
În FIECARE `config.yaml`:
- `model: { default: <creier>, provider: gemini }`
- `agent.restart_drain_timeout: 20`
- **Anti-chatter** — consolidează UN SINGUR `display.platforms.telegram` (elimină duplicatul
  `platforms` din clonă!) + `display.busy_ack_enabled: false`:
```yaml
display:
  busy_ack_enabled: false
  platforms:
    telegram:
      streaming: false
      tool_progress: off
      interim_assistant_messages: false
      long_running_notifications: false
      cleanup_progress: true
      busy_ack_detail: false
      show_reasoning: false
```
Verifică cu yaml.safe_load că `display.platforms.telegram` are valorile de mai sus și că nu există chei duplicate.

## Pas 6 — `.env` gating (REGULA ANTI-BUCLĂ)
Toți: `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN=<tokenul lui>`,
`TELEGRAM_GROUP_ALLOWED_CHATS=-100<GROUP_ID>`, `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true`.
- **CEO (singurul liber):** `TELEGRAM_REQUIRE_MENTION=false`,
  `TELEGRAM_ALLOWED_TOPICS=1,<topic_worker_1>,<topic_worker_2>,...` (General + toate topicurile de workeri).
- **Fiecare worker (gated):** `TELEGRAM_REQUIRE_MENTION=true`,
  `TELEGRAM_ALLOWED_TOPICS=<topicul lui>`.
`chmod 600` pe toate `.env`.
> Regula: EXACT un bot cu `require_mention=false`. Dacă doi boți sunt liberi în același topic → buclă infinită.

## Pas 7 — Worker de imagini (dacă există)
Copiază `scripts/gen_image.py` în `~/.hermes/profiles/<worker>/skills/image-studio/scripts/`
+ scrie un `image-studio/SKILL.md` (vezi `templates/image-studio.SKILL.md`,
adaptat la limbă). Setează `GEN_IMAGE_MODEL` dacă vrei alt model de imagini.

## Pas 8 — Skill de delegare per worker (în profilul CEO-ului)
Pentru FIECARE worker, creează în profilul CEO-ului:
```
~/.hermes/profiles/<ceo>/skills/assign-to-<worker>/
  scripts/delegate.py   (copie din scripts/delegate.py)
  handoff.json          → {"worker_mention":"@<worker_username>","thread_id":"<topic_id>","max_rounds":<cap>,"reset_gap":600}
  SKILL.md              (adaptat din templates/assign-to-pam.SKILL.md)
```
`delegate.py` e identic pentru toți — diferă doar `handoff.json` + folderul skill-ului
(state-ul e per-worker, cheiat după mențiune).

## Pas 9 — SOUL-uri (generate din persona+rol, în limba aleasă)
Generează `SOUL.md` pentru fiecare profil urmând STRUCTURA dovedită (vezi
`templates/michael.SOUL.md` și `pam.SOUL.md`):
- **CEO**: identitate/persona; „două+ topicuri" (General cu omul, câte un topic per worker);
  „deleagă DOAR prin skill-urile assign-to-<worker>, nu tasta handle-uri"; flux
  CLARIFICĂ→BRIEF→DELEAGĂ→EVALUEAZĂ→LIVREAZĂ în General; LOOP GUARD (cap, fără handle în proză,
  stop după livrare). Listează TOȚI workerii și skill-ul de delegare al fiecăruia.
- **Worker**: persona; „lucrezi DOAR în topicul tău"; tool-ul lui (image-studio sau altul);
  „acționează doar la task/feedback de la CEO; taci la aprobări/laude"; o livrare pe rundă.
Toate în limba aleasă; prompturile de imagine rămân engleză.

## Pas 10 — Launcher + pornire + verificare
- **team.json LIVE** = `~/.hermes/team.json` (seed și lângă `manage.py`): `{"profiles": ["<ceo>", "<worker1>", ...]}`.
- `<venv-python> manage.py start` → toți RUNNING + „✓ telegram connected".
- Test controlat per worker (declanșează un ciclu prin skill-ul de delegare) cu monitor
  auto-kill (oprește dacă > cap+1 livrări într-un ciclu). Confirmă: fără chatter, limba corectă,
  livrare în General, fără buclă.

## Cum scalezi la N workeri fără buclă (esențial)
- Mereu EXACT un bot liber: CEO-ul. Toți ceilalți gated, fiecare în topicul lui.
- Workerii nu se declanșează decât prin skill-ul `assign-to-<worker>` al CEO-ului (mențiune
  hardcodată + cap). CEO-ul vede tot și coordonează. Astfel, indiferent de N, bucla e imposibilă.
- Ca să adaugi un worker la o echipă EXISTENTĂ, folosește skill-ul `adauga-membru-echipa`.

## Reguli pe care le respecți mereu
- Secretele doar în `.env` (chmod 600). NU atinge profilul `default`.
- Exact un bot liber; restul gated. Delegare DOAR prin skill (mențiune hardcodată + cap).
- La schimbare de limbă/persona: `manage.py fresh` (restart + șterge sesiuni), altfel modelul
  imită limba din istoric.
