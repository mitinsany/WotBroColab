# Troubleshooting

## Мод не загрузился
- Проверьте `D:\GAMES\World_of_Tanks_EU\python.log` по строкам `wot_telegram_notifier_current.wotmod`.
- Если есть `compression not supported`, пересоберите мод через `scripts/build_wotmod.ps1` и обновите артефакт в `mod`.
- Убедитесь, что файл лежит в `mods/<active_version>/wot_telegram_notifier_current.wotmod`.

## Нет сообщений в Telegram
- Проверьте наличие `D:\GAMES\World_of_Tanks_EU\mods\.env`.
- Убедитесь, что в `.env` заполнены `WOT_TG_BOT_TOKEN` и `WOT_TG_CHAT_ID`.
- Проверьте `D:\GAMES\World_of_Tanks_EU\logs\wot_tg_mod.log` по маркеру `[WoT TG]`.

## Не найден .env
- Создайте `D:\GAMES\World_of_Tanks_EU\mods\.env` на основе `.env.example`.
- Не размещайте `.env` внутри версии (`mods/2.2.0.2/.env`) — используйте только корень `mods`.