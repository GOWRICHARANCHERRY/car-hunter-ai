import re
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class OLXScraper(BaseScraper):
    source_name = "OLX"
    needs_browser = False

    async def scrape_listings(self, page=None, session=None) -> List[Dict]:
        import httpx
        listings = []

        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(
                    "https://www.olx.in/cars/",
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/125.0.0.0 Safari/537.36"
                        ),
                    },
                )
                html = resp.text
        except httpx.TimeoutException:
            print("[OLX] HTTP timeout - OLX may be blocking")
            return []
        except Exception as e:
            err_msg = str(e) or type(e).__name__
            print(f"[OLX] HTTP fetch failed: {err_msg}")
            return []

        items = re.findall(
            r'<li[^>]*data-aut-id="itemBox2"[^>]*>(.*?)</li>',
            html,
            re.DOTALL,
        )

        for item_html in items[:30]:
            try:
                data = self._extract(item_html)
                if data and data.get("price"):
                    listings.append(data)
            except Exception as e:
                print(f"[OLX] card error: {e}")

        return listings

    def _extract(self, item_html: str) -> Optional[Dict]:
        url_match = re.search(r'<a\s+class=""\s+href="([^"]+)"', item_html)
        url = url_match.group(1).strip() if url_match else ""

        title_match = re.search(
            r'data-aut-id="itemTitle"[^>]*>\s*(.*?)\s*<', item_html
        )
        title = title_match.group(1).strip() if title_match else ""

        price_match = re.search(
            r'data-aut-id="itemPrice"[^>]*>\s*(.*?)\s*<', item_html
        )
        price_str = price_match.group(1).strip() if price_match else ""

        subtitle_match = re.search(
            r'data-aut-id="itemSubTitle"[^>]*>\s*(.*?)\s*<', item_html
        )
        subtitle = subtitle_match.group(1).strip() if subtitle_match else ""

        img_match = re.search(
            r'<img[^>]*src="([^"]+)"', item_html
        )
        img_url = str(img_match.group(1)) if img_match else None

        brand, model = self.extract_brand_model(title)
        full_url = url if url.startswith("http") else f"https://www.olx.in{url}"
        source_id = url.split("iid-")[-1] if "iid-" in url else url.split("/")[-1]

        year = None
        mileage = None
        if subtitle:
            parts = subtitle.split("-")
            yr_match = re.search(r'\b(20\d{2})\b', parts[0] if parts else subtitle)
            if yr_match:
                year = int(yr_match.group(1))
            km_str = parts[1] if len(parts) > 1 else subtitle
            km_match = re.search(r'([\d,]+)\s*km', km_str, re.IGNORECASE)
            if km_match:
                mileage = int(km_match.group(1).replace(",", ""))

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
        }
