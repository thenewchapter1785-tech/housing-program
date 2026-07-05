from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class ZillowScraper(BaseScraper):
    name = "zillow"

    def scrape(self, city: str, query: str) -> List[Listing]:
        search_url = f"https://www.zillow.com/homes/{city.lower().replace(' ', '-')}/"
        response = requests.get(search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        title = soup.title.get_text(" ", strip=True) if soup.title else "Zillow page"
        return [
            Listing(
                title=title,
                url=search_url,
                source=self.name,
                price=None,
                location=city,
                description="Zillow search page",
                voucher_friendly=True,
                record_friendly=True,
                tags=["voucher", "record-friendly"],
            )
        ]
