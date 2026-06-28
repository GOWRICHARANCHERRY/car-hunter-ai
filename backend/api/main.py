import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest
from fastapi.responses import Response

from database.repositories import init_db
from backend.utils.metrics import metrics_middleware
from backend.api.routes import cars, deals, preferences, chat, stats, notifications
from backend.config import settings


async def scheduler_loop():
    while True:
        print("Starting scheduler cycle...")
        try:
            from scrapers.websites.cars24 import Cars24Scraper
            from scrapers.websites.spinny import SpinnyScraper
            from scrapers.websites.carwale import CarWaleScraper
            from scrapers.websites.olx import OLXScraper

            for scraper_cls in [Cars24Scraper, SpinnyScraper, CarWaleScraper, OLXScraper]:
                try:
                    scraper = scraper_cls()
                    await scraper.run()
                except Exception as e:
                    print(f"Scraper {scraper_cls.__name__} failed: {e}")

            from ai.analysis.analyzer import analyze_unanalyzed_listings
            await analyze_unanalyzed_listings()

            try:
                from notifications.telegram import send_telegram_message
                from sqlalchemy import select, func
                from database.repositories import async_session
                from database.models import Car, CarAnalysis
                async with async_session() as s:
                    total = await s.scalar(select(func.count(Car.id)).where(Car.is_active == True))
                    scored = await s.scalar(select(func.count(CarAnalysis.id)).where(CarAnalysis.score.isnot(None)))
                    top = await s.execute(
                        select(CarAnalysis).order_by(CarAnalysis.score.desc()).limit(3)
                    )
                    top_list = []
                    for a in top.scalars():
                        car = await s.get(Car, a.car_id)
                        if car:
                            top_list.append(f"• {car.title[:30]} — Score: {a.score}/100")
                    msg = (
                        f"🔄 *Car Hunter Cycle Complete*\n"
                        f"Total cars: {total} | Analyzed: {scored}\n\n"
                    )
                    if top_list:
                        msg += "*Top Deals:*\n" + "\n".join(top_list)
                    ok = await send_telegram_message(msg)
                    print(f"Telegram summary sent: {ok}")
            except Exception as notify_e:
                print(f"Telegram notification error: {notify_e}")

        except Exception as e:
            print(f"Scheduler error: {e}")

        await asyncio.sleep(settings.scrape_interval_minutes * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(scheduler_loop())
    yield
    task.cancel()


app = FastAPI(title="Car Hunter AI", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(metrics_middleware)

app.include_router(cars.router, prefix="/api")
app.include_router(deals.router, prefix="/api")
app.include_router(preferences.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
