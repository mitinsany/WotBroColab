# Troubleshooting (mod branch)

## Мод не загрузился
- Проверьте `python.log` по строкам `wot_telegram_notifier_current.wotmod`.
- Если есть `load error`, выполните `git pull` и запустите игру снова.

## Нет сообщений в Telegram
- Проверьте `mods/.env` и наличие `WOT_TG_BOT_TOKEN`, `WOT_TG_CHAT_ID`.
- Проверьте `logs/wot_tg_mod.log` по строкам `[WoT TG]`.

## Не найден .env
- Запустите: `powershell -ExecutionPolicy Bypass -File .\tools\bootstrap_mod.ps1`.
- Или вручную скопируйте `.env.example` в `mods/.env`.