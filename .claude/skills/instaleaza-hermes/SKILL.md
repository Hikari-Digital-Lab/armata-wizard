---
name: instaleaza-hermes
description: "PASUL 0 (bootstrap) înainte de orice echipă de boți: instalează Hermes Agent (NousResearch) de la zero pe calculatorul utilizatorului — Mac, Linux sau Windows — și îl configurează cu o cheie Google AI Studio (Gemini), pentru un utilizator FINAL non-tehnic. Detectează OS-ul și rulează installer-ul oficial; tratează gotcha-ul Claude Desktop (PATH moștenit → binar invizibil în sesiune). Idempotent (oferă upgrade dacă Hermes există), backup la config înainte de modificări, configurare NON-interactivă prin scriere de fișiere (fiindcă `hermes setup` e TUI și nu merge în Claude Code), dovadă reală prin `hermes -z` (one-shot). Se încheie cu ritualul AI-Wizard. Rulează ÎNAINTE de adauga-ceo."
version: 1.0.0
author: silviu
license: MIT
platforms: [linux, darwin, win32]
metadata:
  hermes:
    tags: [Hermes, Install, Bootstrap, Gemini, Onboarding, Setup]
---

# Instalează Hermes (Pasul 0 — bootstrap)

Instalează și configurează **Hermes Agent** (engine-ul pe care rulează toți boții echipei) pe
calculatorul utilizatorului, pe **orice** sistem (Mac / Linux / Windows). La final: Hermes instalat,
configurat cu o cheie **Gemini**, și o **dovadă** că merge (un mesaj de test cu răspuns real de la
model). Acesta e **Pasul 0**: după el, echipa Telegram se construiește cu `adauga-ceo` → workeri.

Self-contained: `scripts/` (`detect`, `backup`, `configure_gemini`, `verify` — fiecare în pereche
`.sh` pentru Linux/mac și `.ps1` pentru Windows) + `templates/` (`env.template`,
`config-model-block.yaml`, `aiwizard-box.txt`).

> **De ce e altfel decât celelalte skill-uri:** acesta e *bootstrap-ul* — rulează ÎNAINTE ca Hermes
> și Python-ul lui să existe. De aceea pașii de **detect + instalare** sunt în **bash/PowerShell**
> (nu python), iar **configurarea** folosește CLI-ul `hermes` (apelat prin **cale absolută**) abia
> după instalare.

## REGULĂ DE INTERACȚIUNE (obligatorie)
- **Orice** întrebare către utilizator se pune prin **AskUserQuestion**, niciodată ca text liber.
  Valorile libere (cheia Gemini) → utilizatorul le pune în opțiunea **„Other"**. Max 4 întrebări/apel.
- **Ton:** română, simplu, pe înțelesul oricui. Pentru fiecare pas explică în 1–2 propoziții (a) ce
  faci și (b) de ce. Fără jargon; dacă folosești un termen tehnic, explică-l în paranteze.
- **Pattern pentru pași fizici:** când utilizatorul trebuie să facă ceva manual (ex. să-și ia cheia
  Gemini), **NU** trimite la documente externe — **afișează pașii compleți PE ECRAN** (numerotat, cu
  URL exact), apoi într-**un singur** apel AskUserQuestion confirmă că a terminat **și** colectează
  secretul în „Other". Dacă alege „Am nevoie de ajutor", afișează o variantă mai detaliată și
  re-întreabă cu ACELAȘI apel.
- Ce poți face singur (rulezi scripturi, detectezi OS, scrii config) faci TU; ceri userului doar ce
  nu poți face în locul lui (cheia, eventual instalare manuală dacă installer-ul cere admin).

## ⚠️ AVERTISMENT CRITIC — PATH-ul în Claude Desktop (citește acum)
Claude Desktop pornește procese-copil care **moștenesc PATH-ul vechi**, dinainte de instalare. După
ce installer-ul pune binarul `hermes` (ex. `~/.local/bin/hermes`), **terminalul tău din această
sesiune s-ar putea să NU-l vadă**. De aceea:
- Apelează `hermes` mereu prin **cale absolută** (scripturile o fac deja). Nu te baza pe `hermes` „gol"
  în PATH în sesiunea curentă.
- Pe Windows **nu** folosi `setx` (poate șterge PATH-ul). Installer-ul oficial gestionează singur PATH-ul.
- Dacă tot nu se vede în sesiune, verificarea finală se face într-un **terminal nou deschis MANUAL** de
  utilizator (vezi Pas 5, fallback).

## ⚠️ NICIODATĂ comenzi interactive în Claude Code
`hermes` (gol), `hermes chat`, `hermes --tui`, `hermes setup` sunt **interactive (TUI)** și **blochează**
fără TTY. Nu le rula. Pentru configurare folosim **scrierea de fișiere** (`hermes config set` + `.env`),
iar pentru dovadă folosim **`hermes -z "..."`** (one-shot, non-interactiv).

---

## Pas 0 — Detectează OS-ul și ce există deja (fără să modifici nimic)
Rulează scriptul de detecție potrivit și parsează liniile `key=value`:
- Linux/macOS/WSL2: `bash scripts/detect.sh`
- Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File scripts/detect.ps1`

Reține: `OS`, `HERMES_INSTALLED`, `HERMES_BIN`, `HERMES_VERSION`, `HERMES_CONFIG`, `HERMES_ENV`,
`HAS_docker`, `DOCKER_RUNNING`. Raportează scurt utilizatorului: *„Sistemul tău e X. Hermes: instalat
vY / lipsește."*

## Pas 1 — Gate consolidat (UN apel AskUserQuestion)
Pune într-un singur apel (adaptează la ce ai detectat):

> APELEAZĂ AskUserQuestion (exemplu literal — copiază, adaptează):
> Întrebarea 1 — „Cum instalăm Hermes?"
>   opțiuni: ["Nativ (recomandat) — instalare directă pe sistem"], ["Docker — în container (necesită Docker Desktop)"]
> Întrebarea 2 — „Pot să instalez acum Hermes + dependențele pe acest calculator?"
>   opțiuni: ["Da, instalează"], ["Nu acum"]
> [DOAR dacă HERMES_INSTALLED=yes] Întrebarea 3 — „Am găsit Hermes vX. Faci upgrade la ultima versiune?"
>   opțiuni: ["Da, fă upgrade"], ["Nu, păstrează versiunea — doar configurează"]

- „Nu acum" la Întrebarea 2 → oprește-te politicos, nu instala nimic.
- Dacă `HERMES_INSTALLED=yes` și alege „Nu, păstrează" → **sari peste Pas 3** (instalarea) și treci la
  configurare (Pas 4). „Da, fă upgrade" → re-rulează installer-ul (Pas 3, ramura upgrade).
- Dacă a ales **Docker** dar `DOCKER_RUNNING=no` → spune-i clar că Docker nu e pornit/instalat, oferă
  fallback la **Nativ** (re-întreabă cu AskUserQuestion) sau lasă-l să pornească Docker Desktop.

## Pas 2 — Backup (înainte de orice modificare)
Spune: *„Întâi salvez o copie a setărilor tale actuale, ca să le pot restaura dacă e nevoie."*
- Linux/macOS: `bash scripts/backup.sh`
- Windows: `powershell -ExecutionPolicy Bypass -File scripts/backup.ps1`

Reține `BACKUP_DIR` (sau „none" la instalare curată) ca să-l pui în raportul final.

## Pas 3 — Instalează Hermes
Cere confirmarea o ai deja de la Pas 1. Explică scurt: *„Instalez Hermes — aduce singur tot ce-i
trebuie (Python, Node, etc.), fără să-ți strice altceva."* Apoi rulează ramura potrivită.

**Linux / macOS / WSL2 — nativ:**
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
# propagă PATH-ul în shell-ul curent (best-effort):
source "$HOME/.bashrc" 2>/dev/null || true
source "$HOME/.zshrc" 2>/dev/null || true
```

**Windows — nativ (PowerShell):**
```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```
> Installer-ul instalează sub `%LOCALAPPDATA%\hermes` și aduce un **Git Bash portabil** (MinGit, fără
> drepturi de admin). Nu folosi `setx`.

**Docker (alternativă, dacă a ales-o):** dacă `DOCKER_RUNNING=yes`, folosește setup-ul Docker al
Hermes (`docker compose` din arborele Hermes / imaginea oficială). Dacă Docker lipsește → fallback la
nativ.

**Upgrade (Hermes deja prezent + „Da"):** re-rulează **același** one-liner de mai sus — installer-ul
detectează instalarea (`.install_method`) și actualizează în loc.

**Auto-fix agresiv la eșec** (înainte să implici utilizatorul, încearcă în ordine):
1. Lipsă `curl` (Linux): încearcă `wget -qO- <url> | bash`; (mac) `curl` vine din sistem.
2. PATH nevăzut în sesiune → folosește calea absolută `~/.local/bin/hermes` (gotcha Claude Desktop).
3. Re-rulează installer-ul o dată (erori tranzitorii de rețea).
4. Re-`source` la `~/.bashrc`/`~/.zshrc`.

Abia dacă tot eșuează: **oprește-te**, arată eroarea exactă (în engleză cum vine) + o traducere pe
înțeles + 1–2 remedii, și nu continua orbește.

## Pas 4 — Configurează Gemini (NON-interactiv)
1. Afișează **pe ecran** pașii de obținere a cheii și apoi colectează cheia:

   > Pași pe ecran (afișează-i exact):
   > 1. Intră pe **https://aistudio.google.com/apikey**
   > 2. Loghează-te cu contul Google.
   > 3. Apasă **„Create API key"** (Creează cheie API).
   > 4. Copiază cheia (un șir lung de litere/cifre).
   >
   > APELEAZĂ AskUserQuestion (un singur apel):
   > Întrebarea — „Ai cheia Gemini? Lipește-o în «Other»."
   >   opțiuni: ["Gata, am cheia"  (→ cheia în «Other»)], ["Am nevoie de ajutor"]
   > „Am nevoie de ajutor" → afișează o variantă mai detaliată (cu capturi descrise în text) și
   > re-întreabă cu ACELAȘI apel.

2. Configurează (scrie provider+model și cheia, cu cale absolută la binar):
   - Linux/macOS: `bash scripts/configure_gemini.sh "<CHEIA>" gemini-3.5-flash`
   - Windows: `powershell -ExecutionPolicy Bypass -File scripts/configure_gemini.ps1 -Key "<CHEIA>" -Model gemini-3.5-flash`

   Scriptul: `hermes config set model.provider gemini` + `model.default gemini-3.5-flash`, apoi scrie
   `GOOGLE_API_KEY` + `GEMINI_API_KEY` în `.env` (merge-safe) și `chmod 600`. Configurează profilul
   **default** (`~/.hermes`) — corect pe o mașină nouă de utilizator final.

## Pas 5 — Verifică + validează cheia (= „prima conversație")
Rulează scriptul de verificare (folosește calea absolută → ocolește gotcha-ul PATH):
- Linux/macOS: `bash scripts/verify.sh`
- Windows: `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`

Citește liniile: `VERSION_OK`, `DOCTOR_OK`, `ONESHOT_OK`, `ONESHOT_REPLY`, `RESULT`.
- `RESULT=PASS` + `ONESHOT_REPLY` are text de la model → **succes**: arată-i utilizatorului că botul a
  răspuns („prima conversație" reușită).
- `ONESHOT_HINT=cheie_invalida` → cheia e greșită: re-cere cheia (Pas 4.1), re-rulează
  `configure_gemini`, re-verifică (maxim ~3 încercări).
- Dacă binarul nu e găsit deloc în sesiune (gotcha PATH dur): **fallback manual** — cere-i să deschidă
  un **terminal NOU** (Windows: Start → „Git Bash"; macOS: Terminal/iTerm2; Linux: terminalul lui) și
  să lipească: `hermes --version && hermes doctor && hermes -z "reply OK"`, apoi trimite-ți rezultatul.

## Pas 6 — Lasă gateway-ul pornit (best-effort)
Pornește serviciul de gateway în fundal (alegerea utilizatorului — lăsat pornit):
- `hermes gateway install` apoi `hermes gateway start` (serviciu de fundal), prin cale absolută.

Dacă gateway-ul cere configurare suplimentară (un canal — ex. Telegram), **nu eșua skill-ul**: notează
onest în raport că *gateway-ul e pregătit, dar stă în idle până adaugi un canal (ex. cu `adauga-ceo`)*.

## Pas 7 — Raport final
Trimite un raport scurt:
```
✅ Instalate / configurate:
  - Hermes Agent <versiune>
  - Provider: gemini · Model: gemini-3.5-flash
  - Cheie Gemini: setată (în .env, permisiuni private)
  - Test „prima conversație": <ONESHOT_REPLY>

ℹ️ Sărite (erau deja prezente):
  - <ex: instalarea, dacă a ales „doar configurează">

⚠️ Acțiuni manuale rămase (dacă există):
  - <ex: restart terminal, gateway idle până la un canal>

📁 Backup config: <BACKUP_DIR>
```

## Pas 8 — Ritualul de încheiere (AI-Wizard)
Afișează **exact** conținutul din `templates/aiwizard-box.txt` (e deja un fenced code block — păstrează
toate caracterele și spațiile, nu modifica nimic). Apoi:

> APELEAZĂ AskUserQuestion:
> Întrebarea — „Vrei să intri în comunitatea AI-Wizard?"  (header „Comunitate")
>   opțiuni: ["Da"], ["Nu, mulțumesc"]

- **„Nu, mulțumesc"** → spune o linie scurtă (*„Ok, mulțumesc că ai instalat alături de mine. Spor!"*)
  și **OPREȘTE-TE** — nicio altă întrebare, nicio comandă.
- **„Da"** → al doilea AskUserQuestion:
  > Întrebarea — „E ok să deschid acum https://ai-wizard.tech/comunitate în browser?"  (header „Browser")
  >   opțiuni: ["Da, deschide"], ["Nu, las mai târziu"]
  - „Nu, las mai târziu" → afișează URL-ul clicabil într-o linie și treci la mesajul final.
  - „Da, deschide" → deschide cu comanda potrivită OS-ului:
    - Windows: `Start-Process "https://ai-wizard.tech/comunitate"`
    - macOS: `open "https://ai-wizard.tech/comunitate"`
    - Linux: `xdg-open "https://ai-wizard.tech/comunitate"`
    - Dacă eșuează → fallback: *„Nu am putut deschide browserul. Accesează manual: https://ai-wizard.tech/comunitate"*

Mesaj final (o singură linie): **„Ne vedem în comunitate. Foc la ghete!"**

## ⛔ STOP
Aici se încheie skill-ul. Nu inventa pași noi, nu propune `/adauga-ceo` sau alte skill-uri, nu pune
alte întrebări, nu rula alte comenzi. Conversația se încheie după mesajul final.

## Comportament în caz de eroare (general)
- NU ascunde erorile, NU continua orbește. Arată eroarea exactă, traduce-o într-o propoziție, propune
  1–2 remedii.
- „Nu" la o confirmare = sari peste pasul respectiv.
- Dacă un pas cere drepturi de admin pe care userul nu le are, nu forța — explică-i ce să facă manual.
