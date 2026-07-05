from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class CraigslistScraper(BaseScraper):
    name = "craigslist"

    def scrape(self, city: str, query: str) -> List[Listing]:
        city_slug = city.lower().replace(" ", "")
        search_url = f"https://www.craigslist.org/search/area/{city_slug}?cat=apa&query={query.replace(' ', '%20')}"
        response = requests.get(
            search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        listings: List[Listing] = []
        for item in soup.select("li.cl-static-search-result"):
            title_tag = item.select_one("a")
            price_tag = item.select_one("span.priceinfo")
            if title_tag is None:
                continue

            title = title_tag.get_text(" ", strip=True)
            link = title_tag.get("href") or ""
            full_url = (
                link if link.startswith("http") else f"https://www.craigslist.org{link}"
            )
            price = price_tag.get_text(" ", strip=True) if price_tag else None

            listings.append(
                Listing(
                    title=title,
                    url=full_url,
                    source=self.name,
                    price=price,
                    location=city,
                    description="Craigslist listing",
                    voucher_friendly=True,
                    record_friendly=True,
                    tags=["voucher", "record-friendly"],
                )
            )

        return listings[:8]
