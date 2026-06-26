from typing import Dict, Optional
from backend.config import settings


async def send_whatsapp(message: str) -> bool:
    # WhatsApp Business API via Twilio or Meta Cloud API
    # Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
    print(f"[WhatsApp] Would send: {message[:100]}...")
    return False
