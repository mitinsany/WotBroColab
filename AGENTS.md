# AGENTS.md

## Project
World of Tanks mod: Telegram notifier for game events (login/logout/battle start/battle end).

## Source of truth for active mod path
- Active `res_mods` version is defined in `paths.xml`.
- Confirmed active path:
  - `./res_mods/2.2.0.2`

## Deployment layout (current working setup)
- Mod entrypoint:
  - `D:\GAMES\World_of_Tanks\res_mods\2.2.0.2\scripts\client\gui\mods\mod_wot_telegram_notifier.pyc`
- Env file:
  - `D:\GAMES\World_of_Tanks\mods\.env`

## Runtime constraints
- Client runtime is Python 2 (see `python.log` markers like `Python2`).
- Keep compatibility with Python 2 syntax and stdlib:
  - no `dataclasses`
  - no Python 3-only `urllib.request` / type hints / f-strings
  - use `urllib`, `urllib2`, `Queue`

## Telegram config
Required in `.env`:
- `WOT_TG_BOT_TOKEN`
- `WOT_TG_CHAT_ID`

Optional:
- `WOT_TG_TIMEOUT_SECONDS` (default `3.0`)
- `WOT_TG_QUEUE_SIZE` (default `128`)

## Validation checklist
1. Launch game.
2. Check `D:\GAMES\World_of_Tanks\python.log` for `[WotBroColab]` messages.
3. Trigger events: login, logout, battle start, battle end.
4. Confirm messages arrive in Telegram.

## Notes
- If mod does not start, first re-check `paths.xml` and copy mod to the currently active `res_mods/<version>/scripts/client/gui/mods`.
- If token was exposed in logs/history, rotate token in BotFather and update `.env`.


