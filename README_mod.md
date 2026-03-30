# WoT Telegram Notifier (mod branch)

Эта ветка для конечного пользователя: здесь только готовый мод и утилиты установки.

## Быстрый старт (2 команды)
```powershell
cd D:\GAMES\World_of_Tanks_EU
powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest https://raw.githubusercontent.com/mitinsany/WotBroColab/mod/tools/bootstrap_mod.ps1 -OutFile .\wot_tg_bootstrap.ps1; .\wot_tg_bootstrap.ps1; Remove-Item .\wot_tg_bootstrap.ps1 -Force"
```

После этого:
1. Заполните `mods/.env` (если создан пустой шаблон).
2. Запустите игру.

## Ежедневное обновление
```powershell
git pull
```

## Проверка обновления
- Мод сам проверяет новую версию по `gh-pages`.
- Если обновление доступно, уведомление появится в игре после логина.

## Где лежит мод
- `mods/2.2.0.2/wot_telegram_notifier_current.wotmod`

Подробности по ошибкам: `docs/TROUBLESHOOTING.md`.