import re
import asyncio
import cloudscraper
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class Cars24Scraper(BaseScraper):
    source_name = "Cars24"

    async def scrape_listings(self, page, session) -> List[Dict]:
        listings = []
        try:
            scraper = cloudscraper.create_scraper()
            resp = await asyncio.to_thread(
                scraper.get,
                "https://www.cars24.com/buy-used-cars-bangalore/",
                timeout=60,
            )
            html = resp.text
            status = resp.status_code
            length = len(html)

            cloudflare = "Attention Required" in html or "Just a moment" in html or "cf-browser-verification" in html
            if cloudflare:
                print(f"[Cars24] CLOUDFLARE BLOCKED (status={status}, length={length})", flush=True)
            else:
                has_next = "__NEXT_DATA__" in html
                card_count = len(re.findall(r'carCardWrapper', html))
                print(f"[Cars24] OK (status={status}, length={length}, has_next={has_next}, carCardWrapper mentions={card_count})", flush=True)
        except Exception as e:
            print(f"[Cars24] Fetch failed: {e}", flush=True)
            return []

        card_pattern = re.compile(
            r'<a\s[^>]*class="[^"]*carCardWrapper[^"]*"[^>]*href="([^"]+)"[^>]*>'
            r'.*?styles_priceWrap[^>]*>\s*([^<]+)\s*<',
            re.DOTALL,
        )

        found = 0
        for match in card_pattern.finditer(html):
            found += 1
            try:
                data = self._extract(match)
                if data and data.get("price"):
                    listings.append(data)
            except Exception as e:
                print(f"[Cars24] card error #{found}: {e}", flush=True)

        print(f"[Cars24] Regex matched {found} cards, extracted {len(listings)}", flush=True)
        return listings

    def _extract(self, match: re.Match) -> Optional[Dict]:
        url = match.group(1).strip()
        full_url = f"https://www.cars24.com{url}" if url.startswith("/") else url
        source_id = url.rstrip("/").split("/")[-1] if url else ""

        price_raw = match.group(2).strip()
        price_lines = [l.strip() for l in price_raw.split("\n") if l.strip()]
        actual_price = (
            next((l for l in price_lines if "lakh" in l.lower()), price_lines[-1])
            if len(price_lines) > 1
            else price_raw
        )
        price = self._format_price(actual_price)

        card_html = match.group(0)
        text = re.sub(r'<[^>]+>', ' ', card_html)
        text = re.sub(r'\s+', ' ', text).strip()

        title = ""
        year = None
        for line in text.split("Cars24 Owned Stock"):
            line = line.strip()
            if not line:
                continue
            yr_match = re.search(r'\b(20\d{2})\b', line)
            if yr_match:
                title = line.split("EMI")[0].strip() if "EMI" in line else line
                year = int(yr_match.group(1))
                break

        if not year:
            yr_match = re.search(r'\b(20\d{2})\b', text)
            if yr_match:
                year = int(yr_match.group(1))
                yr_pos = yr_match.start()
                title = text[yr_pos:].split("EMI")[0].strip() if "EMI" in text else text[yr_pos:].split("₹")[0].strip()

        brand, model = self.extract_brand_model(title)

        mileage = None
        km_match = re.search(r'([\d,]+)\s*km', text, re.IGNORECASE)
        if km_match:
            mileage = int(km_match.group(1).replace(",", ""))

        fuel_type = None
        for f in ["Petrol", "Diesel", "CNG", "Electric", "Hybrid"]:
            if f in text:
                fuel_type = f
                break

        transmission = None
        if "Automatic" in text:
            transmission = "Automatic"
        elif "Manual" in text:
            transmission = "Manual"

        img_match = re.search(r'<img[^>]*src="([^"]+)"', card_html)
        img_url = img_match.group(1) if img_match else None

        return {
            "source_id": source_id,
            "title": title.strip()[:100],
            "brand": brand,
            "model": model,
            "year": year,
            "price": price,
            "mileage": mileage,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "listing_url": full_url,
            "image_urls": [img_url] if img_url else [],
            "description": text.strip()[:300],
        }
