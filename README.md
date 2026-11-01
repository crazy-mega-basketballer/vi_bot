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
- `ARCHIVE_CHAT_ID`: ID приватного канала или чата, куда бот будет загружать видео (получить через [@userinfobot](https://t.me/userinfobot))
- `LOG_LEVEL`: уровень логирования (DEBUG, INFO, WARNING, ERROR)
- `CACHE_TTL`: время жизни кэша в секундах (по умолчанию 3600)

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

#### 1. Создать пользователя

```bash
sudo useradd -r -m -d /home/botuser -s /bin/bash botuser
```

#### 2. Скопировать файлы

```bash
sudo cp -r . /home/botuser/telegram-inline-video-bot
sudo chown -R botuser:botuser /home/botuser/telegram-inline-video-bot
```

#### 3. Установить виртуальное окружение

```bash
sudo -u botuser bash
cd /home/botuser/telegram-inline-video-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
exit
```

#### 4. Настроить .env

```bash
sudo -u botuser nano /home/botuser/telegram-inline-video-bot/.env
```

#### 5. Установить systemd service

```bash
sudo cp deploy/telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

#### 6. Проверить статус

```bash
sudo systemctl status telegram-bot
sudo journalctl -u telegram-bot -f
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
