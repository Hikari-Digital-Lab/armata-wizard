# Config changes for the lawyer profile (`<SLUG>/config.yaml`)

The lawyer is a **gated, purely-reactive text worker** that **researches the web**. Build its
`config.yaml` like this:

## 1. Start from a known-good team config (anti-chatter already verified)
`hermes profile create <SLUG> --clone` clones from `default`, whose `config.yaml` does NOT have the
consolidated anti-chatter `display` block. So OVERWRITE it with a config that does:

- **Preferred source:** an existing **gated worker** in the team (already gated + anti-chatter-clean):
  `cp <HERMES_HOME>/profiles/<GATED_WORKER>/config.yaml <HERMES_HOME>/profiles/<SLUG>/config.yaml`
- **Fallback:** the **CEO** config (always exists). If you copy the CEO's, make sure the worker stays
  gated (the `.env` `TELEGRAM_REQUIRE_MENTION=true` must win).

The good `display` block (already present in the team's configs):
```yaml
display:
  busy_ack_enabled: false
  # ...
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
Also: `agent.restart_drain_timeout: 20`, `model.default: <TEAM_MODEL>` (e.g. gemini-3.5-flash).

## 2. Disable the kanban dispatcher (anti-chatter)
```yaml
kanban:
  dispatch_in_gateway: false
```
This (with the `.env` home-channel keys) prevents the `📬 No home channel` notice.

## 3. ⭐ ENABLE WEB SEARCH (critical — the lawyer must research legislation)
By default `web.search_backend` is empty → there is NO active search provider, so `web_search`
silently returns nothing and the model flails (it tries `execute_code`/HTTP, which fails). Fix it:

1. Install the keyless DuckDuckGo backend into the Hermes venv (once per machine):
   ```bash
   uv pip install --python <HERMES_HOME>/hermes-agent/venv/bin/python ddgs
   ```
   (verify: `<venv_python> -c "import ddgs; print('ddgs', ddgs.__version__)"`)
2. Point the lawyer's config at it:
   ```yaml
   web:
     backend: ''
     search_backend: ddgs
     extract_backend: ''
   ```
With another provider (Exa/Firecrawl/Brave) you'd set its name + the API key in `.env` instead — but
`ddgs` needs **no key** and is the default for this skill.

## 4. Keep it gated
Gating is enforced by `.env` (`TELEGRAM_REQUIRE_MENTION=true`). If you copied the CEO's config (CEO is
free), make sure nothing forces `require_mention: false` — the `.env` value must win.

## 5. Curator — leave it as the team has it
This skill does NOT change `curator.*` / `skills.creation_nudge_interval`. (If you ever see the bot
auto-rewriting its own SKILL.md or spending turns on "update the skill library", that's the curator —
disable with `curator.enabled: false` + `skills.creation_nudge_interval: 0`, but only if you want to.)

## 6. Verify
```
grep -nE 'default:|busy_ack_enabled|tool_progress: off|restart_drain|dispatch_in_gateway|search_backend' \
  <HERMES_HOME>/profiles/<SLUG>/config.yaml
```
Expect: model set, `busy_ack_enabled: false`, `tool_progress: off`, `restart_drain_timeout: 20`,
`dispatch_in_gateway: false`, **`search_backend: ddgs`**.
