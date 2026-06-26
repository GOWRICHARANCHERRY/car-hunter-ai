from celery import Celery
from datetime import timedelta
from backend.config import settings

celery_app = Celery(
    "car_hunter",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "backend.tasks.scrape_tasks",
        "backend.tasks.analysis_tasks",
        "backend.tasks.notification_tasks",
    ],
)

celery_app.conf.beat_schedule = {
    "scrape-all-sites": {
        "task": "backend.tasks.scrape_tasks.scrape_all_sites",
        "schedule": timedelta(minutes=settings.scrape_interval_minutes),
    },
    "recalculate-market-prices": {
        "task": "backend.tasks.analysis_tasks.recalculate_market_prices",
        "schedule": timedelta(hours=24),
    },
    "analyze-new-listings": {
        "task": "backend.tasks.analysis_tasks.analyze_new_listings",
        "schedule": timedelta(minutes=15),
    },
    "send-daily-summary": {
        "task": "backend.tasks.notification_tasks.send_daily_summary",
        "schedule": timedelta(hours=24),
    },
    "detect-price-drops": {
        "task": "backend.tasks.notification_tasks.detect_price_drops",
        "schedule": timedelta(hours=6),
    },
    "cleanup-stale-listings": {
        "task": "backend.tasks.analysis_tasks.cleanup_stale_listings",
        "schedule": timedelta(hours=12),
    },
}

celery_app.conf.timezone = "UTC"
