from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from database.models import SellerProfile, Car, CarAnalysis
from database.repositories import async_session


async def calculate_seller_trust_score(seller_name: str, seller_phone: str) -> Dict:
    async with async_session() as session:
        result = await session.execute(
            select(SellerProfile).where(SellerProfile.seller_phone == seller_phone)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return {"score": 50, "factors": ["New seller - insufficient data"]}

        score = 70
        factors = []

        if profile.active_listings > 10:
            score -= 15
            factors.append("Many active listings - possible dealer")
        elif profile.active_listings <= 3:
            score += 10
            factors.append("Few listings - likely individual seller")

        cars_result = await session.execute(
            select(Car).where(Car.seller_phone == seller_phone, Car.is_active == True)
        )
        cars = cars_result.scalars().all()

        prices = [c.price for c in cars if c.price]
        if len(prices) >= 2:
            avg = sum(prices) / len(prices)
            for p in prices:
                if p < avg * 0.6 or p > avg * 1.5:
                    score -= 10
                    factors.append("Suspicious pricing detected")
                    break

        if profile.first_seen:
            days_known = (datetime.utcnow() - profile.first_seen).days
            if days_known > 90:
                score += 10
                factors.append("Established seller")
            elif days_known < 7:
                score -= 5
                factors.append("Very new seller")

        return {
            "score": max(0, min(100, score)),
            "factors": factors,
        }
