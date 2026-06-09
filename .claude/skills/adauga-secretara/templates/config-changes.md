# Config changes for the secretary profile (`<SLUG>/config.yaml`)

The secretary is a **gated, reactive text worker** that drives email scripts. Build its
`config.yaml` like this:

## 1. Start from a known-good team config (anti-chatter already verified)
`hermes profile create <SLUG> --clone` clones from `default`, whose `config.yaml` does NOT have the
consolidated anti-chatter `display` block. So OVERWRITE it with a config that does:

- **Preferred:** copy an existing **gated worker** in the team (already gated + anti-chatter-clean):
  `cp <HERMES_HOME>/profiles/<GATED_WORKER>/config.yaml <HERMES_HOME>/profiles/<SLUG>/config.yaml`
- **Fallback:** the **CEO** config (always exists). If you copy the CEO's, make sure the worker stays
  gated (the `.env` `TELEGRAM_REQUIRE_MENTION=true` must win).

The good `display` block (already present in the team's configs):
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
Also: `agent.restart_drain_timeout: 20`, `model.default: <TEAM_MODEL>` (e.g. gemini-3.5-flash).

## 2. Disable the kanban dispatcher (anti-chatter)
```yaml
kanban:
  dispatch_in_gateway: false
```
This (with the `.env` home-channel keys) prevents the `📬 No home channel` notice.

## 3. ⛔ DO NOT enable Hermes' native email channel
The secretary does email through deterministic SCRIPTS, not Hermes' built-in email gateway. The
native channel auto-activates when `.env` has `EMAIL_ADDRESS` + `EMAIL_PASSWORD` + `EMAIL_IMAP_HOST`
+ `EMAIL_SMTP_HOST`. That's why this skill uses **`MAILBOX_*`** vars instead — Hermes does NOT detect
them, so the native channel stays OFF and the scripts own the inbox. NEVER add `EMAIL_ADDRESS` /
`EMAIL_PASSWORD` to the secretary's `.env`. (Verify after start: `grep -c platforms.email` in the
secretary's gateway log must be **0**, and the boot log says `Gateway running with 1 platform(s)`.)

## 4. Keep it gated
Gating is enforced by `.env` (`TELEGRAM_REQUIRE_MENTION=true`). If you copied the CEO's config (CEO is
free), make sure nothing forces `require_mention: false` — the `.env` value must win.

## 5. Curator — leave it as the team has it
This skill does NOT change `curator.*` / `skills.creation_nudge_interval`.

## 6. Verify
```
grep -nE 'default:|busy_ack_enabled|tool_progress: off|restart_drain|dispatch_in_gateway' \
  <HERMES_HOME>/profiles/<SLUG>/config.yaml
```
Expect: model set, `busy_ack_enabled: false`, `tool_progress: off`, `restart_drain_timeout: 20`,
`dispatch_in_gateway: false`.
