import json
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from google import genai

from database.models import Car, CarAnalysis, CarImage
from database.repositories import async_session
from backend.config import settings
from backend.services.storage import storage_service

client = None
if settings.gemini_api_key:
    client = genai.Client(api_key=settings.gemini_api_key)


VISION_PROMPT = """Analyze these car photos. Return JSON only:
{
  "exterior_condition": {"score": <0-10>, "issues": ["dents", "scratches", ...]},
  "interior_condition": {"score": <0-10>, "issues": [...]},
  "accident_signs": {"detected": true/false, "details": "..."},
  "tyre_condition": {"score": <0-10>, "notes": "..."},
  "overall_condition_score": <0-10>,
  "repainting_detected": true/false,
  "recommendation": "..."
}
"""


async def analyze_car_images(car_id, image_urls: List[str]) -> Optional[Dict]:
    if not client or not image_urls:
        return None

    image_parts = []
    for url in image_urls[:5]:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as c:
                resp = await c.get(url)
                if resp.status_code == 200:
                    import base64
                    b64 = base64.b64encode(resp.content).decode()
                    image_parts.append({
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64,
                        }
                    })
        except Exception:
            continue

    if not image_parts:
        return None

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[VISION_PROMPT, *image_parts],
        )
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Image analysis error: {e}")
        return None


async def analyze_all_car_images():
    async with async_session() as session:
        result = await session.execute(
            select(CarImage).where(CarImage.ai_analysis.is_(None)).limit(50)
        )
        images = result.scalars().all()

        for image in images:
            if image.original_url:
                analysis = await analyze_car_images(image.car_id, [image.original_url])
                if analysis:
                    image.ai_analysis = analysis

        await session.commit()
        print(f"Analyzed {len(images)} car images")
