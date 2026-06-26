import asyncio
from celery import shared_task
from database.repositories import async_session
from database.models import Car, CarAnalysis, MarketPrice
from sqlalchemy import select, func, delete


@shared_task
def analyze_new_listings():
    async def _run():
        from ai.analysis.analyzer import analyze_car
        async with async_session() as session:
            subq = select(CarAnalysis.car_id)
            result = await session.execute(
                select(Car).where(Car.id.not_in(subq), Car.is_active == True)
            )
            cars = result.scalars().all()
            for car in cars:
                analysis = await analyze_car(car)
                if analysis:
                    session.add(analysis)
            await session.commit()
            print(f"Analyzed {len(cars)} new listings")

    asyncio.run(_run())


@shared_task
def recalculate_market_prices():
    async def _run():
        async with async_session() as session:
            await session.execute(delete(MarketPrice))
            model_years = await session.execute(
                select(Car.model, Car.year, Car.city,
                       func.avg(Car.price), func.min(Car.price),
                       func.max(Car.price), func.count(Car.id))
                .where(Car.price.isnot(None), Car.is_active == True)
                .group_by(Car.model, Car.year, Car.city)
            )
            for row in model_years:
                mp = MarketPrice(
                    model_key=f"{row[0]}|{row[1]}|{row[2]}",
                    year=row[1],
                    city=row[2],
                    avg_price=int(row[3]),
                    lowest_price=int(row[4]),
                    highest_price=int(row[5]),
                    sample_count=row[6],
                )
                session.add(mp)
            await session.commit()
            print("Market prices recalculated")

    asyncio.run(_run())


@shared_task
def cleanup_stale_listings():
    async def _run():
        from datetime import datetime, timedelta
        async with async_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=14)
            result = await session.execute(
                select(Car).where(Car.updated_at < cutoff, Car.is_active == True)
            )
            cars = result.scalars().all()
            for car in cars:
                car.is_active = False
            await session.commit()
            print(f"Marked {len(cars)} stale listings as inactive")

    asyncio.run(_run())
