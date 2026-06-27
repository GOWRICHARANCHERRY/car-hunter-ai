import re
import json
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class SpinnyScraper(BaseScraper):
    source_name = "Spinny"
    needs_browser = True

    async def scrape_listings(self, page=None, session=None) -> List[Dict]:
        listings = []
        if not page:
            return listings

        try:
            await page.goto(
                "https://www.spinny.com/used--cars-in-delhi-ncr/s/",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await page.wait_for_timeout(5000)
            try:
                await page.wait_for_selector('[class*="CarListingCard"]', timeout=15000)
            except Exception:
                pass
            await page.wait_for_timeout(2000)
            html = await page.content()
        except Exception as e:
            print(f"[Spinny] Page load error: {e}", flush=True)
            return []

        cards_found = re.findall(
            r'class="[^"]*CarListingCard[^"]*"[^>]*>.*?</(?:a|div)>\s*</(?:a|div)>',
            html,
            re.DOTALL,
        )

        if not cards_found:
            cards_found = html.split('class="CarListingCardV2__')[1:]
            cards_found = [c.split("</")[0] for c in cards_found[:30]]

        if not cards_found:
            state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\}),\s*window\.', html, re.DOTALL)
            if state_match:
                js_str = state_match.group(1)
                js_str = js_str.replace('!0', 'true').replace('!1', 'false')
                js_str = re.sub(r'void\s+0', 'null', js_str)
                js_str = re.sub(r'\bundefined\b', 'null', js_str)
                try:
                    state = json.loads(js_str)
                    for section in state.values():
                        if isinstance(section, dict):
                            for data_list in section.values():
                                if isinstance(data_list, list) and len(data_list) > 0 and isinstance(data_list[0], dict):
                                    for item in data_list:
                                        d = self._js_extract(item)
                                        if d and d.get("price"):
                                            listings.append(d)
                except (json.JSONDecodeError, Exception) as e:
                    print(f"[Spinny] State parse error: {e}", flush=True)

        for card_html in cards_found[:50]:
            try:
                data = self._extract(card_html)
                if data and data.get("price"):
                    listings.append(data)
            except Exception as e:
                print(f"[Spinny] card error: {e}", flush=True)

        print(f"[Spinny] Found {len(cards_found)} card blocks, extracted {len(listings)} listings", flush=True)
        return listings

    def _js_extract(self, item: dict) -> Optional[Dict]:
        name = item.get("name") or item.get("title") or item.get("carName", "")
        if not name:
            return None
        price = item.get("priceNumeric") or item.get("price")
        if not price:
            return None
        if isinstance(price, str):
            price = self._format_price(price)
        full_url = item.get("url") or item.get("link", "")
        listing_url = full_url if full_url.startswith("http") else f"https://www.spinny.com{full_url}" if full_url else ""
        source_id = item.get("id") or item.get("stockId") or item.get("uuid", "")

        year = item.get("year") or item.get("makeYear")
        mileage = item.get("kilometer") or item.get("kmNumeric") or item.get("odometer")
        fuel_type = item.get("fuelType") or item.get("fuel", "")
        transmission = item.get("transmission") or item.get("transmissionType", "")
        city = item.get("city") or item.get("cityName", "")
        owners = item.get("ownerNumber") or item.get("owners", "")
        img_url = item.get("imageUrl") or item.get("image", item.get("imageUrls", [None])[0] if isinstance(item.get("imageUrls"), list) else None)
        brand = item.get("brand") or item.get("makeName", "")
        model = item.get("model") or item.get("modelName", "")
        registration = item.get("registrationNumber") or item.get("registration", "")
        color = item.get("color", "")

        return {
            "source_id": source_id,
            "title": str(name)[:200],
            "brand": brand,
            "model": model,
            "year": year,
            "price": price,
            "mileage": mileage,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "listing_url": listing_url,
            "image_urls": [img_url] if img_url else [],
            "description": str(name)[:300],
            "city": city,
            "owners": owners,
            "registration": registration,
            "color": color,
        }

    def _extract(self, card_html: str) -> Optional[Dict]:
        card_text = re.sub(r'<[^>]+>', ' ', card_html)
        card_text = re.sub(r'\s+', ' ', card_text).strip()

        link_match = re.search(r'href="([^"]+)"', card_html)
        url = link_match.group(1).strip() if link_match else ""
        full_url = url if url.startswith("http") else f"https://www.spinny.com{url}"
        source_id = url.rstrip("/").split("/")[-1] if url else ""

        title = ""
        yr = self.extract_year(card_text)
        for sep in ["Used", "used", "Year"]:
            if sep in card_text:
                parts = card_text.split(sep, 1)
                title = parts[0].strip()
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
            "year": yr,
            "price": price,
            "mileage": mileage,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "listing_url": full_url,
            "image_urls": [img_url] if img_url else [],
            "description": card_text.strip()[:300],
            "location": location,
        }
