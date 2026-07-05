from typing import List

from .models import Listing


class ResultFormatter:
    def format_listing(self, listing: Listing) -> str:
        lines = [
            f"Title: {listing.title}",
            f"Source: {listing.source}",
            f"Price: {listing.price or 'N/A'}",
            f"Location: {listing.location or 'N/A'}",
            f"Description: {listing.description or 'N/A'}",
            f"Voucher friendly: {'Yes' if listing.voucher_friendly else 'No'}",
            f"Record friendly: {'Yes' if listing.record_friendly else 'No'}",
            f"URL: {listing.url}",
        ]
        return "\n".join(lines)

    def format_results(self, listings: List[Listing]) -> str:
        if not listings:
            return "No listings found."
        return "\n\n".join(self.format_listing(listing) for listing in listings)
