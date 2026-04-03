# Troubleshooting

## Мод не загрузился
- Проверьте `<GAME_ROOT>/python.log` по строкам `[WotBroColab]`.
- Убедитесь, что существуют файлы:
  - `res_mods/<active_version>/scripts/client/gui/mods/mod_wot_telegram_notifier.pyc`
- Перезапустите установку: `powershell -ExecutionPolicy Bypass -File .\scripts\install_or_update.ps1`.

## Нет сообщений в Telegram
- Проверьте наличие `<GAME_ROOT>/mods/wot_bro_colab.ini`.
- Убедитесь, что в `wot_bro_colab.ini` заполнены `WOT_TG_BOT_TOKEN` и `WOT_TG_CHAT_ID`.
- Проверьте `<GAME_ROOT>/logs/wot_tg_mod.log` по маркеру `[WotBroColab]`.

## Не найден wot_bro_colab.ini
- Создайте `<GAME_ROOT>/mods/wot_bro_colab.ini` на основе `wot_bro_colab.ini.example`.
- Не размещайте `wot_bro_colab.ini` внутри версии (`mods/2.2.0.2/`) — используйте только корень `mods`.

