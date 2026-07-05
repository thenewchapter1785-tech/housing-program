from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class ZillowScraper(BaseScraper):
    name = "zillow"

    def scrape(self, city: str, query: str) -> List[Listing]:
        search_url = f"https://www.zillow.com/homes/{city.lower().replace(' ', '-')}/"
        response = requests.get(
            search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        listings: List[Listing] = []

        # Parse Zillow home listings
        for card in soup.select(
            "[class*='ListItem'], [class*='PropertyCard'], article"
        )[:10]:
            try:
                title_elem = card.select_one(
                    "h2, [class*='title'], [class*='address']"
                )
                price_elem = card.select_one("[class*='price'], [class*='amount']")
                link_elem = card.select_one("a[href*='/homes/']")

                title = (
                    title_elem.get_text(strip=True) if title_elem
                    else "Zillow Listing"
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
                    url = f"https://www.zillow.com{url}"

                listings.append(
                    Listing(
                        title=title,
                        url=url,
                        source=self.name,
                        price=price,
                        location=city,
                        description="Zillow home listing",
                        voucher_friendly=False,
                        record_friendly=False,
                        tags=["real-estate", "market-rate"],
                    )
                )
            except Exception:
                continue

        return listings if listings else []
