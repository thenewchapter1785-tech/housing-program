from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class RentalsScraper(BaseScraper):
    name = "rentals"

    def scrape(self, city: str, query: str) -> List[Listing]:
        search_url = f"https://www.rentals.com/{city.lower().replace(' ', '-')}/?q={query.replace(' ', '+')}"
        response = requests.get(search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        listings: List[Listing] = []
        for card in soup.select("a[href*='/rentals/']")[:6]:
            title = card.get_text(" ", strip=True)
            href = card.get("href") or ""
            full_url = href if href.startswith("http") else f"https://www.rentals.com{href}"
            if title:
                listings.append(
                    Listing(
                        title=title,
                        url=full_url,
                        source=self.name,
                        price=None,
                        location=city,
                        description="Rentals.com listing",
                        voucher_friendly=True,
                        record_friendly=True,
                        tags=["voucher", "record-friendly"],
                    )
                )
        return listings
