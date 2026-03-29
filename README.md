# WoT Telegram Notifier (Python 2)

Репозиторий для разработки и деплоя мода-уведомителя Telegram.

## Ветки репозитория
- `build` — исходники, тесты, скрипты сборки/обновления.
- `mod` — только готовый деплой-артефакт для папки игры.

На целевой машине используется ветка `mod`: обычный `git pull` обновляет файл мода в `mods/<version>/...`.

## Что делает мод
Отправляет в Telegram события клиента WoT:
- вход в игру
- выход из игры
- начало боя
- завершение боя

## Требования среды
- Клиент WoT (runtime Python 2)
- PowerShell 5+
- Рабочий `.env` в `D:\GAMES\World_of_Tanks_EU\mods\<version>\.env`

Обязательные переменные:
- `WOT_TG_BOT_TOKEN`
- `WOT_TG_CHAT_ID`

Опциональные:
- `WOT_TG_TIMEOUT_SECONDS` (по умолчанию `3.0`)
- `WOT_TG_QUEUE_SIZE` (по умолчанию `128`)

## Исходники и упаковка
- Исходник entrypoint: `res_mods/mods/mod_wot_telegram_notifier.py`
- Шаблон meta: `packaging/meta.xml`
- Сборка: `build/*.wotmod`

## Скрипты
- `scripts/build_wotmod.ps1`
  - Воспроизводимо собирает `.wotmod` из репозитория.
  - По умолчанию результат: `build/wot_telegram_notifier_current.wotmod`.

- `scripts/install_or_update.ps1`
  - Читает активную версию из `D:\GAMES\World_of_Tanks_EU\paths.xml`.
  - Копирует исходник в активный `res_mods/<version>/scripts/client/gui/mods`.
  - Собирает `.wotmod` и кладет в `mods/<version>/wot_telegram_notifier_current.wotmod`.

- `scripts/clean_res_mods.ps1`
  - Удаляет наши временные/тестовые артефакты (`*.pyc`, `*_test*`, `*_debug*`) в активном `res_mods`.

## Быстрый цикл работы
```powershell
# из корня репозитория
powershell -ExecutionPolicy Bypass -File .\scripts\install_or_update.ps1
```

## Релиз в ветку mod
1. Работать в ветке `build`.
2. Собрать пакет: `powershell -ExecutionPolicy Bypass -File .\scripts\build_wotmod.ps1`.
3. Обновить файл `mods/<version>/wot_telegram_notifier_current.wotmod` в ветке `mod`.
4. На игровой машине (ветка `mod`) выполнить `git pull`.

## Только сборка пакета
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_wotmod.ps1
```

## Очистка res_mods
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\clean_res_mods.ps1
```

## Проверка после установки
1. Запустить игру.
2. Проверить `D:\GAMES\World_of_Tanks_EU\python.log` по маркеру `[WoT TG]`.
3. Проверить события: login/logout/battle start/battle end.
4. Убедиться, что сообщения пришли в Telegram.

## Безопасность
Если токен бота попал в логи/историю команд, его нужно перевыпустить в BotFather и обновить `.env`.