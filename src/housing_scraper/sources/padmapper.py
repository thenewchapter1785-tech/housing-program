from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class PadmapperScraper(BaseScraper):
    name = "padmapper"

    def scrape(self, city: str, query: str) -> List[Listing]:
        search_url = f"https://www.padmapper.com/apartments/{city.lower().replace(' ', '-')}/{query.replace(' ', '-')}/"
        response = requests.get(
            search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        listings: List[Listing] = []

        # Parse Padmapper listings
        for card in soup.select(
            "[class*='listing'], [class*='property'], [class*='apartment']"
        )[:10]:
            try:
                title_elem = card.select_one(
                    "h2, h3, [class*='title'], [class*='name']"
                )
                price_elem = card.select_one("[class*='price']")
                link_elem = card.select_one("a[href]")

                title = (
                    title_elem.get_text(strip=True) if title_elem
                    else "Padmapper Listing"
                )
                price = (
                    price_elem.get_text(strip=True) if price_elem
                    else None
                )
                url = (
                    link_elem.get("href", search_url) if link_elem
                    else search_url
                )
                if not url.startswith("http"):
                    url = f"https://www.padmapper.com{url}"

                listings.append(
                    Listing(
                        title=title,
                        url=url,
                        source=self.name,
                        price=price,
                        location=city,
                        description="Padmapper apartment listing",
                        voucher_friendly=False,
                        record_friendly=False,
                        tags=["padmapper", "aggregator"],
                    )
                )
            except Exception:
                continue

        return listings if listings else []
