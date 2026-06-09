# Config changes for the artist profile (`<SLUG>/config.yaml`)

The artist is a **gated, reactive image worker**. Build its `config.yaml` like this:

## 1. Start from a known-good team config (anti-chatter already verified)
`hermes profile create <SLUG> --clone` clones from `default`, whose `config.yaml` does NOT have
the consolidated anti-chatter `display` block. So OVERWRITE it with a team config that does:

- **Preferred source:** an existing **gated worker** (e.g. another artist/copywriter) — already
  gated and anti-chatter-clean:
  `cp <HERMES_HOME>/profiles/<GATED_WORKER>/config.yaml <HERMES_HOME>/profiles/<SLUG>/config.yaml`
- **Fallback:** the **CEO** config (always exists). If you copy the CEO config, keep the worker
  gated (see step 3).

The good `display` block (already in the team's configs):
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
Also `agent.restart_drain_timeout: 20` and `model.default: <TEAM_BRAIN_MODEL>` (e.g. gemini-3.5-flash).

## 2. Disable the kanban dispatcher (anti-chatter)
The artist has no kanban board and must never post unsolicited messages. Set:
```yaml
kanban:
  dispatch_in_gateway: false
```
This (with the `.env` home-channel keys) prevents the `📬 No home channel` notice.

## 3. Keep it gated
Gating is enforced by `.env` (`TELEGRAM_REQUIRE_MENTION=true`). If you copied the CEO's config
(CEO is free), make sure nothing in `config.yaml` forces `require_mention: false` — the `.env`
value must win and the worker must stay gated.

## 4. Image model
The chat/brain model is `model.default` (e.g. gemini-3.5-flash). The IMAGE model is handled by
`gen_image.py` (default `gemini-3-pro-image`); override per-profile with `GEN_IMAGE_MODEL` in
`.env` if needed. No config.yaml change is required for the image model.

## 5. Verify
```
grep -nE 'default:|busy_ack_enabled|tool_progress: off|restart_drain|dispatch_in_gateway' \
  <HERMES_HOME>/profiles/<SLUG>/config.yaml
```
Expect: brain model set, `busy_ack_enabled: false`, `tool_progress: off`,
`restart_drain_timeout: 20`, `dispatch_in_gateway: false`.
