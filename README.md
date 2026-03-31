# WoT Telegram Notifier (build branch)

Эта ветка предназначена для разработки и выпуска релизов.

## Branch model
- `build`: исходники, тесты, build/release скрипты.
- `mod`: пользовательская ветка с runtime `.pyc` для `git pull`.
- `gh-pages`: публичная страница версии и короткого changelog.

## Development essentials
- Runtime WoT: Python 2.
- Основной исходник: `res_mods/mods/mod_wot_telegram_notifier.py`.
- Env у пользователя: `D:\GAMES\World_of_Tanks_EU\mods\.env`.

## Release source of truth
- `packaging/meta.xml` -> версия мода.
- `release/version.json` -> публичная версия/канал/путь артефакта.
- `release/CHANGELOG_SHORT.md` -> короткие изменения для страницы версии.

## Standard release flow
1. Обновить код в `build`.
2. Собрать runtime `.pyc`: `powershell -ExecutionPolicy Bypass -File .\scripts\build_wotmod.ps1`.
3. Обновить метаданные: `powershell -ExecutionPolicy Bypass -File .\scripts\update_release_version.ps1 -WotVersion <x.y.z.w> -ChangelogShort "..."`.
4. Перенести новый runtime `.pyc` в `res_mods/<version>/scripts/client/gui/mods/` ветки `mod`.
5. Обновить `gh-pages` (`version.json` + `index.html`).

## Validation
- Запуск игры, проверка `[WotBroColab]` в `python.log`.
- События: login/logout/battle start/battle end.
- Сообщения дошли в Telegram.

## Support docs
- Пользовательская инструкция: `README_mod.md` (в ветке `mod`).
- Типовые проблемы: `TROUBLESHOOTING.md`.

