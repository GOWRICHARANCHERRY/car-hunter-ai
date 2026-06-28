import re
import json
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class Cars24Scraper(BaseScraper):
    source_name = "Cars24"
    needs_browser = True

    async def scrape_listings(self, page=None, session=None) -> List[Dict]:
        listings = []
        if not page:
            return listings

        api_responses = []

        async def handle_response(response):
            url = response.url
            if "/api/" in url and response.ok:
                try:
                    body = await response.json()
                    api_responses.append(body)
                except Exception:
                    pass

        page.on("response", handle_response)

        cities = ["delhi", "bangalore", "mumbai", "pune"]
        for city in cities:
            try:
                await page.goto(
                    f"https://www.cars24.com/buy-used-cars-{city}/",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                await page.wait_for_timeout(8000)

                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)

                html = await page.content()

                for resp_data in api_responses:
                    parsed = self._parse_api_response(resp_data, city)
                    for item in parsed:
                        if item.get("price"):
                            listings.append(item)
                api_responses.clear()

                cards = await page.query_selector_all('[class*="Card"], [class*="card"], [class*="listing"], [class*="Item"], [data-testid*="card"]')
                if cards:
                    for card in cards[:30]:
                        try:
                            html_snippet = await card.inner_html()
                            data = self._extract(html_snippet)
                            if data and data.get("price"):
                                listings.append(data)
                        except Exception:
                            continue

                state_data = await page.evaluate("""
                    () => {
                        try {
                            const scripts = document.querySelectorAll('script');
                            for (const s of scripts) {
                                if (s.text.includes('__NEXT_DATA__') || s.text.includes('window.__')) {
                                    return s.text;
                                }
                            }
                        } catch(e) {}
                        return null;
                    }
                """)
                if state_data:
                    import re as re2
                    match = re2.search(r'({.*})', state_data, re2.DOTALL)
                    if match:
                        try:
                            state = json.loads(match.group(1))
                            for key in ["props", "pageProps", "cars", "listings", "results", "items", "data"]:
                                if isinstance(state.get(key), list):
                                    for item in state[key]:
                                        d = self._js_extract(item, city)
                                        if d and d.get("price"):
                                            listings.append(d)
                        except Exception:
                            pass

            except Exception as e:
                print(f"[Cars24] {city} error: {e}", flush=True)
                continue

        seen = set()
        unique = []
        for item in listings:
            sid = item.get("source_id", "")
            if sid and sid not in seen:
                seen.add(sid)
                unique.append(item)

        print(f"[Cars24] Extracted {len(unique)} listings from {len(cities)} cities", flush=True)
        return unique

    def _parse_api_response(self, data: dict, city: str) -> List[Dict]:
        results = []
        items = data.get("data") or data.get("results") or data.get("items") or data.get("cars") or []
        if isinstance(items, dict):
            items = items.get("data") or items.get("results") or items.get("items") or items.get("cars") or []
        if isinstance(items, list):
            for item in items:
                d = self._js_extract(item, city)
                if d:
                    results.append(d)
        return results

    def _js_extract(self, item: dict, city: str = "") -> Optional[Dict]:
        if not isinstance(item, dict):
            return None
        title = item.get("title") or item.get("name") or item.get("carName") or item.get("car_name") or ""
        if not title:
            return None
        price = item.get("price") or item.get("priceNumeric") or item.get("price_numeric") or item.get("price_amount", 0)
        if isinstance(price, str):
            price = self._format_price(price)
        if not price:
            return None

        sid = str(item.get("id") or item.get("stockId") or item.get("stock_id") or item.get("uuid") or item.get("car_id") or "")
        listing_url = item.get("url") or item.get("link") or item.get("seo_url") or ""
        if listing_url and not listing_url.startswith("http"):
            listing_url = f"https://www.cars24.com{listing_url}"

        return {
            "source_id": sid,
            "title": str(title)[:200],
            "brand": item.get("brand") or item.get("make") or item.get("make_name") or "",
            "model": item.get("model") or item.get("model_name") or title,
            "year": item.get("year") or item.get("makeYear") or item.get("registration_year") or item.get("reg_year"),
            "price": price,
            "mileage": item.get("kilometer") or item.get("km") or item.get("odometer") or item.get("mileage"),
            "fuel_type": item.get("fuelType") or item.get("fuel_type") or item.get("fuel") or "",
            "transmission": item.get("transmission") or item.get("transmission_type") or "",
            "listing_url": listing_url,
            "image_urls": [item.get("image") or item.get("imageUrl") or item.get("img") or ""] if item.get("image") or item.get("imageUrl") else [],
            "description": str(item.get("description") or item.get("carDescription") or title)[:300],
            "city": item.get("city") or item.get("cityName") or city or "",
            "owners": item.get("ownerNumber") or item.get("owners") or item.get("noOfOwners") or "",
            "registration": item.get("registrationNumber") or item.get("registration") or item.get("reg_number") or "",
            "color": item.get("color") or "",
        }

    def _extract(self, card_html: str) -> Optional[Dict]:
        card_text = re.sub(r'<[^>]+>', ' ', card_html)
        card_text = re.sub(r'\s+', ' ', card_text).strip()
        title = card_text[:100].strip()

        price_str = ""
        price_match = re.search(r'(?:Rs\.?|₹)\s*([\d,]+\.?\d*)\s*(Lakh|Crore|L|K|Thousand)', card_text, re.IGNORECASE)
        if price_match:
            price_str = f"Rs. {price_match.group(1)} {price_match.group(2)}"
        else:
            price_match = re.search(r'(?:Rs\.?|₹)\s*([\d,]+\.?\d*)', card_text)
            if price_match:
                price_str = price_match.group(0)
        price = self._format_price(price_str)

        km_match = re.search(r'([\d,]+)\s*km', card_text, re.IGNORECASE)
        mileage = None
        if km_match:
            try:
                mileage = int(km_match.group(1).replace(",", ""))
            except ValueError:
                pass

        yr = self.extract_year(card_text)
        link_match = re.search(r'href="([^"]+)"', card_html)
        url = link_match.group(1).strip() if link_match else ""
        full_url = url if url.startswith("http") else f"https://www.cars24.com{url}" if url else ""
        img_match = re.search(r'<img[^>]*src="([^"]+)"', card_html)
        img_url = img_match.group(1) if img_match else ""
        source_id = url.rstrip("/").split("/")[-1] if url else ""

        if not price:
            return None

        return {
            "source_id": source_id,
            "title": title[:100],
            "brand": "",
            "model": title[:100],
            "year": yr,
            "price": price,
            "mileage": mileage,
            "fuel_type": "",
            "transmission": "",
            "listing_url": full_url,
            "image_urls": [img_url] if img_url else [],
            "description": card_text[:300],
            "city": "",
        }
