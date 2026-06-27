import re
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class CarWaleScraper(BaseScraper):
    source_name = "CarWale"
    needs_browser = False

    async def scrape_listings(self, page=None, session=None) -> List[Dict]:
        import httpx
        listings = []

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(
                    "https://www.carwale.com/used/",
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/125.0.0.0 Safari/537.36"
                        ),
                    },
                )
                html = resp.text
        except Exception as e:
            err_msg = str(e) or type(e).__name__
            print(f"[CarWale] HTTP fetch failed: {err_msg}", flush=True)
            return []

        card_blocks = re.findall(
            r'class="[^"]*UsedCarCard-module-scss-module[^"]*"[^>]*>.*?</a>\s*</div>',
            html,
            re.DOTALL,
        )

        if not card_blocks:
            card_blocks = html.split('class="UsedCarCard-module-scss-module')[1:]
            card_blocks = ['<div class="UsedCarCard-module-scss-module' + c[:4000] for c in card_blocks]

        for block in card_blocks[:30]:
            try:
                data = self._extract(block)
                if data and data.get("price"):
                    listings.append(data)
            except Exception as e:
                print(f"[CarWale] card error: {e}", flush=True)

        print(f"[CarWale] Found {len(card_blocks)} card blocks, extracted {len(listings)} listings", flush=True)
        return listings

    def _extract(self, block: str) -> Optional[Dict]:
        text = re.sub(r'<[^>]+>', ' ', block)
        text = re.sub(r'\s+', ' ', text).strip()
        if text.startswith("Used "):
            text = text[5:]

        link_match = re.search(r'href="([^"]+)"', block)
        url = link_match.group(1).strip() if link_match else ""
        full_url = url if url.startswith("http") else f"https://www.carwale.com{url}"
        source_id = url.rstrip("/").split("/")[-1] if url else ""

        parts = [p.strip() for p in text.split("|")]

        title = parts[0].strip() if parts else ""
        km_match = re.search(r'([\d,]+)\s*km', title, re.IGNORECASE)
        if km_match:
            title = title[:km_match.start()].strip().rstrip(",").strip()

        fuel_type = parts[1].strip() if len(parts) > 1 else None

        location = parts[2].strip() if len(parts) > 2 else ""
        if location:
            location = re.sub(r'\s*Rs\.?\s*.*$', '', location).strip()

        price_str = ""
        price_match = re.search(r'Rs\.?\s*([\d,]+\.?\d*)\s*(Lakh|Crore|L|K)\b', text, re.IGNORECASE)
        if price_match:
            price_str = f"Rs. {price_match.group(1)} {price_match.group(2)}"

        price = self._format_price(price_str)
        year = self.extract_year(text)

        brand, model = self.extract_brand_model(title)

        transmission = None
        if "Automatic" in text or "AMT" in text or "DCT" in text:
            transmission = "Automatic"
        elif "Manual" in text or "MT" in text:
            transmission = "Manual"

        mileage = None
        km_match2 = re.search(r'([\d,]+)\s*km', text, re.IGNORECASE)
        if km_match2:
            mileage = int(km_match2.group(1).replace(",", ""))

        img_match = re.search(r'<img[^>]*src="([^"]+)"', block)
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
            "location": location,
        }
