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

        # Parse Craigslist apartment listing results
        for item in soup.select("li.cl-static-search-result"):
            try:
                title_tag = item.select_one("a")
                price_tag = item.select_one("span.priceinfo")
                nearby_tag = item.select_one("span.nearby")

                if title_tag is None:
                    continue

                title = title_tag.get_text(" ", strip=True)
                link = title_tag.get("href") or ""
                full_url = (
                    link
                    if link.startswith("http")
                    else f"https://www.craigslist.org{link}"
                )
                price = (
                    price_tag.get_text(" ", strip=True) if price_tag
                    else None
                )
                location = (
                    nearby_tag.get_text(" ", strip=True) if nearby_tag
                    else city
                )

                # Check for voucher/record-friendly keywords
                full_text = f"{title} {price or ''} {location or ''}".lower()
                is_voucher = any(
                    kw in full_text
                    for kw in [
                        "voucher",
                        "section 8",
                        "housing choice",
                        "accepts",
                    ]
                )
                is_record = any(
                    kw in full_text
                    for kw in [
                        "background",
                        "felony",
                        "record",
                        "reentry",
                        "second chance",
                    ]
                )

                listings.append(
                    Listing(
                        title=title,
                        url=full_url,
                        source=self.name,
                        price=price,
                        location=location,
                        description="Craigslist apartments listing",
                        voucher_friendly=is_voucher,
                        record_friendly=is_record,
                        tags=["craigslist", "peer-to-peer"],
                    )
                )
            except Exception:
                continue

        return listings[:12]
