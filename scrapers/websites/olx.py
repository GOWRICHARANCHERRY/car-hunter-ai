import re
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

        cards = await page.query_selector_all('li[data-aut-id="itemBox2"]')
        if not cards:
            cards = await page.query_selector_all('[data-aut-id="itemsList"] a[href*="/item/"]')

        for card in cards[:30]:
            try:
                data = await self._extract(page, card)
                if data and data.get("price"):
                    listings.append(data)
            except Exception as e:
                print(f"OLX card error: {e}")

        return listings

    async def _extract(self, page, card) -> Optional[Dict]:
        link_el = await card.query_selector("a[href]")
        url = await link_el.get_attribute("href") if link_el else ""

        title_el = await card.query_selector('[data-aut-id="itemTitle"]')
        title = await title_el.inner_text() if title_el else ""

        price_el = await card.query_selector('[data-aut-id="itemPrice"]')
        price_str = await price_el.inner_text() if price_el else ""

        subtitle_el = await card.query_selector('[data-aut-id="itemSubTitle"]')
        subtitle = await subtitle_el.inner_text() if subtitle_el else ""

        details_el = await card.query_selector('[data-aut-id="itemDetails"]')
        detail_text = await details_el.inner_text() if details_el else ""

        img_el = await card.query_selector("img")
        img_url = await img_el.get_attribute("src") if img_el else None

        brand, model = self.extract_brand_model(title)
        full_url = url if url.startswith("http") else f"https://www.olx.in{url}"
        source_id = url.split("iid-")[-1] if "iid-" in url else url.split("/")[-1]

        year = self.extract_year(subtitle)
        mileage = None
        if subtitle:
            parts = subtitle.split("-")
            if len(parts) > 1:
                km_match = re.search(r'([\d,]+)\s*km', parts[1])
                if km_match:
                    mileage = int(km_match.group(1).replace(",", ""))

        location = detail_text.split("\n")[0].strip() if detail_text else ""

        return {
            "source_id": source_id,
            "title": title.strip(),
            "brand": brand,
            "model": model,
            "year": year,
            "price": self._format_price(price_str),
            "mileage": mileage,
            "listing_url": full_url,
            "image_urls": [img_url] if img_url else [],
            "description": subtitle.strip(),
            "location": location,
        }
