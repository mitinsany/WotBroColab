# Troubleshooting (mod branch)

## Мод не загрузился
- Проверьте `python.log` по строкам `[WotBroColab]`.
- Проверьте, что присутствует runtime-файл:
  - `res_mods/<active_version>/scripts/client/gui/mods/mod_wot_telegram_notifier.pyc`
- Выполните `git pull` и запустите игру снова.

## Нет Telegram-сообщений по событиям
- Проверьте `mods/wot_bro_colab.ini` и значения `WOT_TG_BOT_TOKEN`, `WOT_TG_CHAT_ID`.
- Проверьте `logs/wot_tg_mod.log` по строкам `[WotBroColab]`.

## Нет уведомления об обновлении
- Уведомление о новой версии показывается в игре после логина.
- Если нужно проверить вручную, обновите ветку командой `git pull`.

## Не найден wot_bro_colab.ini
- Запустите: `powershell -ExecutionPolicy Bypass -File .\tools\bootstrap_mod.ps1`.
- Или вручную скопируйте `wot_bro_colab.ini.example` в `mods/wot_bro_colab.ini`.
