# Config changes for the web-developer profile (`<SLUG>/config.yaml`)

The web developer is a **gated, purely-reactive worker** that writes files (HTML) and reads
images. Build its `config.yaml` like this:

## 1. Start from a known-good team config (anti-chatter already verified)
`hermes profile create <SLUG> --clone` clones from `default`, whose `config.yaml` does NOT have
the consolidated anti-chatter `display` block. So OVERWRITE it with a config that does:

- **Preferred source:** an existing **gated worker** in the team (e.g. the copywriter or artist) —
  it is already gated and anti-chatter-clean:
  `cp <HERMES_HOME>/profiles/<EXISTING_WORKER>/config.yaml <HERMES_HOME>/profiles/<SLUG>/config.yaml`
- **Fallback:** the **CEO** config (always exists). If you copy the CEO's config, make sure the
  worker stays gated (see step 3).

The good `display` block (already present in the team's configs) is:
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
And `agent.restart_drain_timeout: 20`, `model.default: <TEAM_MODEL>` (e.g. gemini-3.5-flash).

## 2. Disable the kanban dispatcher (anti-chatter)
The developer has no kanban board and must never post unsolicited messages. Set:
```yaml
kanban:
  dispatch_in_gateway: false
```
This (together with the `.env` home-channel keys) prevents the `📬 No home channel` notice.

## 3. Keep it gated
Gating is enforced by the `.env` (`TELEGRAM_REQUIRE_MENTION=true`). If you copied the CEO's config
(CEO is free), make sure nothing in `config.yaml` forces `require_mention: false` — the `.env`
value must win and the worker must stay gated.

## 4. File tools must be available
The developer WRITES `index.html` and READS the spec + images. The default `hermes-cli` toolset
already includes file-read/file-write/terminal — do NOT disable them. (No image generation: the
developer is NOT an artist — do not add `gen_image.py` / an `image-studio` skill.)

## 5. Verify
```
grep -nE 'default:|busy_ack_enabled|tool_progress: off|restart_drain|dispatch_in_gateway' \
  <HERMES_HOME>/profiles/<SLUG>/config.yaml
```
Expect: model set, `busy_ack_enabled: false`, `tool_progress: off`, `restart_drain_timeout: 20`,
`dispatch_in_gateway: false`.
