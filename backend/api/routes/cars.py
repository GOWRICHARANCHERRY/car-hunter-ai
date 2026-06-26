from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import uuid

from database.repositories import get_db
from database.repositories.car_repository import CarRepository, PriceHistoryRepository
from database.models import Car, CarAnalysis, CarPriceHistory
from backend.services.storage import storage_service

router = APIRouter(tags=["cars"])


def car_to_dict(car: Car, analysis: Optional[CarAnalysis] = None) -> dict:
    return {
        "id": str(car.id),
        "source": car.source,
        "title": car.title,
        "brand": car.brand,
        "model": car.model,
        "year": car.year,
        "price": car.price,
        "kms": car.kms,
        "fuel_type": car.fuel_type,
        "transmission": car.transmission,
        "owners": car.owners,
        "city": car.city,
        "registration": car.registration,
        "color": car.color,
        "image_urls": car.image_urls,
        "listing_url": car.listing_url,
        "created_at": car.created_at.isoformat() if car.created_at else None,
        "score": analysis.score if analysis else None,
        "recommendation": analysis.recommendation if analysis else None,
        "fair_price": analysis.fair_price if analysis else None,
        "pros": analysis.pros if analysis else None,
        "cons": analysis.cons if analysis else None,
    }


@router.get("/cars")
async def list_cars(
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    min_year: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    transmission: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    max_kms: Optional[int] = Query(None),
    max_owners: Optional[int] = Query(None),
    sources: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    limit: int = Query(50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    repo = CarRepository(db)
    source_list = sources.split(",") if sources else None
    cars, total = await repo.search(
        brand=brand, model=model,
        min_price=min_price, max_price=max_price,
        min_year=min_year, city=city,
        fuel_type=fuel_type, transmission=transmission,
        min_score=min_score, max_kms=max_kms,
        max_owners=max_owners, sources=source_list,
        sort_by=sort_by, sort_dir=sort_dir,
        limit=limit, offset=offset,
    )
    return {
        "total": total,
        "cars": [car_to_dict(c) for c in cars],
        "limit": limit,
        "offset": offset,
    }


@router.get("/cars/{car_id}")
async def get_car(car_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(car_id)
    except ValueError:
        raise HTTPException(400, "Invalid car ID")

    repo = CarRepository(db)
    car = await repo.get_by_id(uid)
    if not car:
        raise HTTPException(404, "Car not found")

    analysis = None
    if car.analysis:
        analysis = car.analysis

    price_history = []
    if car.price_history:
        for ph in car.price_history:
            price_history.append({
                "old_price": ph.old_price,
                "new_price": ph.new_price,
                "changed_at": ph.changed_at.isoformat() if ph.changed_at else None,
            })

    images = []
    if car.images:
        for img in car.images:
            images.append({
                "id": str(img.id),
                "original_url": img.original_url,
                "storage_path": storage_service.get_url(img.storage_path) if img.storage_path else None,
                "thumbnail_path": storage_service.get_url(img.thumbnail_path) if img.thumbnail_path else None,
                "ai_analysis": img.ai_analysis,
            })

    return {
        **car_to_dict(car, analysis),
        "description": car.description,
        "seller_name": car.seller_name,
        "seller_phone": car.seller_phone,
        "registration_state": car.registration_state,
        "source_id": car.source_id,
        "price_history": price_history,
        "images": images,
        "analysis_detail": {
            "score_breakdown": analysis.score_breakdown if analysis else None,
            "seller_trust_score": analysis.seller_trust_score if analysis else None,
            "raw_analysis": analysis.raw_analysis if analysis else None,
        } if analysis else None,
    }
