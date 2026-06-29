from typing import Dict, Optional
import httpx
from backend.config import settings

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


async def send_telegram_message(text: str) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": settings.telegram_chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False


async def send_telegram_photo(photo_url: str, caption: str) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{TELEGRAM_API}/sendPhoto",
                json={
                    "chat_id": settings.telegram_chat_id,
                    "photo": photo_url,
                    "caption": caption,
                    "parse_mode": "Markdown",
                },
                timeout=30,
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"Telegram photo error: {e}")
            return False


def format_deal_message(car: Dict) -> str:
    score_emoji = "🔥" if car["score"] >= 90 else "✅"
    stars = "⭐" * (car["score"] // 20)
    msg = (
        f"{score_emoji} *Great Deal Found*\n\n"
        f"*{car['title']}*\n"
        f"{car['year']} | {car['kms']:,} km\n"
        f"💰 ₹{car['price']:,}\n\n"
        f"*Score:* {car['score']}/100 {stars}\n"
    )
    if car.get("listing_url"):
        msg += f"🔗 [View Listing]({car['listing_url']})\n"
    if car.get("fair_price"):
        diff = car["fair_price"] - car["price"]
        if diff > 0:
            msg += f"✅ ₹{diff:,} below market\n"
        else:
            msg += f"⚠️ ₹{abs(diff):,} above market\n"
    if car.get("pros"):
        msg += "\n*Pros:*\n" + "\n".join(f"✓ {p}" for p in car["pros"][:3]) + "\n"
    if car.get("cons"):
        msg += "\n*Cons:*\n" + "\n".join(f"⚠️ {c}" for c in car["cons"][:2]) + "\n"
    return msg
