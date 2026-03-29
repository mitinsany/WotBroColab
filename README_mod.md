# WoT Telegram Notifier - mod branch

Эта ветка содержит только готовый файл мода для прямого обновления в папке игры.

## Обновление
```powershell
git pull
```

После `git pull` файл мода будет обновлен по пути:
- `mods/2.2.0.2/wot_telegram_notifier_current.wotmod`

## Создание .env
Создайте файл `mods/.env` (в корне папки `mods`, не внутри версии) со следующим содержимым:

```dotenv
# Required
WOT_TG_BOT_TOKEN=PASTE_YOUR_BOT_TOKEN
WOT_TG_CHAT_ID=PASTE_YOUR_CHAT_ID

# Optional
WOT_TG_TIMEOUT_SECONDS=3.0
WOT_TG_QUEUE_SIZE=128
```