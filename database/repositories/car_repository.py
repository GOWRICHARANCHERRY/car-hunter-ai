from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, delete, update
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from database.models import (
    Car, CarImage, CarAnalysis, CarPriceHistory,
    FavoriteCar, SearchProfile, SellerProfile,
    UserPreference, MarketPrice, Notification, ScrapeJob
)


class CarRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_duplicate(self, car_data: Dict) -> Optional[Car]:
        conditions = []
        if car_data.get("registration"):
            conditions.append(Car.registration == car_data["registration"])
        if car_data.get("seller_phone"):
            conditions.append(Car.seller_phone == car_data["seller_phone"])
        if car_data.get("listing_url"):
            conditions.append(Car.listing_url == car_data["listing_url"])
        if car_data.get("source_id"):
            conditions.append(
                and_(Car.source == car_data.get("source"), Car.source_id == car_data["source_id"])
            )

        if not conditions:
            return None

        for cond in conditions:
            result = await self.session.execute(select(Car).where(cond).limit(1))
            car = result.scalar_one_or_none()
            if car:
                return car
        return None

    async def upsert(self, car_data: Dict) -> Car:
        dup = await self.find_duplicate(car_data)
        if dup:
            for key, val in car_data.items():
                if val is not None and hasattr(dup, key):
                    setattr(dup, key, val)
            dup.updated_at = datetime.utcnow()
            return dup

        car = Car(**{k: v for k, v in car_data.items() if hasattr(Car, k)})
        self.session.add(car)
        await self.session.flush()
        return car

    async def get_by_id(self, car_id: uuid.UUID) -> Optional[Car]:
        result = await self.session.execute(select(Car).where(Car.id == car_id))
        return result.scalar_one_or_none()

    async def search(
        self,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_year: Optional[int] = None,
        city: Optional[str] = None,
        fuel_type: Optional[str] = None,
        transmission: Optional[str] = None,
        min_score: Optional[int] = None,
        max_kms: Optional[int] = None,
        max_owners: Optional[int] = None,
        color: Optional[str] = None,
        sources: Optional[List[str]] = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Car], int]:
        query = select(Car).where(Car.is_active == True)

        if brand:
            query = query.where(Car.brand.ilike(f"%{brand}%"))
        if model:
            query = query.where(Car.model.ilike(f"%{model}%"))
        if min_price:
            query = query.where(Car.price >= min_price)
        if max_price:
            query = query.where(Car.price <= max_price)
        if min_year:
            query = query.where(Car.year >= min_year)
        if city:
            query = query.where(Car.city.ilike(f"%{city}%"))
        if fuel_type:
            query = query.where(Car.fuel_type.ilike(f"%{fuel_type}%"))
        if transmission:
            query = query.where(Car.transmission.ilike(f"%{transmission}%"))
        if max_kms:
            query = query.where(Car.kms <= max_kms)
        if max_owners:
            query = query.where(Car.owners <= max_owners)
        if color:
            query = query.where(Car.color.ilike(f"%{color}%"))
        if sources:
            query = query.where(Car.source.in_(sources))

        total_q = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(total_q)

        sort_col = getattr(Car, sort_by, Car.created_at)
        order_fn = desc if sort_dir == "desc" else asc
        query = query.order_by(order_fn(sort_col)).offset(offset).limit(limit)

        result = await self.session.execute(query)
        cars = result.scalars().all()

        if min_score:
            car_ids = [c.id for c in cars]
            if car_ids:
                analysis_q = select(CarAnalysis.car_id, CarAnalysis.score).where(
                    CarAnalysis.car_id.in_(car_ids),
                    CarAnalysis.score >= min_score,
                )
                analysis_result = await self.session.execute(analysis_q)
                scored_ids = {row[0] for row in analysis_result}
                cars = [c for c in cars if c.id in scored_ids]
                total = len(cars)

        return list(cars), total or 0

    async def get_deals(self, threshold: int = 85, limit: int = 20) -> List[tuple]:
        query = (
            select(Car, CarAnalysis)
            .join(CarAnalysis, Car.id == CarAnalysis.car_id)
            .where(Car.is_active == True, CarAnalysis.score >= threshold)
            .order_by(CarAnalysis.score.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.all()


class PriceHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_change(self, car_id: uuid.UUID, old_price: Optional[int], new_price: int):
        record = CarPriceHistory(car_id=car_id, old_price=old_price, new_price=new_price)
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_history(self, car_id: uuid.UUID) -> List[CarPriceHistory]:
        result = await self.session.execute(
            select(CarPriceHistory)
            .where(CarPriceHistory.car_id == car_id)
            .order_by(CarPriceHistory.changed_at.desc())
            .limit(20)
        )
        return result.scalars().all()

    async def get_recent_price_drops(self, hours: int = 24) -> List[tuple]:
        since = datetime.utcnow() - timedelta(hours=hours)
        subq = (
            select(
                CarPriceHistory.car_id,
                CarPriceHistory.old_price,
                CarPriceHistory.new_price,
                CarPriceHistory.changed_at,
                (CarPriceHistory.old_price - CarPriceHistory.new_price).label("drop_amount"),
            )
            .where(
                CarPriceHistory.changed_at >= since,
                CarPriceHistory.old_price > CarPriceHistory.new_price,
            )
            .order_by(desc("drop_amount"))
            .subquery()
        )
        query = (
            select(Car, subq)
            .join(subq, Car.id == subq.c.car_id)
            .where(Car.is_active == True)
            .order_by(desc(subq.c.drop_amount))
            .limit(20)
        )
        result = await self.session.execute(query)
        return result.all()
