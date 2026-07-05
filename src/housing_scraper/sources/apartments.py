from typing import List

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from .base import BaseScraper


class ApartmentsScraper(BaseScraper):
    name = "apartments"

    def scrape(self, city: str, query: str) -> List[Listing]:
        search_url = f"https://www.apartments.com/{city.lower().replace(' ', '-')}/{query.replace(' ', '-')}/"
        response = requests.get(
            search_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        listings: List[Listing] = []

        # Parse apartment listing cards from search results
        for card in soup.select(
            "article, [class*='listing'], [class*='property-card']"
        )[:10]:
            try:
                # Extract title/property name
                title_elem = card.select_one(
                    "h2, h3, [class*='title'], [class*='name']"
                )
                # Extract price
                price_elem = card.select_one(
                    "[class*='price'], [class*='rent'], span.rentLabel"
                )
                # Extract location/address
                address_elem = card.select_one(
                    "[class*='address'], [class*='location']"
                )
                # Extract link
                link_elem = card.select_one("a[href]")

                title = (
                    title_elem.get_text(strip=True) if title_elem
                    else "Apartment Listing"
                )
                price = (
                    price_elem.get_text(strip=True) if price_elem
                    else None
                )
                location = (
                    address_elem.get_text(strip=True) if address_elem
                    else city
                )
                url = (
                    link_elem.get("href", search_url) if link_elem
                    else search_url
                )
                if not url.startswith("http"):
                    url = f"https://www.apartments.com{url}"

                listings.append(
                    Listing(
                        title=title,
                        url=url,
                        source=self.name,
                        price=price,
                        location=location,
                        description="Apartments.com listing",
                        voucher_friendly=True,
                        record_friendly=True,
                        tags=["apartment", "mainstream"],
                    )
                )
            except Exception:
                continue

        return listings if listings else []
