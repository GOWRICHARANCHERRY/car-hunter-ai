from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import List, Optional
import json

from database.repositories import get_db
from database.models import Car, CarAnalysis
from backend.config import settings

router = APIRouter(tags=["chat"])


client = None
if settings.gemini_api_key:
    from google import genai
    client = genai.Client(api_key=settings.gemini_api_key)


SYSTEM_PROMPT = """You are an AI car buying assistant. Convert the user's natural language request into a JSON filter object for searching used cars.

Return ONLY valid JSON with no markdown:
{
  "filters": {
    "brand": string or null,
    "model": string or null,
    "min_price": int or null,
    "max_price": int or null,
    "min_year": int or null,
    "city": string or null,
    "fuel_type": string or null,
    "transmission": string or null,
    "max_kms": int or null,
    "max_owners": int or null,
    "color": string or null
  },
  "explanation": "brief explanation in 1 sentence"
}

Examples:
- "Find me an automatic Honda City under 9 lakh" -> {"filters": {"model": "Honda City", "transmission": "Automatic", "max_price": 900000}}
- "White car with good resale in Bangalore" -> {"filters": {"city": "Bangalore", "color": "White"}}
"""


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    filters: dict
    explanation: str
    cars: List[dict]


@router.post("/chat", response_model=ChatResponse)
async def chat_search(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    if not client:
        raise HTTPException(503, "AI chat requires Gemini API key")

    prompt = f"{SYSTEM_PROMPT}\n\nUser: {body.message}"
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        filters = data.get("filters", {})
        explanation = data.get("explanation", "")
    except Exception as e:
        raise HTTPException(500, f"AI parsing error: {e}")

    query = select(Car).where(Car.is_active == True)
    if filters.get("brand"):
        query = query.where(Car.brand.ilike(f"%{filters['brand']}%"))
    if filters.get("model"):
        query = query.where(Car.model.ilike(f"%{filters['model']}%"))
    if filters.get("min_price"):
        query = query.where(Car.price >= filters["min_price"])
    if filters.get("max_price"):
        query = query.where(Car.price <= filters["max_price"])
    if filters.get("min_year"):
        query = query.where(Car.year >= filters["min_year"])
    if filters.get("city"):
        query = query.where(Car.city.ilike(f"%{filters['city']}%"))
    if filters.get("fuel_type"):
        query = query.where(Car.fuel_type.ilike(f"%{filters['fuel_type']}%"))
    if filters.get("transmission"):
        query = query.where(Car.transmission.ilike(f"%{filters['transmission']}%"))
    if filters.get("max_kms"):
        query = query.where(Car.kms <= filters["max_kms"])
    if filters.get("max_owners"):
        query = query.where(Car.owners <= filters["max_owners"])
    if filters.get("color"):
        query = query.where(Car.color.ilike(f"%{filters['color']}%"))

    query = query.limit(10)
    result = await db.execute(query)
    cars = result.scalars().all()

    car_list = []
    for car in cars:
        car_list.append({
            "id": str(car.id),
            "title": car.title,
            "brand": car.brand,
            "model": car.model,
            "year": car.year,
            "price": car.price,
            "kms": car.kms,
            "fuel_type": car.fuel_type,
            "transmission": car.transmission,
            "city": car.city,
            "listing_url": car.listing_url,
        })

    return ChatResponse(filters=filters, explanation=explanation, cars=car_list)
