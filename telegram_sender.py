"""Отправка в Telegram через Bot API с разбивкой длинных сообщений."""
import time
import requests

API = "https://api.telegram.org/bot{token}/{method}"


def send_message(token: str, chat_id: str, text: str, parse_mode: str = "HTML", disable_preview: bool = True) -> bool:
    if not token or not chat_id:
        print("[WARN] no TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID — пропускаю отправку")
        print(text[:1000])
        return False
    # Telegram лимит 4096 символов
    chunks: list[str] = []
    t = text
    while len(t) > 4000:
        cut = t.rfind("\n", 0, 4000)
        if cut < 1000:
            cut = 4000
        chunks.append(t[:cut])
        t = t[cut:]
    chunks.append(t)
    ok = True
    for ch in chunks:
        r = None
        try:
            r = requests.post(
                API.format(token=token, method="sendMessage"),
                json={"chat_id": chat_id, "text": ch, "parse_mode": parse_mode,
                      "disable_web_page_preview": disable_preview},
                timeout=25,
            )
            if r.status_code == 429:
                time.sleep(3)
                r = requests.post(
                    API.format(token=token, method="sendMessage"),
                    json={"chat_id": chat_id, "text": ch, "parse_mode": parse_mode,
                          "disable_web_page_preview": disable_preview},
                    timeout=25,
                )
            r.raise_for_status()
            time.sleep(0.4)
        except Exception as e:
            body = r.text[:300] if r is not None else ""
            print(f"[ERROR] telegram send failed: {e} | {body}")
            ok = False
    return ok


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_offer(offer: dict, score: dict, proposal: str) -> str:
    title = esc(offer.get("title", "Без назви")[:200])
    budget = esc(offer.get("budget", "—"))
    cat = esc(offer.get("category", ""))
    url = offer.get("url", "")
    reason = esc(score.get("reason", "")[:400])
    sc = score.get("score", 0)
    desc = esc((offer.get("description", "") or "")[:600])
    prop = esc((proposal or "")[:3000])
    return (
        f"🆕 <b>{title}</b>\n"
        f"💰 {budget} | 📂 {cat}\n"
        f"⭐ Score: <b>{sc}/10</b> — {reason}\n"
        f"🔗 {url}\n\n"
        f"<b>Опис:</b>\n{desc}…\n\n"
        f"<b>✉️ Готовий відгук (PL + EN) — копіюй на FreelanceHunt:</b>\n"
        f"<pre>{prop}</pre>"
    )
