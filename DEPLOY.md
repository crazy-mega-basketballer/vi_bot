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

```bash
# Переключиться на botuser
sudo -i -u botuser

# Клонировать репозиторий
cd /home/botuser
git clone https://github.com/yourusername/telegram-inline-video-bot.git
cd telegram-inline-video-bot

# Выйти из botuser
exit
```

Или одной командой без переключения:
```bash
sudo -u botuser git clone https://github.com/yourusername/telegram-inline-video-bot.git /home/botuser/telegram-inline-video-bot
```

---

## 4. Установка зависимостей

```bash
# Создать виртуальное окружение
sudo -u botuser python3 -m venv /home/botuser/telegram-inline-video-bot/venv

# Активировать venv и установить зависимости
sudo -u botuser bash -c "
    cd /home/botuser/telegram-inline-video-bot
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
"
```

Проверить установку:
```bash
sudo -u botuser /home/botuser/telegram-inline-video-bot/venv/bin/python -c "import bot; print('OK')"
```

---

## 5. Настройка переменных окружения

### Создать .env файл
```bash
sudo -u botuser nano /home/botuser/telegram-inline-video-bot/.env
```

### Заполнить следующие переменные:
```env
# Токен от @BotFather
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789

# ID чата для хранения видео (приватный канал или чат, куда бот добавлен как админ)
# Получить: создать приватный канал, добавить бота как администратора,
# переслать любое сообщение из канала в @userinfobot
ARCHIVE_CHAT_ID=-1001234567890

# Уровень логирования
LOG_LEVEL=INFO

# TTL кэша в секундах (1 час по умолчанию)
CACHE_TTL=3600
```

Сохранить (Ctrl+O, Enter, Ctrl+X).

### Проверить права доступа
```bash
sudo chmod 600 /home/botuser/telegram-inline-video-bot/.env
sudo chown botuser:botuser /home/botuser/telegram-inline-video-bot/.env
```

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
sudo -u botuser /home/botuser/telegram-inline-video-bot/venv/bin/python -m bot
```

Если всё ОК, вы увидите:
```
2026-11-01 20:21:50 [INFO] bot.__main__: Starting bot...
2026-11-01 20:21:51 [INFO] bot.__main__: Bot started, waiting for inline queries...
```

Остановить тестовый запуск: **Ctrl+C**

---

## 8. Установка systemd service

### Скопировать service-файл
```bash
sudo cp /home/botuser/telegram-inline-video-bot/deploy/telegram-bot.service /etc/systemd/system/
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
# Переключиться на botuser
sudo -u botuser bash

# Перейти в директорию проекта
cd /home/botuser/telegram-inline-video-bot

# Получить изменения
git pull origin main

# Обновить зависимости (если изменился requirements.txt)
source venv/bin/activate
pip install -r requirements.txt

# Выйти из botuser
exit

# Перезапустить бота
sudo systemctl restart telegram-bot

# Проверить статус
sudo systemctl status telegram-bot
```

Или одной командой:
```bash
sudo -u botuser bash -c "cd /home/botuser/telegram-inline-video-bot && git pull && source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart telegram-bot
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

1. **"BOT_TOKEN not set"**
   - Проверить `.env`: `sudo -u botuser cat /home/botuser/telegram-inline-video-bot/.env`
   - Убедиться, что токен скопирован без пробелов

2. **"ARCHIVE_CHAT_ID not set"**
   - Создать приватный канал
   - Добавить бота как администратора
   - Получить ID через @userinfobot

3. **"ModuleNotFoundError: No module named 'aiogram'"**
   - Переустановить зависимости:
     ```bash
     sudo -u botuser bash -c "cd /home/botuser/telegram-inline-video-bot && source venv/bin/activate && pip install -r requirements.txt"
     ```

4. **"ffmpeg: not found"**
   - Установить: `sudo apt install -y ffmpeg`

### Бот запустился, но не отвечает

1. **Проверить, включён ли inline-режим:**
   - BotFather → `/setinline` → выбрать бота

2. **Проверить ARCHIVE_CHAT_ID:**
   - Бот должен быть администратором канала/чата
   - ID должен быть отрицательным числом для групп/каналов

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

```bash
# Установка
sudo apt update && sudo apt install -y python3.12 python3.12-venv ffmpeg git
sudo useradd -r -m -d /home/botuser -s /bin/bash botuser
sudo -u botuser git clone <repo-url> /home/botuser/telegram-inline-video-bot
sudo -u botuser bash -c "cd /home/botuser/telegram-inline-video-bot && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
sudo -u botuser nano /home/botuser/telegram-inline-video-bot/.env
sudo cp /home/botuser/telegram-inline-video-bot/deploy/telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable telegram-bot && sudo systemctl start telegram-bot

# Управление
sudo systemctl status telegram-bot     # Статус
sudo systemctl restart telegram-bot    # Перезапуск
sudo systemctl stop telegram-bot       # Остановка
sudo journalctl -u telegram-bot -f     # Логи

# Обновление
sudo -u botuser bash -c "cd /home/botuser/telegram-inline-video-bot && git pull && source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart telegram-bot
```

---

## Готово! 🚀

Ваш бот запущен и работает в фоновом режиме. Проверьте его работу в любом Telegram-чате через `@your_bot_username`.
