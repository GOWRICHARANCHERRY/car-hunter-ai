import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy import select, desc, func

from database.repositories import async_session
from database.models import Car, CarAnalysis, CarPriceHistory, Notification
from backend.config import settings
from notifications.telegram import send_telegram_message
from ai.analysis.scorer import format_deal_text


@shared_task
def detect_price_drops():
    async def _run():
        since = datetime.utcnow() - timedelta(hours=6)
        async with async_session() as session:
            result = await session.execute(
                select(CarPriceHistory, Car)
                .join(Car, CarPriceHistory.car_id == Car.id)
                .where(
                    CarPriceHistory.changed_at >= since,
                    CarPriceHistory.old_price > CarPriceHistory.new_price,
                    Car.is_active == True,
                )
                .order_by(desc(CarPriceHistory.old_price - CarPriceHistory.new_price))
                .limit(10)
            )
            rows = result.all()
            for ph, car in rows:
                drop = ph.old_price - ph.new_price
                msg = (
                    f"💰 *Price Drop Alert*\n\n"
                    f"*{car.title}*\n"
                    f"₹{ph.old_price:,} → ₹{ph.new_price:,}\n"
                    f"🔥 Dropped by ₹{drop:,}\n"
                    f"[View Listing]({car.listing_url})"
                )
                await send_telegram_message(msg)

                session.add(Notification(
                    user_id="default",
                    car_id=car.id,
                    notification_type="price_drop",
                    title=f"Price dropped by ₹{drop:,}",
                    message=msg,
                    channel="telegram",
                    sent=True,
                    sent_at=datetime.utcnow(),
                ))
            await session.commit()
            print(f"Sent {len(rows)} price drop alerts")

    asyncio.run(_run())


@shared_task
def send_daily_summary():
    async def _run():
        since = datetime.utcnow() - timedelta(hours=24)
        async with async_session() as session:
            new_cars = await session.scalar(
                select(func.count(Car.id)).where(Car.created_at >= since, Car.is_active == True)
            )
            excellent = await session.scalar(
                select(func.count(CarAnalysis.id))
                .where(CarAnalysis.created_at >= since, CarAnalysis.score >= 85)
            )
            price_drops = await session.scalar(
                select(func.count(CarPriceHistory.id))
                .where(CarPriceHistory.changed_at >= since, CarPriceHistory.old_price > CarPriceHistory.new_price)
            )

            msg = (
                f"📊 *Daily Summary*\n\n"
                f"📅 {datetime.utcnow().strftime('%b %d, %Y')}\n\n"
                f"🆕 New listings: {new_cars or 0}\n"
                f"🔥 Excellent deals: {excellent or 0}\n"
                f"💰 Price drops: {price_drops or 0}\n\n"
                f"---\n"
                f"🤖 Car Hunter AI"
            )
            await send_telegram_message(msg)
            print("Daily summary sent")

    asyncio.run(_run())
