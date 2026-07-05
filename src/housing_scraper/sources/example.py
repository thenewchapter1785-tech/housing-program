from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class ExampleScraper(BaseScraper):
    name = "example"

    def scrape(self, city: str, query: str) -> List[Listing]:
        url = f"https://example.com/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else "Example listing"

        return [
            Listing(
                title=title,
                url=url,
                source=self.name,
                price="$1200",
                location=city,
                description="Sample listing from the example provider",
                voucher_friendly=True,
                record_friendly=True,
                tags=["voucher", "record-friendly"],
            )
        ]
