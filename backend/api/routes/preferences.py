import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List

from database.repositories import get_db, async_session
from database.repositories.queries import get_preferences, save_preferences, get_search_profiles, create_search_profile
from database.repositories.queries import get_favorites, add_favorite, remove_favorite, create_notification
from database.models import Car, CarAnalysis

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
    prefs_data = body.model_dump(exclude_none=True)
    await save_preferences(db, prefs_data)
    await db.commit()

    asyncio.create_task(search_and_notify_on_preferences(prefs_data))

    return {"status": "saved", "search_started": True, "message": "Preferences saved! Searching for matching cars..."}


async def search_and_notify_on_preferences(prefs: dict):
    from scrapers.websites.cars24 import Cars24Scraper
    from scrapers.websites.spinny import SpinnyScraper
    from scrapers.websites.carwale import CarWaleScraper
    from scrapers.websites.olx import OLXScraper
    from ai.analysis.analyzer import analyze_unanalyzed_listings
    from notifications.telegram import send_telegram_message, format_deal_message
    from sqlalchemy import select, and_, or_

    new_count = 0
    for scraper_cls in [Cars24Scraper, SpinnyScraper, CarWaleScraper, OLXScraper]:
        try:
            scraper = scraper_cls()
            await scraper.run()
            new_count += 1
        except Exception as e:
            print(f"Scraper {scraper_cls.__name__} failed: {e}")

    await analyze_unanalyzed_listings()

    async with async_session() as session:
        conditions = [Car.is_active == True, CarAnalysis.id != None]
        query = select(Car).join(CarAnalysis, Car.id == CarAnalysis.car_id)

        budget_min = prefs.get("budget_min")
        budget_max = prefs.get("budget_max")
        max_kms = prefs.get("max_kms")
        preferred_models = prefs.get("preferred_models")
        cities = prefs.get("cities")
        fuel_types = prefs.get("fuel_types")
        transmission = prefs.get("transmission")
        colors = prefs.get("colors")

        if budget_min:
            conditions.append(Car.price >= budget_min)
        if budget_max:
            conditions.append(Car.price <= budget_max)
        if max_kms:
            conditions.append(Car.kms <= max_kms)
        if preferred_models:
            model_conditions = [Car.model.ilike(f"%{m}%") for m in preferred_models]
            conditions.append(or_(*model_conditions))
        if cities:
            city_conditions = [Car.city.ilike(f"%{c}%") for c in cities]
            conditions.append(or_(*city_conditions))
        if fuel_types:
            fuel_conditions = [Car.fuel_type.ilike(f) for f in fuel_types]
            conditions.append(or_(*fuel_conditions))
        if transmission:
            conditions.append(Car.transmission.ilike(f"%{transmission}%"))
        if colors:
            color_conditions = [Car.color.ilike(f"%{c}%") for c in colors]
            conditions.append(or_(*color_conditions))

        query = query.where(and_(*conditions)).order_by(CarAnalysis.score.desc()).limit(10)
        result = await session.execute(query)
        cars = result.scalars().all()

        if not cars:
            msg = (
                "🔍 *Search Complete*\n\n"
                f"Scraped {new_count} sites but no cars matched your preferences yet.\n"
                "Scheduler will keep checking every 14 minutes."
            )
            await send_telegram_message(msg)
            return

        score_threshold = 70
        deals = []
        for car in cars:
            analysis = await session.execute(
                select(CarAnalysis).where(CarAnalysis.car_id == car.id)
            )
            analysis = analysis.scalar_one_or_none()
            if analysis and analysis.score and analysis.score >= score_threshold:
                deals.append({
                    "title": car.title or "",
                    "year": car.year,
                    "kms": car.kms or 0,
                    "price": car.price or 0,
                    "score": analysis.score,
                    "fair_price": analysis.fair_price,
                    "pros": analysis.pros or [],
                    "cons": analysis.cons or [],
                    "listing_url": car.listing_url or "",
                })

        if deals:
            header = f"🔍 *Search Results — {len(deals)} deals found*\n\n"
            await send_telegram_message(header + "Top matches below 👇")

            for deal in deals[:5]:
                try:
                    msg = format_deal_message(deal)
                    await send_telegram_message(msg)
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Failed to send deal notification: {e}")
        else:
            await send_telegram_message(
                f"🔍 *Search Complete*\n\nFound {len(cars)} matching cars but none scored above {score_threshold}. Scheduler will keep checking."
            )

        for car in cars[:10]:
            analysis = await session.execute(
                select(CarAnalysis).where(CarAnalysis.car_id == car.id)
            )
            analysis = analysis.scalar_one_or_none()
            await create_notification(session, {
                "user_id": "default",
                "car_id": car.id,
                "notification_type": "preference_match",
                "title": f"Preference match: {car.title}",
                "message": f"{car.title} — ₹{car.price:,}" if car.price else car.title,
                "score": analysis.score if analysis else None,
                "channel": "telegram",
                "sent": True,
                "sent_at": datetime.utcnow(),
            })
        await session.commit()


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
