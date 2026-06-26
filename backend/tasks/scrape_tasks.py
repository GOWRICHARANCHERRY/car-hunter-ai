import asyncio
from celery import shared_task
from backend.utils.metrics import SCRAPES_TOTAL, LISTINGS_FOUND, SCRAPE_DURATION
import time


def run_scraper(scraper_class):
    async def _run():
        scraper = scraper_class()
        try:
            start = time.time()
            await scraper.run()
            duration = time.time() - start
            SCRAPE_DURATION.labels(source=scraper.source_name).observe(duration)
            SCRAPES_TOTAL.labels(source=scraper.source_name, status="success").inc()
            LISTINGS_FOUND.labels(source=scraper.source_name).inc(len(getattr(scraper, 'last_listings', [])))
        except Exception as e:
            SCRAPES_TOTAL.labels(source=scraper.source_name, status="failed").inc()
            raise e

    asyncio.run(_run())


@shared_task
def scrape_cars24():
    from scrapers.websites.cars24 import Cars24Scraper
    run_scraper(Cars24Scraper)


@shared_task
def scrape_spinny():
    from scrapers.websites.spinny import SpinnyScraper
    run_scraper(SpinnyScraper)


@shared_task
def scrape_carwale():
    from scrapers.websites.carwale import CarWaleScraper
    run_scraper(CarWaleScraper)


@shared_task
def scrape_olx():
    from scrapers.websites.olx import OLXScraper
    run_scraper(OLXScraper)


@shared_task
def scrape_all_sites():
    tasks = [scrape_cars24.delay(), scrape_spinny.delay(), scrape_carwale.delay(), scrape_olx.delay()]
    for t in tasks:
        t.get(timeout=300)
