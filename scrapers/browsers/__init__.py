import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy import select, func

from database.repositories import async_session
from database.models import Car, CarImage, ScrapeJob
from database.repositories.car_repository import CarRepository
from database.repositories.queries import upsert_seller_profile
from backend.services.storage import storage_service
from backend.utils.metrics import CARS_ACTIVE


class BaseScraper(ABC):
    needs_browser: bool = True

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    async def scrape_listings(self, page=None, session=None) -> List[Dict]:
        pass

    async def run(self):
        import traceback

        job_id = None
        async with async_session() as session:
            job = ScrapeJob(source=self.source_name, status="running", started_at=datetime.utcnow())
            session.add(job)
            await session.commit()
            job_id = job.id

        listings = []
        if self.needs_browser:
            from playwright.async_api import async_playwright
            browser = None
            async with async_playwright() as pw:
                try:
                    browser = await pw.chromium.launch(
                        headless=True,
                        args=[
                            "--no-sandbox",
                            "--disable-blink-features=AutomationControlled",
                            "--disable-web-security",
                            "--disable-features=IsolateOrigins,site-per-process",
                        ],
                    )
                    context = await browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    )
                    await context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                        window.chrome = { runtime: {} };
                    """)
                    page = await context.new_page()
                    listings = await self.scrape_listings(page, None)
                except Exception as e:
                    print(f"[{self.source_name}] Error: {e}")
                    traceback.print_exc()
                    async with async_session() as session:
                        j = await session.get(ScrapeJob, job_id)
                        if j:
                            j.status = "failed"
                            j.errors = {"error": str(e)}
                            await session.commit()
                    raise e
                finally:
                    if browser:
                        await browser.close()
        else:
            try:
                listings = await self.scrape_listings(None, None)
            except Exception as e:
                print(f"[{self.source_name}] Error: {e}")
                traceback.print_exc()
                async with async_session() as session:
                    j = await session.get(ScrapeJob, job_id)
                    if j:
                        j.status = "failed"
                        j.errors = {"error": str(e)}
                        await session.commit()
                raise e

        saved = 0
        updated = 0
        async with async_session() as session:
            for data in listings:
                try:
                    result = await self._save_listing(session, data)
                    if result == "new":
                        saved += 1
                    elif result == "updated":
                        updated += 1
                except Exception as e:
                    print(f"Save error: {e}", flush=True)
                    await session.rollback()

            j = await session.get(ScrapeJob, job_id)
            if j:
                j.status = "completed"
                j.completed_at = datetime.utcnow()
                j.listings_found = len(listings)
                j.listings_new = saved
                j.listings_updated = updated

            await session.commit()

            CARS_ACTIVE.set(
                await session.scalar(select(func.count(Car.id)).where(Car.is_active == True))
            )

        print(f"[{self.source_name}] {saved} new, {updated} updated / {len(listings)} total", flush=True)
        return listings

    async def _save_listing(self, session, data: Dict) -> str:
        data["source"] = self.source_name
        repo = CarRepository(session)
        car = await repo.upsert(data)
        result = "updated" if car.updated_at != car.created_at else "new"

        image_urls = data.get("image_urls") or data.get("images") or []
        for url in image_urls:
            if isinstance(url, str):
                existing = await session.execute(
                    select(CarImage).where(
                        CarImage.car_id == car.id,
                        CarImage.original_url == url,
                    )
                )
                if not existing.scalar_one_or_none():
                    session.add(CarImage(car_id=car.id, original_url=url))

        if car.seller_phone:
            await upsert_seller_profile(session, {
                "seller_name": car.seller_name,
                "seller_phone": car.seller_phone,
                "sources": [car.source],
                "total_listings": 1,
                "active_listings": 1,
            })

        return result

    async def take_screenshot(self, page, listing_id: str):
        await storage_service.save_screenshot(page, listing_id)
        await storage_service.save_html(page, listing_id)

    def extract_brand_model(self, title: str) -> tuple:
        if not title:
            return None, None
        parts = title.strip().split(" ", 1)
        brand = parts[0] if parts else None
        return brand, title.strip()

    def _format_price(self, price_str: str) -> Optional[int]:
        if not price_str:
            return None
        s = price_str.replace(',', '')
        s = re.sub(r'\s+', '', s)
        s = s.replace('₹', '').replace('Rs.', '').replace('rs.', '')
        lower = s.lower()
        if 'lakh' in lower or lower.endswith('l'):
            s = lower.replace('lakh', '').replace('l', '').strip()
            try:
                return int(float(s) * 100000)
            except ValueError:
                return None
        if 'crore' in lower or lower.endswith('cr'):
            s = lower.replace('crore', '').replace('cr', '').strip()
            try:
                return int(float(s) * 10000000)
            except ValueError:
                return None
        try:
            return int(float(s))
        except ValueError:
            return None

    def extract_year(self, text: str) -> Optional[int]:
        import re
        years = re.findall(r'\b(20\d{2})\b', str(text))
        if years:
            return int(years[0])
        return None
