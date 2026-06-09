# agenti-office

Documentație + skill-uri Claude Code pentru a construi agenți AI care colaborează pe Telegram
(stil *The Office*), cu [Hermes Agent](https://github.com/NousResearch/hermes-agent) + Google Gemini.

## Conținut
- **[RUNBOOK.md](RUNBOOK.md)** — ghidul complet: arhitectură, pașii tăi din Telegram (cu
  screenshot-uri), ce face Claude Code, tabelul cu TOATE setările care au mers, costuri,
  mentenanță/depanare, cum extinzi echipa.
- **`.claude/skills/`** — skill-uri Claude Code (de proiect; română, autonome cu pauze, secrete cerute la rulare):

  **Workflow standard (recomandat) — fundație, apoi membri în ordine:**
  | Pas | Skill | Rol |
  |---|---|---|
  | **0** | `instaleaza-hermes` | **Bootstrap (o singură dată).** Instalează Hermes Agent pe calculator (Mac/Linux/Windows) + configurează cheia Gemini, non-interactiv. Rulează ÎNAINTE de `adauga-ceo` pe o mașină nouă. |
  | **1** | `adauga-ceo` | **Fundația.** Creează CEO-ul liber (default Michael) + te ghidează să faci grupul Telegram cu Topicuri; stabilește `team.json`-ul canonic. |
  | **2** | `adauga-artist` | Worker de imagini (default Pam, Gemini Nano Banana Pro), gated în topicul lui. **Vine ÎNAINTEA copywriter-ului** (e sursa imaginii). |
  | **3** | `adauga-copywriter` | Worker de copy (default Ryan): primește imaginea de la artist + brief → scrie textul de reclamă. |
  | **4** | `adauga-web-developer` | Worker HTML (default Dwight): primește 2-3 imagini + copy-ul paginii → scrie un `index.html` self-contained. CEO-ul împachetează `index.html` + imaginile într-un `.zip` livrat în General. **Ultimul** (depinde de imagini+copy). |

  **În afara workflow-ului — libertate maximă:**
  | Skill | Ce face |
  |---|---|
  | `adauga-membru-echipa` | Îți creezi TU un agent **custom** (orice rol/persona) care NU e în workflow-ul de mai sus — escape hatch generic, raportează tot la CEO. |
  | `adauga-avocat` | Agent **AVOCAT** (default Toby) care verifică contracte: cercetează legislația pe internet (`web_search`/ddgs), 3 runde CEO↔avocat, apoi CEO-ul livrează un **Go/No-Go scurt + PDF cu analiza aprofundată** (determinist, anti-duplicat). Standalone — declanșat când CEO-ul e rugat să verifice un contract. |
  | `adauga-secretara` | Agent **SECRETARĂ** (default Erin Hannon) cu **mailbox Gmail/Yahoo**: trimite emailuri la cererea CEO-ului (`send_email.py`), **răspunde pe același thread** (`reply_email.py`, `Re:`+`In-Reply-To`), și **ascultă** inbox-ul cu un watcher auto-poll — **filtrează** și raportează CEO-ului doar ce contează, cu UID. Aprobare-o-dată. Folosește `MAILBOX_*` ca să NU pornească canalul email nativ Hermes. Standalone — declanșat când CEO-ul e rugat să scrie/citească email. |
  | `echipa-boti-hermes` | Builder generic „ca la carte": echipă manager→workeri de la zero, parametrizabilă, cu toate fix-urile baked-in. |
  | `reproducere-agenti-office` | Recreează FIDEL setup-ul curent (CEO Michael + Pam artistă). |
- **assets/** — imagini pentru doc (screenshot-uri Telegram + exemple generate).

Fiecare skill e **self-contained**: are propriul `scripts/` (cross-platform: `manage.py`,
`monitor.py`, și după caz `delegate.py`/`gen_image.py`) și `templates/` (SOUL-uri, config-uri,
sub-skill-uri), ca să nu depindă de fișiere din afara lui.

## Flux de creare a echipei

```
   PAS 0 (bootstrap, o singură dată pe o mașină nouă):
   • instaleaza-hermes  → instalează Hermes (Mac/Linux/Win) + configurează cheia Gemini, non-interactiv

   WORKFLOW STANDARD (în ordine):

   ┌─────────────────────────┐   ┌─────────────────────────┐   ┌──────────────────────────┐   ┌──────────────────────────┐
   │ 1. adauga-ceo           │   │ 2. adauga-artist        │   │ 3. adauga-copywriter     │   │ 4. adauga-web-developer  │
   │   CEO liber (Michael)   │──►│   worker imagini (Pam)  │──►│   worker copy (Ryan)     │──►│   worker HTML (Dwight)   │
   │   + grup + Topicuri     │   │   gated, topic propriu  │   │   gated, topic propriu   │   │   gated, topic propriu   │
   │   + team.json CANONIC   │   │   (SURSA imaginii)      │   │   imagine+brief → text   │   │   imagini+copy → index   │
   └─────────────────────────┘   └─────────────────────────┘   └──────────────────────────┘   │   .html ; CEO → .zip     │
        fundația, primul            artistul ÎNAINTEA copywriter-ului (îi dă imaginea)          └──────────────────────────┘
   fiecare worker: gated în topicul lui, raportează DOAR la CEO; își adaugă topicul în allowlist-ul
   CEO + extinde SOUL-ul CEO. Lanțul imagine→copy→livrare se leagă automat (cu acordul tău). Pentru
   landing: artist(2-3 imagini)→copywriter(copy pagină)→web-developer(HTML)→CEO împachetează un .zip.

   ÎN AFARA WORKFLOW-ULUI (libertate maximă):
   • adauga-membru-echipa     → agent CUSTOM (orice rol/persona) care NU e în workflow-ul de sus
   • adauga-avocat            → agent AVOCAT (default Toby): contract → cercetare legislație → Go/No-Go + PDF
   • adauga-secretara         → agent SECRETARĂ (default Erin): mailbox Gmail/Yahoo, trimite + răspunde pe thread + ascultă/filtrează inbox-ul
   • echipa-boti-hermes       → construiește CEO + workeri dintr-o singură rulare
   • reproducere-agenti-office → recreează exact Michael + Pam
```

**Ordine & dependențe:**
0. **`instaleaza-hermes` e Pasul 0 (bootstrap)** — pe o mașină nouă, instalează Hermes Agent
   (Mac/Linux/Windows, prin installer-ul oficial) + configurează cheia Gemini, **non-interactiv**.
   Rulează **o singură dată**, înaintea lui `adauga-ceo`. Pe o mașină unde Hermes există deja, oferă
   doar upgrade + (re)configurare. Tratează gotcha-ul Claude Desktop (PATH moștenit).
1. **`adauga-ceo` întâi** — creează singurul bot liber + `team.json`-ul canonic pe care workerii îl
   actualizează. Fără el (sau fără `echipa-boti-hermes` / `reproducere-agenti-office`), workerii
   n-au CEO la care să raporteze.
2. **`adauga-artist` (pas 2) vine ÎNAINTEA `adauga-copywriter` (pas 3)** — artistul e sursa
   imaginii pe care copywriter-ul o primește. Ambele necesită un CEO existent; fiecare e gated în
   topicul lui, își adaugă topicul în allowlist-ul CEO și extinde SOUL-ul CEO. Lanțul
   *imagine→copy→livrare* se leagă automat (cu acordul tău) când ambii există.
2b. **`adauga-web-developer` (pas 4) vine ULTIMUL** — depinde de imagini (artist) + copy (copywriter).
   Construiește pagina (`index.html`) din *2-3 imagini + copy-ul paginii*, iar CEO-ul livrează un
   `.zip` (index.html + imagini) în General. Wire-uiește lanțul peste artistul + copywriter-ul
   existenți: le extinde SOUL-ul (artist: set de 2-3 imagini; copywriter: mod „copy de pagină") și
   face **upgrade multi-imagine** la delegarea copywriter-ului (backward-compatible). Degradează
   elegant dacă lipsește artistul/copywriter-ul.
3. **`adauga-membru-echipa` e în afara workflow-ului** — pentru când vrei TU un agent custom (orice
   rol/persona), libertate maximă; raportează tot la CEO, dar nu face parte din lanțul standard.
4. **`adauga-avocat` e în afara workflow-ului** — agent AVOCAT (default Toby, slug `avocat`, topic
   „Juridic"), standalone, declanșat când CEO-ul e rugat să verifice un contract. Cercetează
   legislația pe internet (necesită `ddgs` în venv + `web.search_backend: ddgs`), pe 3 runde
   CEO↔avocat; avocatul își salvează analiza completă într-un fișier, iar CEO-ul livrează în General
   un **Go/No-Go scurt + PDF aprofundat** prin `deliver_verdict.py` (script determinist, cu lock
   anti-duplicat + reguli anti-duplicat pe sesiunile per-topic ale CEO-ului). Necesită Chrome pentru PDF.
5. **`adauga-secretara` e în afara workflow-ului** — agent SECRETARĂ (default Erin Hannon, slug `erin`,
   topic „Secretariat"), standalone, declanșat când CEO-ul e rugat să scrie/citească email. Are un
   **mailbox Gmail sau Yahoo** (ales la rulare). Outbound: CEO compune → secretara trimite
   (`send_email.py`); răspunsurile merg pe **același thread** (`reply_email.py`, `Re:`+`In-Reply-To`);
   omul aprobă spiritul O dată, apoi CEO compune+trimite (fără draft repetat, exceptând cererea explicită).
   Inbound: un **watcher** auto-poll (în `team.json` „watchers", pornit cu echipa) trezește secretara cu
   directivă-în-mesaj; ea **filtrează** (important vs promo/spam) și raportează CEO-ului **cu UID**, care
   relayează în General. Folosește `MAILBOX_*` (nu `EMAIL_*`) ca să NU pornească canalul email nativ Hermes.

## Cum folosești skill-urile în Claude Code
Skill-urile sunt **de proiect**, în `.claude/skills/` — Claude Code le descoperă automat când
rulezi în acest folder (`~/coding/projects/agenti-office/`). Sunt self-contained (scripts/ +
templates/ proprii). `RUNBOOK.md` și `CLAUDE.md` din proiect sunt referința.

**Experiență ghidată (user-friendly):** la pașii manuali (BotFather, grup, topic, App Password),
skill-urile `adauga-*` afișează instrucțiunile complete **pe ecran**, pas-cu-pas, în română — nu te
trimit la documente externe. Apoi te întreabă printr-un singur dialog (AskUserQuestion) dacă ai
terminat și îți cer doar secretele necesare (token/cheie/parolă). Dacă alegi „Am nevoie de ajutor",
primești o variantă mai detaliată. Ce se poate obține automat (id-uri de grup/topic, instalări) face
Claude singur — `RUNBOOK.md` rămâne doar referință opțională.

## Prerechizite
Hermes Agent instalat + configurat cu o cheie Google AI Studio (Gemini) — pe o mașină nouă, fă asta
cu skill-ul **`instaleaza-hermes`** (Pasul 0, automat, pe orice OS). Apoi: `google-genai` + `psutil`
în venv-ul Hermes (le pune `adauga-ceo`); cont Telegram. Detalii în RUNBOOK §2.
