---
name: reproducere-agenti-office
description: Reproduce fidel setup-ul de doi agenți Telegram în stil The Office (Michael Scott CEO/manager + Pam Beesly artistă de imagini Gemini) construiți cu Hermes Agent. Creează profilurile, config-urile, skill-urile și scripturile, cu toate setările verificate (anti-chatter, gating asimetric, handoff determinist, cap de runde). Autonom, cu pauze pentru pașii Telegram (BotFather/grup) și cere secretele la rulare. Folosește când utilizatorul vrea să recreeze exact acești boți.
---

# Reproducere — Agenți Office (Michael CEO + Pam artistă)

Recreează FIDEL setup-ul descris în `~/coding/projects/agenti-office/RUNBOOK.md`. Lucrezi **autonom**, dar te
**oprești** la pașii pe care doar utilizatorul îi poate face în Telegram (Partea A) și
**ceri secretele la rulare** (nu le scrii niciodată în fișiere versionate — doar în `.env`).

Scripturile cross-platform sunt în `scripts/` (`gen_image.py`, `delegate.py`,
`manage.py`). Le **copiezi** în profilurile Hermes la pașii de mai jos.

Convenții de cale (adaptează la OS):
- venv python: `~/.hermes/hermes-agent/venv/bin/python` (Win: `...\venv\Scripts\python.exe`)
- profiluri: `~/.hermes/profiles/<nume>/`

## REGULĂ DE INTERACȚIUNE (obligatorie)
**Orice** întrebare către utilizator se pune prin tool-ul **AskUserQuestion**, niciodată ca
text liber în chat. Asta include: confirmări („ai terminat pașii din BotFather?"), alegeri și
colectarea de valori. Pentru valori libere (token-uri, chei, id-uri) folosește AskUserQuestion
și utilizatorul le introduce în opțiunea „Other". Grupează întrebările logic (până la 4 per
apel AskUserQuestion).

## Pas 0 — Prerechizite
1. `hermes --version` și `hermes doctor`. Dacă lipsește `hermes`, oprește-te și spune
   utilizatorului să instaleze Hermes Agent (`curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`), apoi reia.
2. Confirmă venv 3.11: `~/.hermes/hermes-agent/venv/bin/python --version`.
3. Instalează deps în venv: `<venv-python> -m pip install google-genai psutil` (sau `uv pip install --python <venv-python> google-genai psutil`).

## Pas 1 — PAUZĂ: pașii utilizatorului în Telegram (Partea A din RUNBOOK §3)
Cere-i utilizatorului să facă (ghidează-l cu RUNBOOK §3, are screenshot-uri). Confirmarea că a
terminat se cere prin **AskUserQuestion** (ex. opțiuni „Gata" / „Am nevoie de ajutor"):
1. `@BotFather` → 2 boți (username-uri terminate în `bot`): **Michael** și **Pam**. Salvează cele 2 token-uri.
2. Pe AMBII: `/setprivacy → Disable` + activează **Bot-to-Bot Communication Mode** (Bot Settings).
3. Creează un **grup-forum** (Topics activat), adaugă ambii boți, promovează-i **admini**.
4. Creează un topic numit **Art** (pe lângă General).
Așteaptă confirmarea că a terminat.

## Pas 2 — Cere secretele (la rulare, niciodată în fișiere git)
Cere prin **AskUserQuestion** (valorile se introduc în opțiunea „Other"): `GOOGLE_API_KEY`,
`MICHAEL_TOKEN`, `PAM_TOKEN`. Reține-le doar pentru a le scrie în `.env`.

## Pas 3 — Creează profilurile
```bash
hermes profile create michael --clone --description "Michael Scott: CEO/manager"
hermes profile create pam     --clone --description "Pam Beesly: artistă imagini Gemini"
```

## Pas 4 — Model creier (ambii: Gemini Flash)
În `~/.hermes/profiles/<michael|pam>/config.yaml`, blocul `model:` de sus:
```yaml
model:
  default: gemini-3.5-flash
  provider: gemini
```

## Pas 5 — Oprește chatter-ul (CRITIC) + drain rapid
În FIECARE `config.yaml`:
- adaugă `busy_ack_enabled: false` în blocul `display:`;
- **consolidează** într-un SINGUR `display.platforms.telegram` (atenție: blocul clonat are deja un `platforms:` cu `streaming: true` — elimină duplicatul, YAML păstrează ultima cheie!):
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
    discord:
      streaming: false
```
- setează `agent.restart_drain_timeout: 20`.
Verifică: `<venv-python> -c "import yaml;d=yaml.safe_load(open('CALE/config.yaml'));print(d['display']['platforms']['telegram'], d['display'].get('busy_ack_enabled'))"`

## Pas 6 — Group id + Art topic id
Roagă utilizatorul să trimită un mesaj în topicul **Art** și unul în **General**. Apoi (cu gateway-urile OPRITE):
```bash
curl -s "https://api.telegram.org/bot<MICHAEL_TOKEN>/getUpdates"
```
Extrage `chat.id` = `-100…` (type supergroup) și `message_thread_id` al topicului Art (mesajul cu `is_topic_message:true`, ex. `2`). General = thread `1`.

## Pas 7 — `.env` per profil (gating asimetric)
`~/.hermes/profiles/michael/.env` (append, apoi `chmod 600`):
```dotenv
GOOGLE_API_KEY=<cheia>
GEMINI_API_KEY=<cheia>
TELEGRAM_BOT_TOKEN=<MICHAEL_TOKEN>
TELEGRAM_GROUP_ALLOWED_CHATS=-100<GROUP_ID>
TELEGRAM_REQUIRE_MENTION=false
TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true
TELEGRAM_ALLOWED_TOPICS=1,<ART_TOPIC_ID>
```
`~/.hermes/profiles/pam/.env`:
```dotenv
GOOGLE_API_KEY=<cheia>
GEMINI_API_KEY=<cheia>
TELEGRAM_BOT_TOKEN=<PAM_TOKEN>
TELEGRAM_GROUP_ALLOWED_CHATS=-100<GROUP_ID>
TELEGRAM_REQUIRE_MENTION=true
TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true
TELEGRAM_ALLOWED_TOPICS=<ART_TOPIC_ID>
```

## Pas 8 — Skill-ul de imagini al lui Pam
```
~/.hermes/profiles/pam/skills/image-studio/
  SKILL.md
  scripts/gen_image.py   (copie din scripts/gen_image.py)
```
`image-studio/SKILL.md` (instruiește Pam să ruleze scriptul cu venv-python absolut; scriptul își ia cheia singur; ROUND nou = `--prompt`, pushback = `--prompt <feedback> --edit-from <LAST_IMAGE>`; include `MEDIA:` verbatim în răspuns; o imagine/rundă; la `IMAGE_ERROR` nu intra în buclă).

## Pas 9 — Skill-ul de delegare al lui Michael
```
~/.hermes/profiles/michael/skills/assign-to-pam/
  SKILL.md
  handoff.json           → {"worker_mention":"@<PAM_USERNAME>","thread_id":"<ART_TOPIC_ID>","max_rounds":3,"reset_gap":600}
  scripts/delegate.py    (copie din scripts/delegate.py)
```
`assign-to-pam/SKILL.md`: Michael delegă DOAR prin acest skill (`delegate.py --prompt "<EN prompt>"`); NU tastează niciodată `@pam`; la `CAP_REACHED` livrează cea mai bună imagine în General și se oprește.

## Pas 10 — SOUL-urile (română; prompt imagine rămâne engleză)
Scrie `~/.hermes/profiles/michael/SOUL.md` și `pam/SOUL.md` din `templates/` (vezi fișierele
`michael.SOUL.md` și `pam.SOUL.md` din acest skill) — înlocuind `<PAM_USERNAME>` /
`<MICHAEL_USERNAME>` / `<ART_TOPIC_ID>` / `-100<GROUP_ID>` cu valorile reale.

## Pas 11 — Launcher + pornire
```bash
cp scripts/manage.py ~/.hermes/bin/manage.py   # sau rulează direct din proiect
# team.json lângă manage.py: {"profiles":["michael","pam"]}
<venv-python> <cale>/manage.py start
<venv-python> <cale>/manage.py status      # ambii RUNNING + în loguri "✓ telegram connected"
```

## Pas 12 — Verificare (test controlat + auto-kill)
1. Confirmă conectarea ambilor.
2. Declanșează un ciclu: rulează `delegate.py --reset` apoi `delegate.py --prompt "A simple red apple on white background, photorealistic"` (ca Michael). Pornește în paralel un monitor care numără `Sending media` în logul Pam și **oprește boții dacă depășește baseline+4** (runaway).
3. Verifică în loguri: Pam a generat + a postat (`Sending media`), Michael a primit `[1 image]`, a livrat prin `send_message`, `handoff_*.json` arată `round` corect, ZERO mesaje `💻 terminal` / `⚡ Interrupting`, răspunsuri în **română**.
4. Dacă apar probleme, vezi tabelul de depanare din RUNBOOK §8.

## Reguli pe care le respecți mereu
- Secretele doar în `.env` (chmod 600), niciodată în SKILL/doc/git.
- NU atinge profilul `default` Hermes.
- Un singur bot liber (Michael), restul gated → fără buclă.
- Delegarea DOAR prin skill (mențiune hardcodată + cap).
