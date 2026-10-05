"""Снапшот GitHub-профиля для системного промпта AI. Живой fetch + статичный фолбэк."""
import requests

FALLBACK_PROFILE = """Freelancer: Taras Szumski (GitHub: Shumskyi77).
Стек: Python (aiogram 3, Playwright, SQLite, Django basics), JavaScript/TypeScript, HTML + Tailwind, REST API, Stripe/S3/PostgreSQL basics, LLM/API integrations.

Репозитории:
1) LandingPagePortfolio (HTML) — статичный лендинг + lead-capture для Oak Corner Workshop (Варшава, мебель дуб/ясень/орех, лидтайм 4-8 недель, гарантия 5 лет). HTML + Tailwind CDN.
2) TelegramBot_Portfolio (Python) — Telegram-бот мониторинга OLX-объявлений, новые лоты каждые 5 мин (aiogram 3 + Playwright + SQLite).
3) SaaS_Product_portfolio (TypeScript) — AI nutrition diary & macro tracker (SaaS дневник питания).
4) BGremover (JavaScript) — удаление фона с изображений.

Вывод: силён в МЕЛКИХ задачах: Telegram-боты, парсинг/мониторинг, лендинги, мелкие Python-скрипты/автоматизации, мелкие JS/TS фиксы, простые API-интеграции, простые чат-боты.
НЕ брать: большие CRM/ERP, долгосрочный full-time, enterprise SaaS, сложные ML/CV R&D, multi-agent production, high-load fintech, сроки в месяцы.
"""


def fetch_github_profile(username: str = "Shumskyi77", timeout: int = 20) -> str:
    try:
        headers = {"User-Agent": "freelance-bot", "Accept": "application/vnd.github+json"}
        r = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated", headers=headers, timeout=timeout)
        r.raise_for_status()
        repos = r.json()
        if not isinstance(repos, list) or not repos:
            return FALLBACK_PROFILE
        lines = [f"Freelancer GitHub: https://github.com/{username}. Репозитории (живые данные):"]
        for repo in repos[:12]:
            if isinstance(repo, dict) and not repo.get("fork"):
                name = repo.get("name", "?")
                lang = repo.get("language") or "?"
                desc = (repo.get("description") or "").strip()[:200]
                url = repo.get("html_url", "")
                lines.append(f"- {name} [{lang}] — {desc} ({url})")
        lines.append(
            "\nВывод: специализация — МЕЛКИЕ задачи: Telegram-боты (aiogram), парсинг/Playwright/SQLite, "
            "лендинги HTML+Tailwind, мелкие Python-автоматизации, JS/TS мелочи, простые API/LLM-интеграции. "
            "НЕ брать большие проекты (CRM с нуля, enterprise SaaS, сложный ML/CV R&D, multi-agent production)."
        )
        return "\n".join(lines)
    except Exception as e:
        print(f"[WARN] github fetch failed, using fallback: {e}")
        return FALLBACK_PROFILE
