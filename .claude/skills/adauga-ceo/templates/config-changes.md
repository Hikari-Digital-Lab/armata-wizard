# Config for the CEO profile (`<SLUG>/config.yaml`)

The CEO is the **single free bot** and the foundation of the team. Because this is the FIRST
profile, there is no existing team config to copy — so this skill **ships** a verified config.

## 1. Apply the shipped config
`hermes profile create <SLUG> --clone` clones from `default` (which lacks the consolidated
anti-chatter `display` block). OVERWRITE the cloned config with the shipped one:

```
cp <skill>/templates/ceo.config.yaml <HERMES_HOME>/profiles/<SLUG>/config.yaml
```

`ceo.config.yaml` is a snapshot of a working CEO config and already contains:
- `model.default: gemini-3.5-flash` (the team brain model — change here if you picked another),
- `agent.restart_drain_timeout: 20`,
- the consolidated anti-chatter `display` block (`busy_ack_enabled: false`,
  `display.platforms.telegram` with `streaming/tool_progress/...` off),
- **`kanban.dispatch_in_gateway: false`** (no unsolicited proactive posts).

## 2. Gating is via `.env`, not config
The CEO is free because `.env` sets `TELEGRAM_REQUIRE_MENTION=false`. The config may carry
`require_mention: true` defaults in some sections — that's fine; the `.env` value governs Telegram
behavior (this is exactly how the current Michael runs).

## 3. Change the brain model (optional)
If you chose a different model, edit `model.default` (and `model.provider` if needed) in
`<HERMES_HOME>/profiles/<SLUG>/config.yaml`.

## 4. Verify
```
grep -nE 'default:|busy_ack_enabled|tool_progress: off|restart_drain|dispatch_in_gateway' \
  <HERMES_HOME>/profiles/<SLUG>/config.yaml
```
Expect: brain model set, `busy_ack_enabled: false`, `tool_progress: off`,
`restart_drain_timeout: 20`, `dispatch_in_gateway: false`.
