# CLAUDE.md — reguli pentru proiectul `agenti-office`

Proiect: agenți AI care colaborează pe Telegram (stil *The Office*) construiți cu **Hermes
Agent** + **Google Gemini**. Vezi `RUNBOOK.md` pentru ghidul complet. Respectă regulile de mai
jos ori de câte ori lucrezi aici sau rulezi/editezi skill-urile.

## Interacțiune
- **Orice** întrebare către utilizator se pune prin tool-ul **AskUserQuestion** — niciodată ca
  text liber. Valorile libere (token-uri, chei, id-uri, nume) → utilizatorul le introduce în
  opțiunea „Other". Grupează logic (max 4 întrebări/apel), mai multe runde dacă e nevoie.
- Skill-urile sunt **autonome cu pauze**: fă tot ce poți singur și oprește-te DOAR la pașii
  Telegram pe care doar utilizatorul îi poate face (BotFather, grup, topicuri).
- **Pattern pentru pași fizici (user-friendly):** când utilizatorul trebuie să facă ceva manual,
  NU-l trimite la documente externe (RUNBOOK etc.) — **afișează pașii compleți PE ECRAN** (text
  neutru, numerotat, cu URL-uri exacte), apoi într-**un singur** apel AskUserQuestion confirmă că a
  terminat („Gata, am terminat" / „Am nevoie de ajutor") **și** colectează secretele (token/cheie/
  parolă în „Other"). „Am nevoie de ajutor" → afișează o variantă mai detaliată și re-întreabă cu
  ACELAȘI apel. Valorile pe care le poți obține singur (group id, topic id via `curl`/API, instalări
  `pip`) le iei/le faci TU, nu le ceri userului — îi ceri doar ce nu poți face singur (ex. instalare
  Chrome la nivel de sistem). Skill-urile `adauga-*` includ blocuri-exemplu literale de AskUserQuestion;
  copiază-le și înlocuiește placeholderele.

## Anti-buclă (REGULA DE AUR)
- **Exact UN bot e „liber"** (CEO/manager: `TELEGRAM_REQUIRE_MENTION=false`). **Toți** workerii
  sunt **gated** (`TELEGRAM_REQUIRE_MENTION=true`), fiecare în **topicul lui**.
- Topologie **hub**: totul trece prin CEO; workerii NU vorbesc între ei.
- Doi boți „liberi" în același topic = **buclă infinită**. Niciodată.
- `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true` peste tot.

## Workflow de creare a agenților (ordine & dependențe)
- **`instaleaza-hermes` e Pasul 0 (bootstrap, ÎN AFARA lanțului de agenți)** — pe o mașină nouă
  instalează Hermes Agent (Mac/Linux/Windows, prin installer-ul oficial) + configurează cheia Gemini
  **non-interactiv** (`hermes setup` e TUI și nu merge în Claude Code → folosește `hermes config set`
  + scriere `.env`; dovadă cu `hermes -z`). Tratează gotcha-ul Claude Desktop (PATH moștenit → binar
  invizibil în sesiune → cale absolută). Idempotent (oferă upgrade), backup config înainte de
  modificări. Rulează **înainte** de `adauga-ceo`; NU instalează deps office (google-genai/psutil) și
  NU atinge Telegram — alea rămân pentru `adauga-ceo`.
- **Ordinea e obligatorie:** `adauga-ceo` e **PRIMUL** — pune fundația (CEO-ul liber + grupul
  Telegram cu Topicuri + `team.json`-ul **canonic** în `adauga-ceo/scripts/`). Abia apoi se adaugă
  workeri.
- **Workflow standard, în ordine:** `adauga-ceo` (1) → **`adauga-artist` (2) → `adauga-copywriter`
  (3) → `adauga-web-developer` (4)**. Artistul vine **ÎNAINTEA** copywriter-ului fiindcă e sursa
  imaginii pe care copywriter-ul o primește; **web-developer-ul e ULTIMUL** fiindcă depinde de
  imagini (artist) + copy (copywriter). Toți workerii necesită un CEO existent, sunt gated în topicul
  lor, își adaugă topicul în `TELEGRAM_ALLOWED_TOPICS` al CEO-ului și **extind SOUL-ul CEO**. Lanțul
  *imagine→copy→livrare* se leagă automat (cu acord) când există ambii. Pentru **landing**:
  *artist (2-3 imagini) → copywriter (copy pagină) → web-developer (`index.html`) → CEO împachetează
  un `.zip` (index.html + imagini) și-l livrează în General*. `adauga-web-developer` wire-uiește
  lanțul peste artistul + copywriter-ul existenți (le extinde SOUL-ul; **upgrade multi-imagine** la
  delegarea copywriter-ului, backward-compatible) și degradează elegant dacă lipsesc.
- **`adauga-membru-echipa` e ÎN AFARA workflow-ului** — escape hatch pentru un agent **custom**
  (orice rol/persona) pe care îl vrei tu, libertate maximă; raportează tot la CEO, dar nu face parte
  din lanțul standard artist→copywriter→web-developer.
- **`adauga-avocat` e ÎN AFARA workflow-ului** — agent AVOCAT (default Toby, slug `avocat`, topic
  „Juridic"), standalone, declanșat când CEO-ul e rugat să verifice un contract. Verifică contracte
  cu cercetare de legislație pe internet (necesită `ddgs` în venv + `web.search_backend: ddgs`), pe 3
  runde CEO↔avocat; avocatul își salvează analiza completă într-un fișier (`avocat_analiza.md`), iar
  CEO-ul livrează în General un **Go/No-Go scurt + PDF aprofundat** prin `deliver_verdict.py` (script
  determinist cu **lock anti-duplicat** + reguli anti-duplicat pe sesiunile per-topic ale CEO-ului).
  Necesită Chrome pentru PDF. NU e în lanțul artist→copywriter→web-developer.
- **`adauga-secretara` e ÎN AFARA workflow-ului** — agent SECRETARĂ (default Erin Hannon, slug `erin`,
  topic „Secretariat"), standalone, declanșat când CEO-ul e rugat să scrie/citească email. Are un
  **mailbox Gmail sau Yahoo** (ales la rulare). **Outbound:** CEO compune → secretara trimite
  (`send_email.py`); răspunsurile merg pe **ACELAȘI thread** (`reply_email.py`, `Re:` + `In-Reply-To`).
  Aprobare: omul aprobă spiritul O dată, apoi CEO compune+trimite (fără draft repetat, exceptând cererea
  explicită). **Inbound:** un **watcher** auto-poll (în `team.json` „watchers", pornit cu echipa prin
  `manage.py`) trezește secretara cu **directivă-în-mesaj**; ea **FILTREAZĂ** (important vs promo/spam) și
  raportează CEO-ului **cu UID**, care relayează în General. ⚠️ Folosește variabile **`MAILBOX_*`** (nu
  `EMAIL_*`) ca să NU pornească canalul email NATIV Hermes (altfel fură inbox-ul + auto-răspunde fără
  aprobare). NU e în lanțul artist→copywriter→web-developer.
- **`team.json` canonic:** skill-urile de workeri caută `team.json` întâi în `adauga-ceo/scripts/`,
  apoi `reproducere-agenti-office/scripts/`, `echipa-boti-hermes`, `adauga-membru-echipa/scripts/`.
  Pe ACELA îl actualizezi + repornești (nu pe copia proprie de fallback).
- **REGULĂ DE MENTENANȚĂ:** când creezi/modifici un skill de creare de agenți, **actualizează
  imediat workflow-ul de dependențe** — diagrama + ordinea din `README.md` (secțiunea „Flux de
  creare a echipei") ȘI lista de mai sus din `CLAUDE.md`, plus ordinea de căutare a `team.json`-ului
  în skill-urile afectate. Workflow-ul de dependențe nu se lasă niciodată în urma skill-urilor.

## Handoff determinist (CEO → worker)
- CEO-ul deleagă **DOAR** prin skill-ul `assign-to-<worker>` (`delegate.py`), care pune
  mențiunea + thread-ul din `handoff.json` și impune un **cap dur de runde** (implicit 3, reset
  după 10 min). CEO-ul **nu tastează NICIODATĂ** `@worker` în proză (Gemini Flash uită → de aici
  scriptul).
- Workerul de imagini livrează prin `gen_image.py` (tag `MEDIA:` în răspuns). Scriptul își ia
  singur cheia din `.env`.

## Config care oprește „chatter-ul" (CRITIC)
În FIECARE `config.yaml`, sub `display:`:
- `busy_ack_enabled: false` (oprește „⚡ Interrupting…").
- UN SINGUR bloc `display.platforms.telegram` cu: `streaming: false`, `tool_progress: off`,
  `interim_assistant_messages: false`, `long_running_notifications: false`,
  `cleanup_progress: true`, `busy_ack_detail: false`, `show_reasoning: false`.
- ⚠️ Blocul clonat are deja un `platforms:` duplicat (`streaming: true`) — YAML păstrează ultima
  cheie, deci **consolidează într-unul singur**, altfel setarea e ignorată în tăcere.
- `agent.restart_drain_timeout: 20`.

## Limbă & persona
- Limba conversației se setează în `SOUL.md`. Prompturile de imagine către Gemini rămân
  **engleză** (calitate); text românesc pe imagine → între ghilimele duble în promptul englez.
- După ce schimbi limba/persona, rulează `manage.py fresh` (restart + șterge sesiuni) — altfel
  modelul imită limba din istoricul vechi.

## Modele
- Creier: `gemini-3.5-flash` (multimodal/ieftin). Imagini: `gemini-3-pro-image` (Nano Banana Pro).

## Secrete
- Doar în `.env` (`chmod 600`). NICIODATĂ în SKILL.md, RUNBOOK, README sau git. În doc/skill —
  doar placeholdere (`<GROUP_ID>`, `@<worker>_bot`, `<TOKEN>`).

## Structură & cod
- Fiecare skill e **self-contained**: propriul `scripts/` + `templates/`, fără referințe `../`
  către alt skill sau rădăcina proiectului.
- Toate scripturile sunt **python3 cross-platform** (Win/macOS/Linux); `manage.py` folosește
  `psutil`. Rulează cu venv-ul Hermes: `~/.hermes/hermes-agent/venv/bin/python`.
- NU atinge profilul Hermes `default`.

## Verificare (mereu)
- Test controlat (declanșează un ciclu prin skill-ul de delegare) + **monitor auto-kill** care
  oprește boții dacă apar > cap+1 livrări (runaway).
- Confirmă: conectare „✓ telegram connected", ZERO „💻 terminal"/„⚡ Interrupting", limba corectă,
  livrare în General, `handoff_*.json` cu `round` corect, fără buclă.

## Comenzi utile
```bash
PY=~/.hermes/hermes-agent/venv/bin/python
$PY ~/coding/projects/agenti-office/.claude/skills/reproducere-agenti-office/scripts/manage.py {start|stop|restart|status|logs <profil>|fresh}
```
