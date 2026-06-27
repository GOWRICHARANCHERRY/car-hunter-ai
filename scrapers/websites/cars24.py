import re
from typing import Optional, Dict, List
from scrapers.browsers import BaseScraper


class Cars24Scraper(BaseScraper):
    source_name = "Cars24"

    async def scrape_listings(self, page, session) -> List[Dict]:
        print("[Cars24] Skipped - Cloudflare blocks datacenter IPs on Fly.io", flush=True)
        return []

    def _extract(self, match: re.Match) -> Optional[Dict]:
        return None
