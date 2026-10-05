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

# Официальный RSS (разрешён для агрегаторов, не блокируется как HTML).
RSS_URL = "https://freelancehunt.com/pl/projects.rss"

# Skill-категории группы "Programowanie" (PL-названия как в RSS <category>).
# Фильтруем ленту по ним — это те же 20 субкатегорий, что парсили по HTML.
PROGRAMOWANIE_SKILLS = [
    "AI i uczenie maszynowe",
    "Aplikacje desktopowe",
    "AR i VR",
    "Bazy danych i SQL",
    "BI i analityka danych",
    "C i C++",
    "C#",
    "Content Management Systems",
    "Java",
    "Javascript & Typescript",
    "Kryptowaluty i blockchain",
    "Parsowanie danych",
    "PHP",
    "Programowanie stron internetowych",
    "Python",
    "Systemy wbudowane i mikrokontrolery",
    "Testowanie i kontrola jakości",
    "Tworzenie chatbota",
    "Tworzenie gier",
    "Układ HTML i CSS",
    # запасные короткие формы, если RSS назовёт иначе:
    "Machine Learning",
    "Chatbot",
    "Parsing",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8,uk;q=0.7,ru;q=0.6",
}

SEEN_FILE = "seen.json"
