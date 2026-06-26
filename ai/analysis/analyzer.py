import json
from typing import Optional
from google import genai

from database.models import Car, CarAnalysis
from backend.config import settings
from ai.analysis.scorer import calculate_score

client = None
if settings.gemini_api_key:
    client = genai.Client(api_key=settings.gemini_api_key)


ANALYSIS_PROMPT = """You are an automotive buying expert. Analyze this used car listing.

Return valid JSON with no markdown:
{
  "score": <int 0-100>,
  "fair_price": <int in INR>,
  "recommendation": "<Excellent Deal|Good Deal|Fair Deal|Skip>",
  "pros": ["<pro>", ...],
  "cons": ["<con>", ...],
  "market_insight": "<one sentence market analysis>",
  "negotiation_tip": "<one sentence negotiation advice>"
}

Weight: Market Price 25%, Mileage 15%, Owner Count 15%, Condition 20%, Seller Trust 10%, Resale 5%, Service History 10%

Car Details:
Title: {title}
Brand: {brand} | Model: {model}
Year: {year} | Price: ₹{price} | KMs: {kms}
Fuel: {fuel_type} | Transmission: {transmission} | Owners: {owners}
City: {city} | Registration: {registration}
Description: {description}
"""


async def analyze_car(car: Car) -> Optional[CarAnalysis]:
    if client:
        prompt = ANALYSIS_PROMPT.format(
            title=car.title or "N/A",
            brand=car.brand or "N/A",
            model=car.model or "N/A",
            year=car.year or "N/A",
            price=f"{car.price:,}" if car.price else "N/A",
            kms=f"{car.kms:,}" if car.kms else "N/A",
            fuel_type=car.fuel_type or "N/A",
            transmission=car.transmission or "N/A",
            owners=car.owners or "N/A",
            city=car.city or "N/A",
            registration=car.registration or "N/A",
            description=(car.description or "")[:800],
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            text = response.text.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
        except Exception as e:
            print(f"Gemini API error: {e}")
            data = calculate_score(car)
    else:
        data = calculate_score(car)

    return CarAnalysis(
        car_id=car.id,
        score=data.get("score"),
        score_breakdown={
            "market_price": 25,
            "mileage": 15,
            "owner_count": 15,
            "condition": 20,
            "seller_trust": 10,
            "resale": 5,
            "service_history": 10,
        },
        fair_price=data.get("fair_price"),
        recommendation=data.get("recommendation", "Fair Deal"),
        pros=data.get("pros", []),
        cons=data.get("cons", []),
        seller_trust_score=data.get("seller_trust_score"),
        raw_analysis=data,
    )
