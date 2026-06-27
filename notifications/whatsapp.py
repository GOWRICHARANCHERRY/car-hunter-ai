from typing import Optional
import httpx
from backend.config import settings

WHATSAPP_API = "https://graph.facebook.com/v21.0"


async def send_whatsapp(to: str, message: str) -> bool:
    if not settings.whatsapp_phone_number_id or not settings.whatsapp_access_token:
        print("[WhatsApp] Not configured")
        return False

    url = f"{WHATSAPP_API}/{settings.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": True, "body": message},
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return True
            print(f"[WhatsApp] Error: {resp.text}")
            return False
        except Exception as e:
            print(f"[WhatsApp] Exception: {e}")
            return False


def format_whatsapp_message(car_data: dict) -> str:
    msg = f"🔥 *Great Deal Found*\n\n"
    msg += f"*{car_data['title']}*\n"
    msg += f"{car_data['year']} | {car_data['kms']:,} km\n"
    msg += f"💰 ₹{car_data['price']:,}\n"
    msg += f"Score: {car_data['score']}/100\n"
    if car_data.get("pros"):
        msg += "\nPros:\n" + "\n".join(f"✅ {p}" for p in car_data["pros"][:3])
    if car_data.get("listing_url"):
        msg += f"\n\n{car_data['listing_url']}"
    return msg
