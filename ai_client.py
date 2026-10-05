"""AI через NVIDIA NIM: google/diffusiongemma-26b-a4b-it (диффузионная текстовая модель).

Правильный вызов (как в доке NVIDIA):
    import requests
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "google/diffusiongemma-26b-a4b-it", "messages": [...], "temperature": ..., "max_tokens": ...}
    requests.post(invoke_url, headers=headers, json=payload, timeout=120)

Особенность diffusion-модели: она генерирует токены параллельными блоками по 256,
поэтому ставим stream=False, умеренный temperature и достаточный max_tokens.
Thinking/reasoning режим не включаем — нам нужны короткие чёткие ответы.
"""
import json
import re
import time
import requests

from config import NVIDIA_API_KEY, NVIDIA_INVOKE_URL, NVIDIA_MODEL

FILTER_SYSTEM = """Ты — фильтр фриланс-офферов для Taras Szumski (GitHub Shumskyi77).
{github_profile}

Твоя задача: искать ТОЛЬКО МЕЛКИЕ подходящие офферы, а НЕ большие проекты.

ПОДХОДИТ (score 6-10):
- Telegram-боты, Discord-боты, мелкие чат-боты (aiogram, Python)
- Парсинг / мониторинг / скрапинг (Playwright, BeautifulSoup, OLX/Allegro)
- Лендинги, мелкие правки HTML/CSS/Tailwind, мелкие JS/TS фичи и фиксы
- Мелкие Python-скрипты, автоматизации Excel/Google Sheets, мелкие API-интеграции
- Мелкие AI-интеграции: подключить LLM API, простой RAG-прототип, промпты
- Бюджет/объём: задача на часы — несколько дней, один человек справится

НЕ ПОДХОДИТ (score 1-5):
- Большие CRM/ERP с нуля, enterprise SaaS, долгосрок full-time, команда
- Сложный ML/CV R&D, обучение моделей с нуля, multi-agent production-платформы
- High-load, fintech-ядро, безопасность критичных систем
- "Ищем команду", сроки месяцы, десятки интеграций сразу
- Бюджет огромный при гигантском ТЗ (это не мелкий оффер)

Верни СТРОГО JSON без markdown:
{"score": 1-10, "reason": "1-2 предложения почему", "is_small": true/false}
Оцени title + description + budget + skills из входных данных.
"""


def _nim_chat(system: str, user: str, max_tokens: int = 1500, temperature: float = 0.3) -> str:
    """Базовый вызов NVIDIA NIM chat completions. Возвращает текст ассистента."""
    if not NVIDIA_API_KEY:
        raise RuntimeError("NVIDIA_API_KEY пустой. Добавь секрет в GitHub Secrets / .env")
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "top_p": 0.9,
        "max_tokens": max_tokens,
        "stream": False,
    }
    last_err = None
    for attempt in range(3):
        try:
            resp = requests.post(NVIDIA_INVOKE_URL, headers=headers, json=payload, timeout=120)
            if resp.status_code in (429, 500, 502, 503, 529):
                last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
                time.sleep(5 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            last_err = e
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"NVIDIA NIM failed after 3 tries: {last_err}")


def _extract_json(text: str) -> dict:
    """Вытаскивает JSON даже если модель обернула его в markdown."""
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    raw = m.group(0)
    try:
        return json.loads(raw)
    except Exception:
        # чиним висячие запятые/обрезки
        raw = re.sub(r",\s*}", "}", raw)
        try:
            return json.loads(raw)
        except Exception:
            return {}


def score_offer(offer: dict, github_profile: str) -> dict:
    """Прогон 1: подходит ли оффер + мелкий ли он. Возвращает {score, reason, is_small}."""
    system = FILTER_SYSTEM.format(github_profile=github_profile)
    user = (
        f"Название: {offer.get('title','')}\n"
        f"Бюджет: {offer.get('budget','')}\n"
        f"Категория: {offer.get('category','')}\n"
        f"Скиллы: {', '.join(offer.get('skills', []))}\n"
        f"Ссылка: {offer.get('url','')}\n"
        f"Описание:\n{offer.get('description','')[:3500]}"
    )
    try:
        raw = _nim_chat(system, user, max_tokens=600, temperature=0.2)
        parsed = _extract_json(raw)
        score = int(parsed.get("score", 0) or 0)
        return {
            "score": max(0, min(10, score)),
            "reason": str(parsed.get("reason", raw[:300])),
            "is_small": bool(parsed.get("is_small", score >= 6)),
            "raw": raw[:800],
        }
    except Exception as e:
        print(f"[WARN] score failed {offer.get('id')}: {e}")
        return {"score": 0, "reason": f"AI error: {e}", "is_small": False, "raw": ""}


PROPOSAL_SYSTEM = """Ты — Taras Szumski, фрилансер (Python / Telegram-боты / парсинг / лендинги / JS-TS).
{github_profile}

Напиши короткий отклик-заявку на оффер, которую можно вставить на FreelanceHunt.
Структура:
1) PL — 4-7 предложений: кто я, релевантный проект с GitHub (назови 1-2), как сделаю задачу (2-4 шага), срок + вопрос/CTA.
2) Разделитель ---
3) EN — то же самое на английском (4-7 предложений).

Правила: конкретно под оффер, без воды, без выдуманного опыта, без гарантий 99%.
Тон уверенный, дружелюбный. До 1200 символов на каждый язык.
"""


def generate_proposal(offer: dict, github_profile: str, score_info: dict | None = None) -> str:
    """Прогон 2: генерирует готовый текст отклика PL + EN (почему брать именно меня)."""
    system = PROPOSAL_SYSTEM.format(github_profile=github_profile)
    hint = ""
    if score_info:
        hint = f"\nПочему оффер подошёл (для контекста, не копируй дословно): {score_info.get('reason','')}"
    user = (
        f"Оффер: {offer.get('title','')}\n"
        f"Бюджет: {offer.get('budget','')}\n"
        f"Ссылка: {offer.get('url','')}\n"
        f"Описание:\n{offer.get('description','')[:3500]}"
        f"{hint}\n\nСгенерируй отклик PL + --- + EN."
    )
    return _nim_chat(system, user, max_tokens=1800, temperature=0.5)
