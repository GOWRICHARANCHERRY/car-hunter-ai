import re
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class SpinnyScraper(BaseScraper):
    source_name = "Spinny"

    async def scrape_listings(self, page, session) -> List[Dict]:
        listings = []
        try:
            await page.goto("https://www.spinny.com/used--cars-in-delhi-ncr/s/", timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"[Spinny] goto failed, trying fallback: {e}", flush=True)
            await page.goto("https://www.spinny.com/", timeout=15000, wait_until="domcontentloaded")
            await page.goto("https://www.spinny.com/used--cars-in-delhi-ncr/s/", timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(8000)

        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

        cards = await page.query_selector_all(
            '[class*="CarListingCardV2__carListingCardV2Root"]'
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
        parent_link = await card.evaluate("el => el.closest('a')?.getAttribute('href') || ''")
        url = str(parent_link) if parent_link else ""
        full_url = url if url.startswith("http") else f"https://www.spinny.com{url}"
        source_id = url.rstrip("/").split("/")[-1] if url else ""

        title_el = await card.query_selector(
            'a[class*="ListingBrandModelDetail__makeModelLink"], '
            'span[class*="ListingBrandModelDetail__make"]'
        )
        title = (await title_el.inner_text()).strip() if title_el else ""
        title = title.replace("\u00a0", " ")

        price_el = await card.query_selector(
            'span[class*="ListingBrandModelDetail__priceWithRupeeSymbol"], '
            'li[class*="ListingBrandModelDetail__price"]'
        )
        price_str = (await price_el.inner_text()).strip() if price_el else ""

        variant_el = await card.query_selector(
            'span[class*="ListingPricingDetail__variant"]'
        )
        variant = (await variant_el.inner_text()).strip() if variant_el else ""

        details_el = await card.query_selector(
            'ul[class*="CarListingCardDetail__more"]'
        )
        detail_text = (await details_el.inner_text()).strip() if details_el else ""

        location_el = await card.query_selector(
            'span[class*="HubDetails__hubAddress"]'
        )
        location = (await location_el.inner_text()).strip() if location_el else ""

        brand, model = self.extract_brand_model(title)

        if variant and model:
            model = f"{model} {variant}".strip()

        price = self._format_price(price_str)
        year = self.extract_year(title)

        mileage = None
        match = re.search(r'([\d,]+\.?\d*)\s*K\s*km', detail_text, re.IGNORECASE)
        if match:
            mileage = int(float(match.group(1).replace(",", "")) * 1000)
        else:
            match = re.search(r'([\d,]+)\s*km', detail_text, re.IGNORECASE)
            if match:
                mileage = int(match.group(1).replace(",", ""))

        fuel_type = None
        for f in ["Petrol", "Diesel", "CNG", "Electric", "Hybrid"]:
            if f in detail_text:
                fuel_type = f
                break

        transmission = None
        if "Automatic" in detail_text or "Auto" in detail_text:
            transmission = "Automatic"
        elif "Manual" in detail_text:
            transmission = "Manual"

        img_el = await card.query_selector("img")
        img_url = await img_el.get_attribute("src") if img_el else None

        return {
            "source_id": source_id,
            "title": title.strip(),
            "brand": brand,
            "model": model,
            "year": year,
            "price": price,
            "mileage": mileage,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "listing_url": full_url,
            "image_urls": [img_url] if img_url else [],
            "description": detail_text.strip(),
            "location": location,
        }
