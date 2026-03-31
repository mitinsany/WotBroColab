# Troubleshooting

## Мод не загрузился
- Проверьте `D:\GAMES\World_of_Tanks_EU\python.log` по строкам `[WotBroColab]`.
- Убедитесь, что существуют файлы:
  - `res_mods/<active_version>/scripts/client/gui/mods/mod_wot_telegram_notifier.pyc`
- Перезапустите установку: `powershell -ExecutionPolicy Bypass -File .\scripts\install_or_update.ps1`.

## Нет сообщений в Telegram
- Проверьте наличие `D:\GAMES\World_of_Tanks_EU\mods\.env`.
- Убедитесь, что в `.env` заполнены `WOT_TG_BOT_TOKEN` и `WOT_TG_CHAT_ID`.
- Проверьте `D:\GAMES\World_of_Tanks_EU\logs\wot_tg_mod.log` по маркеру `[WotBroColab]`.

## Не найден .env
- Создайте `D:\GAMES\World_of_Tanks_EU\mods\.env` на основе `.env.example`.
- Не размещайте `.env` внутри версии (`mods/2.2.0.2/.env`) — используйте только корень `mods`.

