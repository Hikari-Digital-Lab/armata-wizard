# Marketplace `armata-wizard` — instalare ca plugin Claude Code

Acest repo e și un **marketplace de plugin-uri Claude Code**. Conține un singur plugin,
**`armata-wizard`**, care împachetează skill-urile de construire a unei echipe de agenți AI pe
Telegram (stil *The Office*) cu **Hermes Agent** + **Google Gemini**.

## Ce conține plugin-ul

8 skill-uri (în ordinea workflow-ului de creare a echipei):

| # | Skill | Rol |
|---|-------|-----|
| 0 | `instaleaza-hermes` | Bootstrap: instalează Hermes Agent + cheia Gemini (rulează primul, în afara lanțului) |
| 1 | `adauga-ceo` | **Fundația** — CEO-ul liber + grupul Telegram cu Topicuri + `team.json` canonic |
| 2 | `adauga-artist` | Worker care generează imagini (Gemini Nano Banana Pro) |
| 3 | `adauga-copywriter` | Worker care scrie textul de reclamă din imagine + brief |
| 4 | `adauga-web-developer` | Worker care construiește un `index.html` din imagini + copy |
| — | `adauga-membru-echipa` | Escape-hatch: agent custom (orice rol/persona) |
| — | `adauga-avocat` | Standalone: verifică contracte (cercetare legislație + verdict PDF) |
| — | `adauga-secretara` | Standalone: trimite/citește email (Gmail/Yahoo) la cererea CEO-ului |

> Cele două buildere alternative „full" (`echipa-boti-hermes` și `reproducere-agenti-office`) NU sunt
> incluse în plugin — rămân în repo doar pentru dezvoltare.

## Instalare

În Claude Code:

```
/plugin marketplace add Hikari-Digital-Lab/armata-wizard
/plugin install armata-wizard@armata-wizard
```

(Sau din terminal: `claude plugin marketplace add Hikari-Digital-Lab/armata-wizard` apoi
`claude plugin install armata-wizard@armata-wizard`.)

După instalare, skill-urile apar namespaced, de ex. `armata-wizard:adauga-ceo`. Le poți invoca sau
le invocă Claude automat în funcție de context. Pornește cu `instaleaza-hermes`, apoi `adauga-ceo`.

## Stare LIVE și unde se scrie

Workflow-ul scrie **starea reală** (profiluri Hermes, `.env`, sesiuni, handoff, imagini, loguri,
PDF-uri) sub `~/.hermes/` (`HERMES_HOME`) — **nu** în directorul plugin-ului. Manifestul canonic al
echipei este **`~/.hermes/team.json`** (LIVE), ținut acolo special ca să rămână editabil chiar și
când skill-urile rulează dintr-un cache de plugin read-only. Copia `scripts/team.json` din fiecare
skill e doar un *seed*/fallback. Astfel plugin-ul funcționează corect și după instalare/upgrade.

## Actualizare / dezinstalare

```
/plugin marketplace update armata-wizard
/plugin uninstall armata-wizard@armata-wizard
```

## Note

- **Versionare:** plugin-ul folosește semver explicit (`version` în `plugin.json`). Bump la fiecare
  release ca utilizatorii să primească update.
- **Windows:** skill-urile sunt referite prin symlink-uri în `plugins/armata-wizard/skills/` către
  `.claude/skills/`. La instalarea prin marketplace (clonare git + copiere de către Claude Code)
  symlink-urile sunt dereferențiate automat. Clonarea manuală pe Windows poate să nu materializeze
  symlink-urile — folosește calea de instalare prin marketplace.
- **Licență:** Apache-2.0.
