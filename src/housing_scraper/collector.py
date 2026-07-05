import json
import os
import time
from typing import List

from .config import settings
from .models import Listing
from .filters import apply_filters
from .sources.provider_catalog import get_scraper_map


class Collector:
    def __init__(self):
        self.settings = settings
        os.makedirs(self.settings.data_dir, exist_ok=True)
        self.scrapers = {
            name: scraper_cls() for name, scraper_cls in get_scraper_map().items()
        }

    def run(self, providers: List[str] | None = None, city: str | None = None, query: str | None = None) -> List[Listing]:
        listings: List[Listing] = []
        providers = providers or ["example"]
        city = city or self.settings.city
        query = query or self.settings.query

        for provider in providers:
            scraper = self.scrapers.get(provider)
            if scraper is None:
                continue
            try:
                fetched = scraper.scrape(city, query)
                listings.extend(fetched)
            except Exception as exc:
                print(f"[{provider}] failed: {exc}")
            time.sleep(self.settings.request_delay_seconds)

        filtered = apply_filters(listings)
        self.save_results(filtered)
        return filtered

    def save_results(self, listings: List[Listing]) -> None:
        output_path = os.path.join(self.settings.data_dir, "listings.json")
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump([listing.to_dict() for listing in listings], handle, indent=2)
