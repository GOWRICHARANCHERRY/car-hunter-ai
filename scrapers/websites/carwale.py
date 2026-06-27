import re
import json
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class CarWaleScraper(BaseScraper):
    source_name = "CarWale"
    needs_browser = False

    CITIES = [
        ("delhi", 10), ("mumbai", 11), ("bangalore", 12), ("hyderabad", 13),
    ]

    BRANDS = [
        ("maruti-suzuki", 10), ("hyundai", 11), ("honda", 12), ("toyota", 13),
        ("mahindra", 14), ("tata", 15),
    ]

    async def scrape_listings(self, page=None, session=None) -> List[Dict]:
        import httpx
        listings = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.carwale.com/used/search/",
                "X-Requested-With": "XMLHttpRequest",
            }

            for city_name, city_id in self.CITIES:
                for brand_name, brand_id in self.BRANDS:
                    try:
                        await self._fetch_brand_city(
                            client, headers, listings, city_name, city_id, brand_name, brand_id
                        )
                    except Exception as e:
                        print(f"[CarWale] {brand_name}/{city_name} error: {e}", flush=True)

        print(f"[CarWale] Extracted {len(listings)} listings total", flush=True)
        return listings

    async def _fetch_brand_city(self, client, headers, listings,
                                 city_name: str, city_id: int,
                                 brand_name: str, brand_id: int):
        url = f"/api/stocks/?pn=1&car={brand_id}&city={city_id}&ps=24&sc=-1&so=-1&lcr=24"
        resp = await client.get(f"https://www.carwale.com{url}", headers=headers)
        if resp.status_code != 200:
            return
        data = resp.json()
        stocks = data.get("stocks", [])
        if not stocks:
            return
        for stock in stocks:
            item = self._parse_stock(stock, city_name)
            if item and item.get("price"):
                listings.append(item)
        next_url = data.get("nextPageUrl")
        page = 2
        while next_url and page <= 3:
            try:
                full_url = next_url if next_url.startswith("http") else f"https://www.carwale.com{next_url}"
                resp = await client.get(full_url, headers=headers)
                if resp.status_code != 200:
                    break
                data = resp.json()
                stocks = data.get("stocks", [])
                for stock in stocks:
                    item = self._parse_stock(stock, city_name)
                    if item and item.get("price"):
                        listings.append(item)
                next_url = data.get("nextPageUrl")
                page += 1
            except Exception as e:
                print(f"[CarWale] page {page} error: {e}", flush=True)
                break

    def _parse_stock(self, stock: dict, city_name: str) -> Optional[Dict]:
        title = stock.get("carName", "").strip()
        if not title:
            return None
        price_numeric = stock.get("priceNumeric") or stock.get("price")
        if not price_numeric:
            return None
        price_str = stock.get("price", str(price_numeric))
        price = self._format_price(price_str) or price_numeric

        full_url = stock.get("url", "")
        listing_url = full_url if full_url.startswith("http") else f"https://www.carwale.com{full_url}"
        source_id = stock.get("stockId") or (full_url.rstrip("/").split("/")[-1] if full_url else "")

        brand = stock.get("makeName", "")
        model = stock.get("modelName", "")
        year = stock.get("makeYear")
        mileage = stock.get("kmNumeric")
        if mileage and isinstance(mileage, str):
            mileage = int(mileage.replace(",", ""))
        fuel_type = stock.get("fuel", "")
        transmission = stock.get("transmission", "")
        location = stock.get("areaName", "")
        city = stock.get("cityName", city_name.capitalize())
        owners = stock.get("ownersId")
        color = stock.get("color")
        registration = stock.get("registrationNumber")
        insurance = stock.get("insurance")
        img_url = stock.get("imageUrl")

        return {
            "source_id": source_id,
            "title": title[:200],
            "brand": brand,
            "model": model,
            "year": year,
            "price": price,
            "mileage": mileage,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "listing_url": listing_url,
            "image_urls": [img_url] if img_url else [],
            "description": f"{brand} {model} {stock.get('versionName', '')}".strip()[:300],
            "location": location,
            "city": city,
            "owners": owners,
            "color": color,
            "registration": registration,
            "insurance": insurance,
        }
