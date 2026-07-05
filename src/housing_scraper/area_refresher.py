import os
import threading
import time
from typing import List

from .collector import Collector
from .master_listing_db import MasterListingDatabase


class AreaRefreshScheduler:
    """Background scheduler that refreshes tracked areas into master listings."""

    def __init__(self, master_db: MasterListingDatabase):
        self.master_db = master_db
        self.collector = Collector()
        self.providers: List[str] = os.getenv(
            "AUTO_REFRESH_PROVIDERS", "craigslist,rentals,padmapper,rightmove"
        ).split(",")
        self.providers = [provider.strip() for provider in self.providers if provider.strip()]
        self._stop_event = threading.Event()

    def refresh_area(self, area_name: str) -> int:
        """Refresh one area and return number of records processed."""
        listings = self.collector.run(
            providers=self.providers,
            city=area_name,
            query=os.getenv("AUTO_REFRESH_QUERY", "apartment"),
        )

        count = 0
        for listing in listings:
            self.master_db.add_or_update_listing(
                title=listing.title,
                location=listing.location or area_name,
                price=listing.price,
                description=listing.description,
                url=listing.url,
                source=listing.source,
                voucher_friendly=listing.voucher_friendly,
                record_friendly=listing.record_friendly,
            )
            count += 1

        self.master_db.mark_area_scraped(area_name)
        return count

    def run_once(self) -> int:
        """Run one scheduler cycle across all due areas."""
        total = 0
        for area in self.master_db.list_due_areas():
            try:
                total += self.refresh_area(area["area_name"])
            except Exception as exc:
                print(f"Area refresh failed for {area['area_name']}: {exc}")
        return total

    def run_forever(self, interval_seconds: int = 900) -> None:
        """Run scheduler loop until stopped."""
        while not self._stop_event.is_set():
            self.run_once()
            self._stop_event.wait(timeout=interval_seconds)

    def stop(self) -> None:
        self._stop_event.set()
