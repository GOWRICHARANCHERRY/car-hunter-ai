from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class OLXScraper(BaseScraper):
    source_name = "OLX"

    async def scrape_listings(self, page, session) -> List[Dict]:
        listings = []
        await page.goto("https://www.olx.in/cars/", timeout=60000)
        await page.wait_for_timeout(5000)

        for _ in range(8):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)

        cards = await page.query_selector_all('[data-autoid*="listing"], [class*="card"], a[href*="/item"]')
        if not cards:
            cards = await page.query_selector_all("a[href*='/cars']")

        for card in cards[:30]:
            try:
                data = await self._extract(page, card)
                if data and data.get("price"):
                    listings.append(data)
            except Exception:
                pass

        return listings

    async def _extract(self, page, card) -> Optional[Dict]:
        title_el = await card.query_selector("h6, h5, [class*='title'], span[class*='title']")
        title = await title_el.inner_text() if title_el else ""

        price_el = await card.query_selector('[class*="price"], span:has-text("₹"), span:has-text("Rs")')
        price_str = await price_el.inner_text() if price_el else ""

        link_el = await card.query_selector("a[href]")
        url = await link_el.get_attribute("href") if link_el else ""

        detail_el = await card.query_selector('[class*="detail"], [class*="desc"]')
        detail_text = await detail_el.inner_text() if detail_el else ""

        img_el = await card.query_selector("img")
        img_url = await img_el.get_attribute("src") if img_el else None

        brand, model = self.extract_brand_model(title)
        full_url = url if url.startswith("http") else f"https://www.olx.in{url}"

        return {
            "source_id": url.split("/")[-1] if url else title,
            "title": title.strip(),
            "brand": brand,
            "model": model,
            "year": self.extract_year(detail_text),
            "price": self._format_price(price_str),
            "listing_url": full_url,
            "image_urls": [img_url] if img_url else [],
            "description": detail_text.strip(),
        }
