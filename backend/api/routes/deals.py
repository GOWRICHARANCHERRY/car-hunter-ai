from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from database.repositories import get_db
from database.repositories.car_repository import CarRepository
from database.models import CarAnalysis

router = APIRouter(tags=["deals"])


@router.get("/deals")
async def get_deals(
    threshold: int = Query(85),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db),
):
    repo = CarRepository(db)
    rows = await repo.get_deals(threshold=threshold, limit=limit)

    result = []
    for car, analysis in rows:
        result.append({
            "id": str(car.id),
            "title": car.title,
            "brand": car.brand,
            "model": car.model,
            "year": car.year,
            "price": car.price,
            "kms": car.kms,
            "city": car.city,
            "fuel_type": car.fuel_type,
            "transmission": car.transmission,
            "score": analysis.score,
            "fair_price": analysis.fair_price,
            "recommendation": analysis.recommendation,
            "pros": analysis.pros,
            "cons": analysis.cons,
            "listing_url": car.listing_url,
            "image_urls": car.image_urls,
            "created_at": car.created_at.isoformat() if car.created_at else None,
        })

    return result
