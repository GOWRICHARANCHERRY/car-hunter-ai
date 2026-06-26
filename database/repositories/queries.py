from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, update, delete
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from backend.config import settings
from database.models import (
    Car, CarImage, CarAnalysis, CarPriceHistory,
    FavoriteCar, SearchProfile, SellerProfile,
    UserPreference, MarketPrice, Notification, ScrapeJob
)


async def get_preferences(session: AsyncSession, user_id: str = "default") -> Optional[UserPreference]:
    result = await session.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def save_preferences(session: AsyncSession, data: Dict, user_id: str = "default") -> UserPreference:
    result = await session.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        pref = UserPreference(user_id=user_id)
        session.add(pref)

    for key in [
        "budget_min", "budget_max", "preferred_models", "cities",
        "max_kms", "fuel_types", "transmission", "colors",
    ]:
        if key in data:
            setattr(pref, key, data[key])
    await session.flush()
    return pref


async def get_search_profiles(session: AsyncSession, user_id: str = "default") -> List[SearchProfile]:
    result = await session.execute(
        select(SearchProfile)
        .where(SearchProfile.user_id == user_id)
        .order_by(SearchProfile.created_at.desc())
    )
    return result.scalars().all()


async def create_search_profile(session: AsyncSession, data: Dict, user_id: str = "default") -> SearchProfile:
    profile = SearchProfile(user_id=user_id, **data)
    session.add(profile)
    await session.flush()
    return profile


async def get_favorites(session: AsyncSession, user_id: str = "default") -> List[Car]:
    result = await session.execute(
        select(Car)
        .join(FavoriteCar, Car.id == FavoriteCar.car_id)
        .where(FavoriteCar.user_id == user_id, Car.is_active == True)
        .order_by(FavoriteCar.created_at.desc())
    )
    return result.scalars().all()


async def add_favorite(session: AsyncSession, car_id, user_id: str = "default") -> FavoriteCar:
    fav = FavoriteCar(user_id=user_id, car_id=car_id)
    session.add(fav)
    try:
        await session.flush()
    except Exception:
        pass  # already exists
    return fav


async def remove_favorite(session: AsyncSession, car_id, user_id: str = "default"):
    await session.execute(
        delete(FavoriteCar).where(
            FavoriteCar.user_id == user_id,
            FavoriteCar.car_id == car_id,
        )
    )
    await session.flush()


async def get_seller_profile(session: AsyncSession, phone: str) -> Optional[SellerProfile]:
    result = await session.execute(
        select(SellerProfile).where(SellerProfile.seller_phone == phone)
    )
    return result.scalar_one_or_none()


async def upsert_seller_profile(session: AsyncSession, data: Dict) -> SellerProfile:
    phone = data.get("seller_phone")
    if phone:
        result = await session.execute(
            select(SellerProfile).where(SellerProfile.seller_phone == phone)
        )
        profile = result.scalar_one_or_none()
        if profile:
            for k, v in data.items():
                if v is not None:
                    setattr(profile, k, v)
            profile.last_seen = datetime.utcnow()
            return profile

    profile = SellerProfile(**data)
    session.add(profile)
    await session.flush()
    return profile


async def create_notification(session: AsyncSession, data: Dict) -> Notification:
    notification = Notification(**data)
    session.add(notification)
    await session.flush()
    return notification


async def get_recent_notifications(
    session: AsyncSession,
    user_id: str = "default",
    limit: int = 50,
) -> List[Notification]:
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_stats(session: AsyncSession) -> Dict:
    total = await session.scalar(select(func.count(Car.id)).where(Car.is_active == True))
    analyzed = await session.scalar(select(func.count(CarAnalysis.id)))
    avg_score = await session.scalar(select(func.avg(CarAnalysis.score)))
    active_deals = await session.scalar(
        select(func.count(CarAnalysis.id)).where(CarAnalysis.score >= settings.notification_score_threshold)
    )
    favorites = await session.scalar(
        select(func.count(FavoriteCar.id)).where(FavoriteCar.user_id == "default")
    )

    return {
        "total_listings": total or 0,
        "analyzed": analyzed or 0,
        "avg_score": round(avg_score, 1) if avg_score else None,
        "active_deals": active_deals or 0,
        "favorites": favorites or 0,
    }
