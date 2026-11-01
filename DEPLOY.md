# Инструкция по развёртыванию бота на Ubuntu 24.04

Пошаговое руководство по установке и запуску Telegram inline video бота на чистом сервере Ubuntu 24.04.

## Предварительные требования

- Сервер с Ubuntu 24.04
- Sudo-доступ
- Интернет-соединение
- Токен бота от [@BotFather](https://t.me/BotFather)
- ID архивного чата (получить через [@userinfobot](https://t.me/userinfobot))

---

## 1. Подготовка сервера

### Обновить систему
```bash
sudo apt update
sudo apt upgrade -y
```

### Установить необходимые пакеты
```bash
sudo apt install -y python3.12 python3.12-venv python3-pip ffmpeg git
```

Проверить версии:
```bash
python3 --version  # Должно быть >= 3.12
ffmpeg -version    # Проверить наличие
```

---

## 2. Создание пользователя для бота

```bash
# Создать системного пользователя без возможности логина
sudo useradd -r -m -d /home/botuser -s /bin/bash botuser

# Переключиться на этого пользователя (опционально для проверки)
sudo -i -u botuser
```

---

## 3. Клонирование проекта

**Важно:** Можно использовать любое имя директории. В примерах ниже используется `vi_bot` для краткости, но вы можете назвать её как угодно.

```bash
# Клонировать репозиторий (замените yourusername на ваш GitHub username)
sudo -u botuser git clone https://github.com/yourusername/telegram-inline-video-bot.git /home/botuser/vi_bot
```

Или можно переключиться на botuser:
```bash
sudo -i -u botuser
cd ~
git clone https://github.com/yourusername/telegram-inline-video-bot.git vi_bot
cd vi_bot
exit
```

---

## 4. Установка зависимостей

```bash
# Создать виртуальное окружение
sudo -u botuser python3 -m venv /home/botuser/vi_bot/venv

# Установить зависимости
sudo -u botuser bash -c "
    cd /home/botuser/vi_bot
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
"
```

Проверить установку:
```bash
sudo -u botuser bash -c "cd /home/botuser/vi_bot && venv/bin/python -c 'import bot; print(\"OK\")'"
```

Должно вывести: `OK`

---

## 5. Настройка переменных окружения

### Создать .env файл
```bash
sudo -u botuser nano /home/botuser/vi_bot/.env
```

### Заполнить следующие переменные:
```env
# Токен от @BotFather
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789

# ID чата для хранения видео (приватный канал, куда бот добавлен как админ)
# ВАЖНО: ID канала начинается с минуса, например: -1001234567890
ARCHIVE_CHAT_ID=-1001234567890

# Уровень логирования
LOG_LEVEL=INFO

# TTL кэша в секундах (1 час по умолчанию)
CACHE_TTL=3600
```

Сохранить: `Ctrl+O`, `Enter`, `Ctrl+X`

### Проверить права доступа
```bash
sudo chmod 600 /home/botuser/vi_bot/.env
sudo chown botuser:botuser /home/botuser/vi_bot/.env
```

---

## 5.1. Как получить ARCHIVE_CHAT_ID

**Способ 1: Через команду `/chatid` в боте (рекомендуется)**

1. Запустить бота временно:
   ```bash
   sudo -u botuser bash -c "cd /home/botuser/vi_bot && venv/bin/python -m bot"
   ```

2. Создать приватный канал в Telegram

3. Добавить бота в канал как администратора (с правом "Post messages")

4. Отправить в канал команду: `/chatid`

5. Бот ответит с ID канала:
   ```
   📋 Chat Info:
   
   ID: -1001234567890
   Type: channel
   Title: My Archive Channel
   
   Use this ID as ARCHIVE_CHAT_ID in .env
   ```

6. Скопировать ID (с минусом!) в .env

7. Остановить временный запуск: `Ctrl+C`

**Способ 2: Через @raw_data_bot**

1. Добавить [@raw_data_bot](https://t.me/raw_data_bot) в ваш приватный канал как администратора
2. Отправить любое сообщение в канал
3. Бот покажет JSON, найти `"chat":{"id":-1001234567890,...}`
4. Скопировать значение `id`

**Способ 3: Через @getidsbot**

1. Добавить [@getidsbot](https://t.me/getidsbot) в канал
2. Бот автоматически отправит ID

**Важно:**
- ID канала **ВСЕГДА** начинается с минуса: `-1001234567890`
- ID личного чата — положительное число (это НЕ то, что нужно!)
- Бот должен быть администратором канала с правом "Post messages"

---

## 6. Настройка бота в BotFather

**Обязательно** включить inline-режим:

1. Открыть [@BotFather](https://t.me/BotFather)
2. Отправить `/setinline`
3. Выбрать вашего бота
4. Ввести placeholder текст (например: `Вставьте ссылку на TikTok или YouTube Shorts`)

---

## 7. Тестовый запуск

Проверить, что бот запускается без ошибок:

```bash
sudo -u botuser bash -c "cd /home/botuser/vi_bot && venv/bin/python -m bot"
```

Если всё ОК, вы увидите:
```
2026-11-02 21:08:50 [INFO] bot.__main__: Starting bot...
2026-11-02 21:08:51 [INFO] bot.__main__: Bot started, waiting for inline queries...
```

Остановить тестовый запуск: **Ctrl+C**

**Типичные ошибки на этом этапе:**

1. **`No module named bot`** — забыли перейти в директорию проекта (`cd /home/botuser/vi_bot`)
2. **`BOT_TOKEN not set`** — не создан файл `.env` или токен не указан
3. **`ARCHIVE_CHAT_ID not set`** — не указан ID канала в `.env`

---

## 8. Установка systemd service

### Отредактировать service-файл под вашу директорию

Если вы используете имя директории отличное от `telegram-inline-video-bot`, нужно отредактировать service-файл:

```bash
sudo nano /home/botuser/vi_bot/deploy/telegram-bot.service
```

Изменить пути в секции `[Service]`:
```ini
[Service]
WorkingDirectory=/home/botuser/vi_bot
Environment="PATH=/home/botuser/vi_bot/venv/bin"
ExecStart=/home/botuser/vi_bot/venv/bin/python -m bot
```

Сохранить: `Ctrl+O`, `Enter`, `Ctrl+X`

### Скопировать service-файл
```bash
sudo cp /home/botuser/vi_bot/deploy/telegram-bot.service /etc/systemd/system/
```

### Перезагрузить systemd
```bash
sudo systemctl daemon-reload
```

### Включить автозапуск при загрузке
```bash
sudo systemctl enable telegram-bot
```

### Запустить бота
```bash
sudo systemctl start telegram-bot
```

### Проверить статус
```bash
sudo systemctl status telegram-bot
```

Должно быть:
```
● telegram-bot.service - Telegram Inline Video Bot
     Loaded: loaded (/etc/systemd/system/telegram-bot.service; enabled; ...)
     Active: active (running) since ...
```

Если статус `failed`, смотрите логи:
```bash
sudo journalctl -u telegram-bot -n 50
```

---

## 9. Мониторинг логов

### Смотреть логи в реальном времени
```bash
sudo journalctl -u telegram-bot -f
```

### Показать последние 100 строк
```bash
sudo journalctl -u telegram-bot -n 100
```

### Логи за последний час
```bash
sudo journalctl -u telegram-bot --since "1 hour ago"
```

### Логи с ошибками
```bash
sudo journalctl -u telegram-bot -p err
```

---

## 10. Управление ботом

### Остановить бота
```bash
sudo systemctl stop telegram-bot
```

### Перезапустить бота
```bash
sudo systemctl restart telegram-bot
```

### Отключить автозапуск
```bash
sudo systemctl disable telegram-bot
```

### Посмотреть статус
```bash
sudo systemctl status telegram-bot
```

---

## 11. Обновление бота

Когда вы пушите новый код в GitHub и хотите обновить бота на сервере:

```bash
# Получить изменения и обновить зависимости
sudo -u botuser bash -c "cd /home/botuser/vi_bot && git pull && source venv/bin/activate && pip install -r requirements.txt"

# Перезапустить бота
sudo systemctl restart telegram-bot

# Проверить статус
sudo systemctl status telegram-bot

# Посмотреть логи
sudo journalctl -u telegram-bot -n 20
```

Или пошагово:
```bash
sudo -i -u botuser
cd ~/vi_bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
exit

sudo systemctl restart telegram-bot
sudo systemctl status telegram-bot
```

---

## 12. Проверка работы бота

1. Открыть любой чат в Telegram
2. Ввести: `@your_bot_username https://www.tiktok.com/@user/video/123456`
3. Выбрать результат из списка
4. Видео должно отправиться в чат

---

## 13. Решение проблем

### Бот не запускается

**Проверить логи:**
```bash
sudo journalctl -u telegram-bot -n 50
```

**Типичные ошибки:**

1. **"No module named bot"**
   - Проблема: команда запущена не из директории проекта
   - Решение: всегда используйте `cd /home/botuser/vi_bot` перед запуском
   - Правильно: `sudo -u botuser bash -c "cd /home/botuser/vi_bot && venv/bin/python -m bot"`
   - Неправильно: `sudo -u botuser /home/botuser/vi_bot/venv/bin/python -m bot`

2. **"BOT_TOKEN not set"**
   - Проверить `.env`: `sudo -u botuser cat /home/botuser/vi_bot/.env`
   - Убедиться, что токен скопирован без пробелов и кавычек

3. **"ARCHIVE_CHAT_ID not set" или "must be integer"**
   - Проверить `.env`: ID должен быть отрицательным числом: `-1001234567890`
   - ID личного чата (положительное число) НЕ подойдёт
   - Используйте команду `/chatid` в канале для получения правильного ID

4. **"ModuleNotFoundError: No module named 'aiogram'"**
   - Переустановить зависимости:
     ```bash
     sudo -u botuser bash -c "cd /home/botuser/vi_bot && source venv/bin/activate && pip install -r requirements.txt"
     ```

5. **"ffmpeg: not found"**
   - Установить: `sudo apt install -y ffmpeg`

6. **"Unauthorized" или "401 Unauthorized"**
   - Неверный BOT_TOKEN
   - Проверить токен в BotFather

### Бот запустился, но не отвечает

1. **Проверить, включён ли inline-режим:**
   - BotFather → `/setinline` → выбрать бота

2. **Проверить ARCHIVE_CHAT_ID:**
   - Бот должен быть администратором канала с правом "Post messages"
   - ID должен быть отрицательным числом (начинается с минуса): `-1001234567890`
   - Проверить: отправить `/chatid` в канал, где бот админ

3. **Проверить логи на ошибки:**
   ```bash
   sudo journalctl -u telegram-bot -f
   ```

### Видео не скачивается

**Проверить логи конкретного запроса:**
```bash
sudo journalctl -u telegram-bot | grep -A 10 "Processing.*URL"
```

**Типичные причины:**
- Видео больше 50 МБ (лимит Telegram)
- Приватное видео (требует авторизации)
- Гео-блок (видео недоступно в вашем регионе)
- Rate limit от TikTok/YouTube

---

## 14. Безопасность

### Настроить firewall (опционально)
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw status
```

### Ограничить доступ к .env
```bash
sudo chmod 600 /home/botuser/telegram-inline-video-bot/.env
```

### Регулярно обновлять систему
```bash
sudo apt update && sudo apt upgrade -y
```

---

## 15. Производительность

### Ограничение использования ресурсов в systemd

Отредактировать service-файл:
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Добавить в секцию `[Service]`:
```ini
# Ограничить CPU (50% одного ядра)
CPUQuota=50%

# Ограничить память (512 МБ)
MemoryMax=512M
MemoryHigh=400M
```

Применить:
```bash
sudo systemctl daemon-reload
sudo systemctl restart telegram-bot
```

---

## 16. Мониторинг ресурсов

### Проверить использование CPU/RAM
```bash
sudo systemctl status telegram-bot
```

### Детальная статистика
```bash
systemd-cgtop
```

Найти строку с `telegram-bot.service` для просмотра CPU/Memory usage.

---

## Краткая шпаргалка команд

**Замените `vi_bot` на имя вашей директории, если используете другое.**

```bash
# === УСТАНОВКА ===
sudo apt update && sudo apt install -y python3.12 python3.12-venv ffmpeg git
sudo useradd -r -m -d /home/botuser -s /bin/bash botuser
sudo -u botuser git clone https://github.com/yourusername/telegram-inline-video-bot.git /home/botuser/vi_bot
sudo -u botuser bash -c "cd /home/botuser/vi_bot && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

# Создать .env
sudo -u botuser nano /home/botuser/vi_bot/.env

# Получить ARCHIVE_CHAT_ID
sudo -u botuser bash -c "cd /home/botuser/vi_bot && venv/bin/python -m bot"
# Отправить /chatid в канал, скопировать ID, остановить бота (Ctrl+C)

# Отредактировать пути в service-файле
sudo nano /home/botuser/vi_bot/deploy/telegram-bot.service
# Изменить WorkingDirectory и ExecStart на /home/botuser/vi_bot

# Установить service
sudo cp /home/botuser/vi_bot/deploy/telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# === УПРАВЛЕНИЕ ===
sudo systemctl status telegram-bot      # Статус
sudo systemctl restart telegram-bot     # Перезапуск
sudo systemctl stop telegram-bot        # Остановка
sudo journalctl -u telegram-bot -f      # Логи в реальном времени
sudo journalctl -u telegram-bot -n 50   # Последние 50 строк логов

# === ОБНОВЛЕНИЕ ===
sudo -u botuser bash -c "cd /home/botuser/vi_bot && git pull && source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart telegram-bot
sudo systemctl status telegram-bot

# === ПРОВЕРКА ===
# Проверить импорт модуля
sudo -u botuser bash -c "cd /home/botuser/vi_bot && venv/bin/python -c 'import bot; print(\"OK\")'"

# Проверить .env
sudo -u botuser cat /home/botuser/vi_bot/.env

# Тестовый запуск
sudo -u botuser bash -c "cd /home/botuser/vi_bot && venv/bin/python -m bot"
```

---

## Готово! 🚀

Ваш бот запущен и работает в фоновом режиме. Проверьте его работу в любом Telegram-чате через `@your_bot_username`.
