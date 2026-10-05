# FreelanceHunt Telegram Bot (Programowanie → AI → Telegram)

Бот каждые 10 минут (GitHub Actions cron):
1. Парсит **все субкатегории Programowanie** на FreelanceHunt (20 штук, см. `config.py`).
2. Отбирает только **новые офферы** — которых не было в `seen.json` 10 минут назад.
3. Прогоняет каждый новый оффер (название + полное описание + бюджет) через **google/diffusiongemma-26b-a4b-it** (NVIDIA NIM) с систем-промптом где зашит твой GitHub `Shumskyi77` → ищет только **МЕЛКИЕ** подходящие задачи.
4. Подходящие прогоняет через **то же ИИ второй раз** → генерирует готовый отклик **PL + EN** ("почему брать именно меня").
5. Шлёт всё в Telegram.

## ⚠️ Безопасность (важно!)
Ты прислал токен бота прямо в чат — он теперь скомпрометирован.
1. Открой `@BotFather` → `/revoke` → выбери своего бота → получи **новый токен**.
2. **Никогда** не клади токены в код. Только в GitHub Secrets (ниже) и локальный `.env` (он в `.gitignore`).

## Настройка за 5 минут

### 1. Узнай свой TELEGRAM_CHAT_ID
- Напиши боту что-нибудь (например `/start`).
- Открой в браузере: `https://api.telegram.org/bot<ТВОЙ_ТОКЕН>/getUpdates`
- Найди `"chat":{"id":123456789` — это и есть CHAT_ID.

### 2. Получи NVIDIA_API_KEY
- https://build.nvidia.com → Login → твой ключ `nvapi-...`
- Модель: `google/diffusiongemma-26b-a4b-it` (диффузионная, вызывается как обычный `POST /v1/chat/completions`, `stream:false` — так уже сделано в `ai_client.py`).

### 3. Залей на GitHub
```bash
cd freelance_bot
git init
git add .
git commit -m "freelance bot"
git branch -M main
git remote add origin https://github.com/Shumskyi77/freelance_bot.git
git push -u origin main
```

### 4. Добавь Secrets (Settings → Secrets and variables → Actions → New secret)
- `TELEGRAM_BOT_TOKEN` — новый токен от BotFather
- `TELEGRAM_CHAT_ID` — цифры из шага 1
- `NVIDIA_API_KEY` — `nvapi-...`

### 5. Запусти
Actions → `freelance-monitor` → `Run workflow`. Дальше само каждые 10 минут.
`seen.json` сам коммитится обратно — так бот помнит что уже видел.

## Локальный запуск
```bash
cp .env.example .env   # и впиши свои ключи
pip install -r requirements.txt
python main.py
```

## Настройки (`config.py` / ENV)
- `MAX_NEW_PER_RUN=15` — максимум новых офферов за 1 запуск (защита от спама).
- `MIN_SCORE=6` — минимальный AI-скор чтобы слать в ТГ.
- Порог "мелкости" сидит в систем-промпте `ai_client.py` (`FILTER_SYSTEM`).

## Файлы
- `main.py` — оркестратор
- `freelance_parser.py` — парсинг листингов + полных описаний (JSON-LD + fallback)
- `github_profile.py` — живой fetch `api.github.com/users/Shumskyi77/repos` + фолбэк
- `ai_client.py` — 2 прогона через diffusiongemma (фильтр + отклик PL/EN)
- `telegram_sender.py` — отправка с разбивкой 4000 символов
- `.github/workflows/freelance.yml` — cron `*/10 * * * *`
