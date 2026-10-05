"""Оркестратор: парсинг Programowanie -> новые за 10 мин -> AI фильтр (мелкие) -> AI отклик -> Telegram."""
import json
import os
import time
import traceback

import config
from freelance_parser import scrape_all_programowanie, parse_project_page
from github_profile import fetch_github_profile
from ai_client import score_offer, generate_proposal
from telegram_sender import send_message, format_offer

# Жёсткий лимит времени на AI-прогоны, чтобы workflow успевал закоммитить seen.json
TIME_BUDGET = 420  # секунд (cron каждые 10 мин, timeout в workflow — 9 мин)


def load_seen(path: str = None) -> dict:
    path = path or config.SEEN_FILE
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_seen(seen: dict, path: str = None):
    path = path or config.SEEN_FILE
    # чистим старше 7 дней чтобы файл не рос бесконечно
    now = time.time()
    cleaned = {k: v for k, v in seen.items() if now - float(v.get("ts", 0) if isinstance(v, dict) else 0) < 7 * 86400}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)


def main():
    started_at = time.time()
    print("=== FreelanceHunt bot run ===")
    seen = load_seen()
    print(f"seen before: {len(seen)}")

    github_profile = fetch_github_profile(config.GITHUB_USERNAME)
    print(f"github profile chars: {len(github_profile)}")

    listings = scrape_all_programowanie()
    print(f"listings total (all Programowanie): {len(listings)}")

    # Новые = которых не было в seen (т.е. появились за последние ~10 мин между запусками)
    fresh_listings = [x for x in listings if x["id"] not in seen]
    print(f"fresh (not in seen): {len(fresh_listings)}")

    # защита от первого запуска (когда seen пустой и всё "новое"): берём только топ-N
    fresh_listings = fresh_listings[: config.MAX_NEW_PER_RUN]
    if not fresh_listings:
        print("No new offers. Updating seen with current ids and exit.")
        for x in listings:
            seen[x["id"]] = {"ts": time.time(), "url": x["url"]}
        save_seen(seen)
        return

    # Детализация: полный title+description для AI
    detailed: list[dict] = []
    for item in fresh_listings:
        try:
            full = parse_project_page(item["url"])
            full["category"] = item.get("category", "")
            detailed.append(full)
            time.sleep(0.5)
        except Exception as e:
            print(f"[WARN] detail failed {item['id']}: {e}")

    sent = 0
    processed_ids: set[str] = set()
    for offer in detailed:
        if time.time() - started_at > TIME_BUDGET:
            print(f"[WARN] time budget {TIME_BUDGET}s исчерпан, остаток уйдёт в след. запуск")
            break
        # Прогон 1: AI-фильтр мелких подходящих
        s = score_offer(offer, github_profile)
        print(f"[{offer['id']}] score={s['score']} small={s['is_small']} | {offer.get('title','')[:80]}")
        processed_ids.add(offer["id"])
        if not s["is_small"] or s["score"] < config.MIN_SCORE:
            continue
        # Прогон 2: AI-генерация отклика PL+EN
        try:
            proposal = generate_proposal(offer, github_profile, s)
        except Exception as e:
            print(f"[WARN] proposal failed {offer['id']}: {e}")
            traceback.print_exc()
            continue
        msg = format_offer(offer, s, proposal)
        ok = send_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, msg)
        if ok:
            sent += 1
        time.sleep(1.5)  # бережём лимиты NVIDIA + Telegram

    # Помечаем seen только реально обработанное + уже известное.
    # Необработанные "свежие" (не влезли в cap / кончилось время) НЕ помечаем —
    # иначе они потеряются навсегда и больше никогда не придут.
    for x in listings:
        if x["id"] in processed_ids or x["id"] in seen:
            seen[x["id"]] = {"ts": time.time(), "url": x["url"]}
    save_seen(seen)
    skipped = len(fresh_listings) - len(processed_ids)
    print(f"DONE. fresh={len(detailed)} sent={sent} deferred={skipped} seen_after={len(seen)}")


if __name__ == "__main__":
    main()
