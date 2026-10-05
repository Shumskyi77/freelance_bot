"""Парсинг FreelanceHunt через официальный RSS (freelancehunt.com/pl/projects.rss).

Почему RSS: HTML-страницы отдают 403 с IP дата-центров (GitHub Actions),
а RSS-лента официально разрешена для агрегаторов и обычно не блокируется.
Лента содержит title + snippet описания + pubDate + link + category — этого
достаточно для AI-фильтра и генерации отклика (полный текст — по ссылке в ТГ).
"""
import html
import re
import time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

from config import HEADERS, PROGRAMOWANIE_SKILLS, RSS_URL

PROJECT_URL_RE = re.compile(r"/project/[^/\"'?>]+/(\d+)\.html")
BUDGET_RE = re.compile(r"[-–—]\s*([\d\s.,]+)\s*(UAH|PLN|USD|EUR)\s*$", re.IGNORECASE)

session = requests.Session()
session.headers.update(HEADERS)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


NORM_SKILLS = {_norm(x) for x in PROGRAMOWANIE_SKILLS}

# Запасной keyword-фильтр: если RSS-категория названа иначе, ловим явно "наши" темы
KEYWORDS = (
    "python", "aiogram", "telegram-bot", "telegram bot", "playwright",
    "parsowanie", "парсинг", "scrap", "chatbot", "chat-bot", "llm", "rag",
    "html", "css", "tailwind", "javascript", "typescript", "php", "opencart",
    "wordpress", "woocommerce",
)


def _is_programowanie(categories: list[str], title: str, desc: str) -> bool:
    if any(_norm(c) in NORM_SKILLS for c in categories):
        return True
    blob = _norm(f"{title} {desc}")
    return any(k in blob for k in KEYWORDS)


def fetch_rss(url: str = RSS_URL, timeout: int = 25) -> list[dict]:
    """Возвращает сырые items ленты: [{id, url, title, description, budget, category, pub_ts}]."""
    last_err = None
    for attempt in range(3):
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            raw = r.content
            break
        except Exception as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"RSS fetch failed: {last_err}")

    root = ET.fromstring(raw)
    items: list[dict] = []
    for it in root.iter("item"):
        title = html.unescape((it.findtext("title") or "").strip())
        desc = html.unescape((it.findtext("description") or "").strip())
        link = (it.findtext("link") or "").strip()
        cats = [html.unescape((c.text or "").strip()) for c in it.findall("category")]
        cats = [c for c in cats if c]
        pub_raw = (it.findtext("pubDate") or "").strip()
        try:
            pub_ts = parsedate_to_datetime(pub_raw).timestamp() if pub_raw else 0
        except Exception:
            pub_ts = 0

        m = PROJECT_URL_RE.search(link)
        if not m:
            continue
        pid = m.group(1)
        clean_url = link.split("?")[0].split("#")[0]

        budget = ""
        bm = BUDGET_RE.search(title)
        if bm:
            amount = re.sub(r"\s+", "", bm.group(1)).replace(",", ".")
            budget = f"{amount} {bm.group(2).upper()}"
            title = BUDGET_RE.sub("", title).strip(" -–—")

        items.append({
            "id": pid,
            "url": clean_url,
            "title": title[:250],
            "description": desc[:1500],
            "budget": budget,
            "skills": cats[:15],
            "category": ", ".join(cats[:4]),
            "pub_ts": pub_ts,
        })
    return items


def scrape_all_programowanie() -> list[dict]:
    """Берёт глобальный RSS и оставляет только Programowanie (по skill-категориям + keywords)."""
    try:
        items = fetch_rss()
    except Exception as e:
        print(f"[WARN] RSS failed: {e}")
        return []
    out = [x for x in items if _is_programowanie(x["skills"], x["title"], x["description"])]
    # сначала самые свежие
    out.sort(key=lambda x: x.get("pub_ts", 0), reverse=True)
    print(f"rss items total={len(items)} programowanie={len(out)}")
    return out
