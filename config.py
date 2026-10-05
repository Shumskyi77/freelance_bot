"""Центральный конфиг. Все секреты — только из ENV / GitHub Secrets, никогда в коде."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "Shumskyi77")

MAX_NEW_PER_RUN = int(os.getenv("MAX_NEW_PER_RUN", "15"))
MIN_SCORE = int(os.getenv("MIN_SCORE", "6"))

# NVIDIA NIM endpoint (OpenAI-compatible). Модель — диффузионная текстовая.
NVIDIA_INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "google/diffusiongemma-26b-a4b-it"

# Все субкатегории категории "Programowanie" (PL). Парсим все — новые отбираем по seen.json
PROGRAMOWANIE_CATEGORIES = {
    # название: url первой страницы (там самые свежие сверху)
    "AI i uczenie maszynowe": "https://freelancehunt.com/pl/projects/skill/uczenie-maszynowe/175.html",
    "Aplikacje desktopowe": "https://freelancehunt.com/pl/projects/skill/programowanie-aplikacji/103.html",
    "AR i VR": "https://freelancehunt.com/pl/projects/skill/ar-vr-tworzenie/185.html",
    "Bazy danych i SQL": "https://freelancehunt.com/pl/projects/skill/bazy-danych/86.html",
    "BI i analityka danych": "https://freelancehunt.com/pl/projects/skill/bi-analityka-danych/199.html",
    "C i C++": "https://freelancehunt.com/pl/projects/skill/cplusplus/2.html",
    "C#": "https://freelancehunt.com/pl/projects/skill/c/24.html",
    "CMS": "https://freelancehunt.com/pl/projects/skill/content-management-systems/78.html",
    "Java": "https://freelancehunt.com/pl/projects/skill/java/13.html",
    "Javascript & Typescript": "https://freelancehunt.com/pl/projects/skill/javascript/28.html",
    "Krypto i blockchain": "https://freelancehunt.com/pl/projects/skill/blockchain/182.html",
    "Parsowanie danych": "https://freelancehunt.com/pl/projects/skill/parsowanie-danych/169.html",
    "PHP": "https://freelancehunt.com/pl/projects/skill/php/1.html",
    "Strony internetowe": "https://freelancehunt.com/pl/projects/skill/programowanie-stron-internetowych/99.html",
    "Python": "https://freelancehunt.com/pl/projects/skill/python/22.html",
    "Embedded / mikrokontrolery": "https://freelancehunt.com/pl/projects/skill/systemy-wbudowane-mikrokontrolery/176.html",
    "Testowanie / QA": "https://freelancehunt.com/pl/projects/skill/testowanie-kontrola-jakosci/57.html",
    "Chatboty": "https://freelancehunt.com/pl/projects/skill/budowa-chatbota/180.html",
    "Gry": "https://freelancehunt.com/pl/projects/skill/tworzenie-gier/88.html",
    "HTML i CSS": "https://freelancehunt.com/pl/projects/skill/uklad-html-css/124.html",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8,uk;q=0.7,ru;q=0.6",
}

SEEN_FILE = "seen.json"
