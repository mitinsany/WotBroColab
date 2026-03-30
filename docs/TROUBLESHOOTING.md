# Troubleshooting (mod branch)

## Мод не загрузился
- Проверьте `python.log` по строкам `[WoT TG]`.
- Проверьте, что присутствуют оба runtime-файла:
  - `res_mods/<active_version>/scripts/client/gui/mods/mod_wot_telegram_notifier.pyc`
  - `res_mods/<active_version>/scripts/client/mods/mod_wot_telegram_notifier.pyc`
- Выполните `git pull` и запустите игру снова.

## Нет Telegram-сообщений по событиям
- Проверьте `mods/.env` и значения `WOT_TG_BOT_TOKEN`, `WOT_TG_CHAT_ID`.
- Проверьте `logs/wot_tg_mod.log` по строкам `[WoT TG]`.

## Нет уведомления об обновлении
- Уведомление о новой версии показывается в игре после логина.
- Если нужно проверить вручную, обновите ветку командой `git pull`.

## Не найден .env
- Запустите: `powershell -ExecutionPolicy Bypass -File .\tools\bootstrap_mod.ps1`.
- Или вручную скопируйте `.env.example` в `mods/.env`.
