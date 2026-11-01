# Telegram Inline Video Bot

Production-ready inline Telegram bot для скачивания видео с TikTok и YouTube Shorts.

## Особенности

- **Только inline-режим**: бот работает через `@bot_username` в любом чате
- **Простота**: минимум зависимостей, flat-структура, без over-engineering
- **Надёжность**: тройная проверка размера файла, TTL-кэш, автоочистка временных файлов
- **Кэш file_id**: повторные запросы одного и того же видео возвращаются мгновенно
- **Типизация**: полный type hints для Python 3.12+

## Требования

- Python 3.12+
- ffmpeg (обязательно для yt-dlp)
- Ubuntu 24.04 (для production развёртывания)

## Установка

### 1. Установить ffmpeg

```bash
sudo apt update
sudo apt install -y ffmpeg
```

### 2. Клонировать репозиторий

```bash
git clone https://github.com/yourusername/telegram-inline-video-bot.git
cd telegram-inline-video-bot
```

### 3. Создать виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

### 5. Настроить переменные окружения

```bash
cp .env.example .env
nano .env  # или любой другой редактор
```

Заполнить в `.env`:

- `BOT_TOKEN`: получить через [@BotFather](https://t.me/BotFather)
- `ARCHIVE_CHAT_ID`: ID приватного канала, куда бот будет загружать видео
  - **Важно**: ID канала начинается с минуса, например: `-1001234567890`
  - **Как получить**: см. раздел "Как получить ARCHIVE_CHAT_ID" ниже
- `LOG_LEVEL`: уровень логирования (DEBUG, INFO, WARNING, ERROR)
- `CACHE_TTL`: время жизни кэша в секундах (по умолчанию 3600)

### 5.1. Как получить ARCHIVE_CHAT_ID

**Способ 1: Через команду `/chatid` в боте (рекомендуется)**

1. Создать приватный канал в Telegram
2. Запустить бота локально: `python -m bot`
3. Добавить бота в канал как администратора (с правом "Post messages")
4. Отправить в канал команду: `/chatid`
5. Бот ответит с ID канала (например: `-1001234567890`)
6. Скопировать ID в `.env`
7. Остановить бота: `Ctrl+C`

**Способ 2: Через @raw_data_bot**

1. Добавить [@raw_data_bot](https://t.me/raw_data_bot) в ваш приватный канал
2. Отправить любое сообщение в канал
3. Бот покажет JSON с `"chat":{"id":-1001234567890,...}`

**Способ 3: Через @getidsbot**

1. Добавить [@getidsbot](https://t.me/getidsbot) в канал
2. Бот автоматически отправит ID

**Важно:**
- ID канала **ВСЕГДА** начинается с минуса: `-1001234567890`
- ID личного чата (положительное число) НЕ подойдёт

### 6. Настроить бота в BotFather

**Обязательно** включить inline-режим:

```
/setinline @your_bot_username
```

Ввести текст placeholder (например: "Вставьте ссылку на TikTok или YouTube Shorts").

## Запуск

### Локально (для разработки)

```bash
python -m bot
```

### Production (Ubuntu 24.04 с systemd)

**Полная инструкция в [DEPLOY.md](DEPLOY.md)**

Краткая версия:

```bash
# Установка зависимостей
sudo apt update && sudo apt install -y python3.12 python3.12-venv ffmpeg git

# Создать пользователя
sudo useradd -r -m -d /home/botuser -s /bin/bash botuser

# Клонировать проект (замените yourusername и vi_bot на свои)
sudo -u botuser git clone https://github.com/yourusername/telegram-inline-video-bot.git /home/botuser/vi_bot

# Установить зависимости
sudo -u botuser bash -c "cd /home/botuser/vi_bot && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

# Создать .env
sudo -u botuser nano /home/botuser/vi_bot/.env

# Получить ARCHIVE_CHAT_ID (временно запустить бота)
sudo -u botuser bash -c "cd /home/botuser/vi_bot && venv/bin/python -m bot"
# Отправить /chatid в канал, скопировать ID, остановить (Ctrl+C)

# Отредактировать пути в service-файле
sudo nano /home/botuser/vi_bot/deploy/telegram-bot.service
# Изменить WorkingDirectory и ExecStart на /home/botuser/vi_bot

# Установить service
sudo cp /home/botuser/vi_bot/deploy/telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

## Использование

1. Открыть любой чат в Telegram
2. Ввести `@your_bot_username https://www.tiktok.com/@user/video/123456`
3. Выбрать результат из списка
4. Видео будет отправлено от вашего имени в чат

Поддерживаемые платформы:
- TikTok: `https://www.tiktok.com/...`
- YouTube Shorts: `https://youtube.com/shorts/...` или `https://youtu.be/...`

## Архитектура

### Пайплайн обработки inline-запроса

1. Получить `InlineQuery`
2. Извлечь URL регулярным выражением
3. Проверить кэш file_id по нормализованному URL
4. Если в кэше — вернуть `InlineQueryResultCachedVideo` (мгновенно)
5. Если нет:
   - **Проверка 1**: извлечь метаданные (без скачивания) через yt-dlp, проверить filesize <= 45 МБ
   - **Проверка 2**: скачать с `max_filesize=50MB` в yt-dlp
   - **Проверка 3**: проверить фактический размер файла на диске
   - Загрузить в архивный чат через `bot.send_video`
   - Получить `file_id` из ответа
   - Сохранить `file_id` в кэш с TTL
   - Удалить временную директорию
   - Вернуть `InlineQueryResultCachedVideo`

### Почему InlineQueryResultCachedVideo?

После первой загрузки видео в Telegram мы получаем `file_id`, который позволяет:
- Повторно отправлять видео без повторной загрузки
- Избежать лимитов на размер при отправке (Telegram уже знает файл)
- Мгновенно отвечать на повторные запросы

### Три рубежа проверки размера

1. **Метаданные** (до скачивания): быстрая проверка filesize/filesize_approx из formats. Блокирует заведомо большие файлы.
2. **yt-dlp max_filesize**: страховка на уровне загрузчика, прерывает скачивание при превышении.
3. **Фактический размер на диске**: финальная проверка перед отправкой в Telegram (API-лимит 50 МБ).

### Почему dict с TTL, а не SQLite?

- Кэш эфемерный — при рестарте бота ничего критичного не теряется
- SQLite — overkill для простого key-value с TTL
- In-memory dict — 0 зависимостей, быстрее, проще код

### Гарантия удаления временной директории

```python
try:
    video_path = await download_video(url)
    tmp_dir = video_path.parent
    # ... upload ...
finally:
    if tmp_dir:
        cleanup_temp_dir(tmp_dir)  # shutil.rmtree(ignore_errors=True)
```

Блок `finally` выполняется даже при исключениях.

### Что такое "архивный чат"?

**Архивный чат** — это приватный канал, куда бот загружает видео для получения `file_id`.

**Зачем это нужно:**
- Telegram Bot API не позволяет напрямую отправлять видео по URL в inline-результатах
- Нужно сначала загрузить видео в Telegram, получить `file_id`
- С `file_id` можно отправлять видео мгновенно и многократно
- Локальный файл удаляется сразу после загрузки
- Видео в архивном канале остаётся (можно удалить вручную при необходимости)

**Как работает:**
1. Бот скачивает видео на сервер
2. Отправляет в архивный канал → получает `file_id`
3. Удаляет локальный файл
4. Сохраняет `file_id` в кэш
5. Повторные запросы используют `file_id` без скачивания

## FAQ

**Q: Удаляются ли видео из архивного канала автоматически?**  
A: Нет, видео остаются в канале. Можно удалять вручную или оставить (они не занимают место на сервере).

**Q: Можно ли использовать группу вместо канала?**  
A: Да, но приватный канал предпочтительнее (меньше уведомлений, проще управление).

**Q: Почему @userinfobot показывает не тот ID?**  
A: @userinfobot показывает ID отправителя, не канала. Используйте команду `/chatid` в боте или @raw_data_bot.

**Q: Можно ли скачивать видео больше 50 МБ?**  
A: Нет, это жёсткий лимит Telegram Bot API для `send_video`. Бот блокирует такие видео до скачивания.

**Q: Работает ли бот с приватными видео?**  
A: Нет, yt-dlp не может скачивать видео, требующие авторизации.

## Ограничения

- **Лимит размера**: 50 МБ (жёсткий лимит Telegram Bot API для `send_video`)
- **Приватные видео**: не скачиваются (требуется авторизация)
- **Гео-блок**: видео, недоступные в регионе сервера, не скачиваются
- **Cookies**: в редких случаях TikTok/YouTube могут требовать cookies (не реализовано)

## Известные проблемы

- Если видео удалено или скрыто — yt-dlp вернёт ошибку
- TikTok периодически блокирует автоматические запросы (rate limit)
- YouTube Shorts без метаданных о размере оцениваются по битрейту (~1.2 Мбит/с)

## Разработка

### Проверка кода

```bash
pip install ruff
ruff check .
```

### Тестовый импорт

```bash
python -c "import bot"
```

### CI (GitHub Actions)

Файл `.github/workflows/ci.yml` автоматически запускается при push/PR:
- Устанавливает зависимости
- Проверяет код через `ruff check`
- Тестирует импорт модуля

## Git и GitHub

### Инициализация репозитория

```bash
git init
git add .
git commit -m "Initial commit: production-ready inline video bot"
```

### Создание репозитория на GitHub

```bash
# Создать репозиторий на github.com через веб-интерфейс, затем:
git remote add origin https://github.com/yourusername/telegram-inline-video-bot.git
git branch -M main
git push -u origin main
```

## Лицензия

MIT

## Автор

Ваше имя / GitHub username
