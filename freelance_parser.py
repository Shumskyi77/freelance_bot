"""Парсинг FreelanceHunt: листинги Programowanie + полные описания проектов."""
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import HEADERS, PROGRAMOWANIE_CATEGORIES

PROJECT_URL_RE = re.compile(r"/(?:pl/)?project/[^/\"']+/(\d+)\.html")

session = requests.Session()
session.headers.update(HEADERS)

PARSER = "lxml"
try:
    BeautifulSoup("<p/>", "lxml")
except Exception:
    PARSER = "html.parser"


def _get(url: str, timeout: int = 25) -> str:
    for attempt in range(3):
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    return ""


def parse_category_listing(category_name: str, category_url: str) -> list[dict]:
    """Возвращает [{id, url, title_short}] с первой страницы категории (самые свежие сверху)."""
    html = _get(category_url)
    soup = BeautifulSoup(html, PARSER)
    found: dict[str, dict] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = PROJECT_URL_RE.search(href)
        if not m:
            continue
        pid = m.group(1)
        full_url = urljoin("https://freelancehunt.com", href)
        # чистим якоря/параметры
        full_url = full_url.split("#")[0]
        if pid in found:
            continue
        short = a.get_text(" ", strip=True)[:180]
        found[pid] = {"id": pid, "url": full_url, "title_short": short, "category": category_name}
    return list(found.values())


def parse_project_page(url: str) -> dict:
    """Тянет полное название + описание + бюджет. Сначала JSON-LD, потом HTML-фолбэк."""
    html = _get(url)
    soup = BeautifulSoup(html, PARSER)
    title, desc, budget = "", "", ""

    # 1) JSON-LD Product
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") == "Product" and ("name" in item or "description" in item):
                title = title or str(item.get("name", ""))
                desc = desc or str(item.get("description", ""))
                offers = item.get("offers", {})
                if isinstance(offers, dict):
                    lp = offers.get("lowPrice", "")
                    hp = offers.get("highPrice", "")
                    cur = offers.get("priceCurrency", "PLN")
                    if lp or hp:
                        budget = f"{lp}-{hp} {cur}".strip("- ")

    # 2) HTML fallback
    if not title:
        h1 = soup.find("h1", class_=re.compile(r"assignment-title"))
        if h1:
            title = h1.get_text(" ", strip=True)
    if not desc:
        box = soup.find("div", class_=re.compile(r"assignment-description"))
        if box:
            desc = box.get_text("\n", strip=True)
    if not desc:
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            desc = meta["content"]

    # бюджет из текста бейджа вида "2166 PLN 120 ofert ..."
    if not budget:
        m = re.search(r"(\d[\d\s]*\s?(?:PLN|UAH|USD|EUR))", soup.get_text(" ", strip=True))
        if m:
            budget = m.group(1).strip()

    # скиллы/теги
    skills: list[str] = []
    for tag in soup.select("a[href*='/projects/skill/']"):
        t = tag.get_text(" ", strip=True)
        if t and len(t) < 60:
            skills.append(t)
    skills = list(dict.fromkeys(skills))[:15]

    pid_m = PROJECT_URL_RE.search(url)
    pid = pid_m.group(1) if pid_m else url

    # обрезаем описание чтобы не раздувать промпт (AI возьмёт ~4000 символов — достаточно)
    desc = (desc or "")[:4000]

    return {
        "id": pid,
        "url": url,
        "title": (title or "")[:250],
        "description": desc,
        "budget": budget,
        "skills": skills,
    }


def scrape_all_programowanie(pause: float = 0.7) -> list[dict]:
    """Проходит все субкатегории Programowanie, возвращает уникальные проекты-листинги."""
    all_projects: dict[str, dict] = {}
    for cat_name, cat_url in PROGRAMOWANIE_CATEGORIES.items():
        try:
            items = parse_category_listing(cat_name, cat_url)
            for it in items:
                if it["id"] not in all_projects:
                    all_projects[it["id"]] = it
                # если проект в нескольких категориях — дописываем категории
                elif cat_name not in all_projects[it["id"]].get("category", ""):
                    all_projects[it["id"]]["category"] += f", {cat_name}"
        except Exception as e:
            print(f"[WARN] category failed {cat_name}: {e}")
        time.sleep(pause)
    return list(all_projects.values())
