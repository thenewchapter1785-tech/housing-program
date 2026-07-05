from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class RightmoveScraper(BaseScraper):
    name = "rightmove"

    def scrape(self, city: str, query: str) -> List[Listing]:
        search_url = f"https://www.rightmove.co.uk/property-for-rent/find.html?locationIdentifier=REGION%3A{city.lower().replace(' ', '+')}&maxBedrooms=2&minBedrooms=1"
        response = requests.get(search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        title = soup.title.get_text(" ", strip=True) if soup.title else "Rightmove page"
        return [
            Listing(
                title=title,
                url=search_url,
                source=self.name,
                price=None,
                location=city,
                description="Rightmove listing context",
                voucher_friendly=True,
                record_friendly=True,
                tags=["voucher", "record-friendly"],
            )
        ]
