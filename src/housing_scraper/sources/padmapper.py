from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class PadmapperScraper(BaseScraper):
    name = "padmapper"

    def scrape(self, city: str, query: str) -> List[Listing]:
        search_url = f"https://www.padmapper.com/apartments/{city.lower().replace(' ', '-')}/{query.replace(' ', '-')}/"
        response = requests.get(search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        title = soup.title.get_text(" ", strip=True) if soup.title else "Padmapper page"
        return [
            Listing(
                title=title,
                url=search_url,
                source=self.name,
                price=None,
                location=city,
                description="Padmapper listing context",
                voucher_friendly=True,
                record_friendly=True,
                tags=["voucher", "record-friendly"],
            )
        ]
