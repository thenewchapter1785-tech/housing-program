from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class RightmoveScraper(BaseScraper):
    name = "rightmove"

    def scrape(self, city: str, query: str) -> List[Listing]:
        search_url = f"https://www.rightmove.co.uk/property-for-rent/find.html?locationIdentifier=REGION%3A{city.lower().replace(' ', '+')}&maxBedrooms=2&minBedrooms=1"
        response = requests.get(
            search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        listings: List[Listing] = []

        # Parse Rightmove UK property listings
        for card in soup.select(
            "[data-test-id='property-card'], li.propertyCard, article"
        )[:10]:
            try:
                title_elem = card.select_one(
                    "h2, [class*='title'], [class*='address']"
                )
                price_elem = card.select_one("[class*='price'], .propertyPrice")
                link_elem = card.select_one("a[href*='/properties/']")

                title = (
                    title_elem.get_text(strip=True) if title_elem
                    else "Rightmove Property"
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
                    url = f"https://www.rightmove.co.uk{url}"

                listings.append(
                    Listing(
                        title=title,
                        url=url,
                        source=self.name,
                        price=price,
                        location=city,
                        description="Rightmove UK rental property",
                        voucher_friendly=False,
                        record_friendly=False,
                        tags=["rightmove", "uk-market"],
                    )
                )
            except Exception:
                continue

        return listings if listings else []
