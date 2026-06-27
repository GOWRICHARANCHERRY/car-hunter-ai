import re
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class CarWaleScraper(BaseScraper):
    source_name = "CarWale"

    async def scrape_listings(self, page, session) -> List[Dict]:
        listings = []
        await page.goto("https://www.carwale.com/used/", timeout=60000)
        await page.wait_for_timeout(5000)

        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

        print(f"[CarWale] URL: {page.url}, Title: {await page.title()}", flush=True)
        cards = await page.query_selector_all(
            '[class*="UsedCarCard-module-scss-module"]'
        )

        for card in cards[:30]:
            try:
                data = await self._extract(page, card)
                if data and data.get("price"):
                    listings.append(data)
            except Exception:
                pass

        return listings

    async def _extract(self, page, card) -> Optional[Dict]:
        link_el = await card.query_selector("a[href]")
        url = await link_el.get_attribute("href") if link_el else ""
        full_url = url if url.startswith("http") else f"https://www.carwale.com{url}"
        source_id = url.rstrip("/").split("/")[-1] if url else ""

        card_text = (await card.inner_text()).replace("\u00a0", " ").strip()
        card_text = re.sub(r'\s+', ' ', card_text)

        if card_text.startswith("Used "):
            card_text = card_text[5:]

        km_match = re.search(r'([\d,]+)\s*km', card_text, re.IGNORECASE)
        mileage = int(km_match.group(1).replace(",", "")) if km_match else None

        parts = [p.strip() for p in card_text.split("|")]

        title = parts[0].strip() if parts else ""
        if km_match:
            title = title[: km_match.start()].strip()
            if title.endswith(","):
                title = title[:-1].strip()

        fuel_type = parts[1].strip() if len(parts) > 1 else None
        location = parts[2].strip() if len(parts) > 2 else ""
        if location:
            location = location.split("Rs.")[0].strip()
            location = re.sub(r'\s+Rs\.?\s*.*$', '', location).strip()

        price_str = ""
        price_match = re.search(r'Rs\.\s*([\d,]+\.?\d*)\s*(Lakh|Crore|K|Lac)', card_text, re.IGNORECASE)
        if price_match:
            price_str = f"Rs. {price_match.group(1)} {price_match.group(2)}"

        year = self.extract_year(title)

        brand, model = self.extract_brand_model(title)

        transmission = None
        if "Automatic" in card_text or "AMT" in card_text or "DCT" in card_text:
            transmission = "Automatic"
        elif "Manual" in card_text or "MT" in card_text:
            transmission = "Manual"

        img_el = await card.query_selector("img")
        img_url = await img_el.get_attribute("src") if img_el else None

        return {
            "source_id": source_id,
            "title": title.strip(),
            "brand": brand,
            "model": model,
            "year": year,
            "price": self._format_price(price_str),
            "mileage": mileage,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "listing_url": full_url,
            "image_urls": [img_url] if img_url else [],
            "description": card_text.strip(),
            "location": location,
        }
