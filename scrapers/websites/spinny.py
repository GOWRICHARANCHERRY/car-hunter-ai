import re
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class SpinnyScraper(BaseScraper):
    source_name = "Spinny"
    needs_browser = False

    async def scrape_listings(self, page=None, session=None) -> List[Dict]:
        import httpx
        listings = []

        try:
            async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
                resp = await client.get(
                    "https://www.spinny.com/used--cars-in-delhi-ncr/s/",
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
            print(f"[Spinny] HTTP fetch failed: {err_msg}", flush=True)
            return []

        cards_found = re.findall(
            r'class="[^"]*CarListingCardV2[^"]*"[^>]*>.*?</(?:a|div)>\s*</(?:a|div)>',
            html,
            re.DOTALL,
        )

        if not cards_found:
            cards_found = html.split('class="CarListingCardV2__carListingCardV2Root')[1:]
            cards_found = ['<div' + c[:3000] for c in cards_found]

        for card_html in cards_found[:30]:
            try:
                data = self._extract(card_html)
                if data and data.get("price"):
                    listings.append(data)
            except Exception as e:
                print(f"[Spinny] card error: {e}", flush=True)

        print(f"[Spinny] Found {len(cards_found)} card blocks, extracted {len(listings)} listings", flush=True)
        return listings

    def _extract(self, card_html: str) -> Optional[Dict]:
        card_text = re.sub(r'<[^>]+>', ' ', card_html)
        card_text = re.sub(r'\s+', ' ', card_text).strip()

        link_match = re.search(r'href="([^"]+)"', card_html)
        url = link_match.group(1).strip() if link_match else ""
        full_url = url if url.startswith("http") else f"https://www.spinny.com{url}"
        source_id = url.rstrip("/").split("/")[-1] if url else ""

        title = ""
        yr_match = re.search(r'\b(20\d{2})\b', card_text)
        year = int(yr_match.group(1)) if yr_match else None
        for sep in ["Used", "used", "Year"]:
            if sep in card_text:
                parts = card_text.split(sep, 1)
                title = parts[0].strip() if len(parts) > 0 else card_text
                break
        if not title:
            title = card_text[:100].strip()

        brand, model = self.extract_brand_model(title)

        price_str = ""
        price_match = re.search(r'(?:Rs\.?|₹)\s*([\d,]+\.?\d*)\s*(Lakh|Crore|L|K|Thousand)', card_text, re.IGNORECASE)
        if price_match:
            price_str = f"Rs. {price_match.group(1)} {price_match.group(2)}"
        else:
            price_match = re.search(r'(?:Rs\.?|₹)\s*([\d,]+\.?\d*)', card_text)
            if price_match:
                price_str = price_match.group(0)

        price = self._format_price(price_str)

        mileage = None
        km_match = re.search(r'([\d,]+\.?\d*)\s*(?:K\s*)?km', card_text, re.IGNORECASE)
        if km_match:
            val = km_match.group(1).replace(",", "")
            try:
                mileage = int(float(val) * 1000) if "." in val else int(val)
            except ValueError:
                pass

        fuel_type = None
        for f in ["Petrol", "Diesel", "CNG", "Electric", "Hybrid"]:
            if f in card_text:
                fuel_type = f
                break

        transmission = None
        if "Automatic" in card_text or "Auto" in card_text:
            transmission = "Automatic"
        elif "Manual" in card_text:
            transmission = "Manual"

        location = ""
        for kw in ["Delhi", "Bangalore", "Mumbai", "Pune", "Chennai", "Hyderabad", "Kolkata", "Ahmedabad"]:
            if kw in card_text:
                location = kw
                break

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
            "description": card_text.strip()[:300],
            "location": location,
        }
