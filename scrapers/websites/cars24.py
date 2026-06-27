import re
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class Cars24Scraper(BaseScraper):
    source_name = "Cars24"

    async def scrape_listings(self, page, session) -> List[Dict]:
        listings = []
        await page.goto("https://www.cars24.com/buy-used-cars-bangalore/", timeout=60000)
        await page.wait_for_timeout(5000)

        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

        cards = await page.query_selector_all('a[class*="carCardWrapper"]')

        for card in cards[:30]:
            try:
                data = await self._extract(page, card)
                if data and data.get("price"):
                    listings.append(data)
            except Exception as e:
                print(f"Cars24 card error: {e}")

        return listings

    async def _extract(self, page, card) -> Optional[Dict]:
        url = await card.get_attribute("href") or ""
        full_url = f"https://www.cars24.com{url}" if url.startswith("/") else url
        source_id = url.rstrip("/").split("/")[-1] if url else ""

        card_text = await card.inner_text()
        lines = [l.strip() for l in card_text.split("\n") if l.strip()]

        title = ""
        year = None
        for line in lines:
            if re.match(r"^(20\d{2})\s", line):
                title = line
                year = int(re.match(r"^(20\d{2})", line).group(1))
                break

        brand, model = self.extract_brand_model(title)

        price_el = await card.query_selector('[class*="priceWrap"]')
        price_str = await price_el.inner_text() if price_el else ""
        # Cars24 shows two prices: display price (₹X.XXL) and actual price (₹X.XX lakh)
        # Take the one with "lakh" spelled out as the actual price
        price_lines = [l.strip() for l in price_str.split("\n") if l.strip()]
        if len(price_lines) > 1:
            actual_price = next((l for l in price_lines if "lakh" in l.lower()), price_lines[-1])
        else:
            actual_price = price_str
        price = self._format_price(actual_price)

        detail_text = " ".join(lines)

        img_el = await card.query_selector("img[src*='cars24'], img[src*='c24']")
        img_url = await img_el.get_attribute("src") if img_el else None
        if not img_url:
            img_el = await card.query_selector("img")
            img_url = await img_el.get_attribute("src") if img_el else None

        fuel_type = None
        for f in ["Petrol", "Diesel", "CNG", "Electric", "Hybrid"]:
            if f in detail_text:
                fuel_type = f
                break

        transmission = None
        if "Automatic" in detail_text:
            transmission = "Automatic"
        elif "Manual" in detail_text:
            transmission = "Manual"

        mileage = self._extract_mileage(detail_text)

        return {
            "source_id": source_id,
            "title": title.strip(),
            "brand": brand,
            "model": model,
            "year": year,
            "price": price,
            "mileage": mileage,
            "listing_url": full_url,
            "image_urls": [img_url] if img_url else [],
            "description": detail_text.strip(),
            "fuel_type": fuel_type,
            "transmission": transmission,
        }

    def _extract_mileage(self, text: str) -> Optional[int]:
        match = re.search(r'([\d,]+)\s*km', text)
        if match:
            return int(match.group(1).replace(",", ""))
        return None
