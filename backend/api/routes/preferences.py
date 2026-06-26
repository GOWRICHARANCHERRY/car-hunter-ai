import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List

from database.repositories import get_db
from database.repositories.queries import get_preferences, save_preferences, get_search_profiles, create_search_profile
from database.repositories.queries import get_favorites, add_favorite, remove_favorite

router = APIRouter(tags=["preferences"])


class PreferenceBody(BaseModel):
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    preferred_models: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    max_kms: Optional[int] = None
    fuel_types: Optional[List[str]] = None
    transmission: Optional[str] = None
    colors: Optional[List[str]] = None


class SearchProfileBody(BaseModel):
    profile_name: str
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    preferred_models: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    max_kms: Optional[int] = None
    fuel_types: Optional[List[str]] = None
    transmission: Optional[str] = None
    colors: Optional[List[str]] = None
    min_year: Optional[int] = None
    max_owners: Optional[int] = None


@router.get("/preferences")
async def get_user_preferences(db: AsyncSession = Depends(get_db)):
    pref = await get_preferences(db)
    if not pref:
        return {
            "budget_min": None, "budget_max": None,
            "preferred_models": [], "cities": [],
            "max_kms": None, "fuel_types": [],
            "transmission": None, "colors": [],
        }
    return {
        "budget_min": pref.budget_min,
        "budget_max": pref.budget_max,
        "preferred_models": pref.preferred_models or [],
        "cities": pref.cities or [],
        "max_kms": pref.max_kms,
        "fuel_types": pref.fuel_types or [],
        "transmission": pref.transmission,
        "colors": pref.colors or [],
    }


@router.post("/preferences")
async def save_user_preferences(body: PreferenceBody, db: AsyncSession = Depends(get_db)):
    await save_preferences(db, body.model_dump(exclude_none=True))
    await db.commit()
    return {"status": "saved"}


@router.get("/search-profiles")
async def list_search_profiles(db: AsyncSession = Depends(get_db)):
    profiles = await get_search_profiles(db)
    return [
        {
            "id": str(p.id),
            "profile_name": p.profile_name,
            "budget_min": p.budget_min,
            "budget_max": p.budget_max,
            "preferred_models": p.preferred_models or [],
            "cities": p.cities or [],
            "max_kms": p.max_kms,
            "fuel_types": p.fuel_types or [],
            "transmission": p.transmission,
            "colors": p.colors or [],
            "min_year": p.min_year,
            "max_owners": p.max_owners,
        }
        for p in profiles
    ]


@router.post("/search-profiles")
async def add_search_profile(body: SearchProfileBody, db: AsyncSession = Depends(get_db)):
    profile = await create_search_profile(db, body.model_dump())
    await db.commit()
    return {"id": str(profile.id), "status": "created"}


@router.get("/favorites")
async def list_favorites(db: AsyncSession = Depends(get_db)):
    cars = await get_favorites(db)
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "brand": c.brand,
            "model": c.model,
            "year": c.year,
            "price": c.price,
            "kms": c.kms,
            "city": c.city,
            "image_urls": c.image_urls,
            "listing_url": c.listing_url,
        }
        for c in cars
    ]


@router.post("/favorites/{car_id}")
async def add_favorite_car(car_id: str, db: AsyncSession = Depends(get_db)):
    try:
        from database.models import Car
        from sqlalchemy import select
        uid = uuid.UUID(car_id)
        result = await db.execute(select(Car).where(Car.id == uid))
        if not result.scalar_one_or_none():
            raise HTTPException(404, "Car not found")
        await add_favorite(db, uid)
        await db.commit()
    except ValueError:
        raise HTTPException(400, "Invalid car ID")
    return {"status": "favorited"}


@router.delete("/favorites/{car_id}")
async def remove_favorite_car(car_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(car_id)
        await remove_favorite(db, uid)
        await db.commit()
    except ValueError:
        raise HTTPException(400, "Invalid car ID")
    return {"status": "removed"}
