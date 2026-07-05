from typing import List

from .models import Listing


def apply_filters(listings: List[Listing]) -> List[Listing]:
    filtered: List[Listing] = []
    for listing in listings:
        text = " ".join(
            [listing.title or "", listing.description or "", listing.location or "", " ".join(listing.tags)]
        ).lower()

        voucher_keywords = ["voucher", "section 8", "housing choice", "assistance", "accepts vouchers"]
        record_keywords = ["background", "felony", "record", "reentry", "second chance", "no background"]

        listing.voucher_friendly = any(keyword in text for keyword in voucher_keywords)
        listing.record_friendly = any(keyword in text for keyword in record_keywords)

        if listing.voucher_friendly or listing.record_friendly:
            filtered.append(listing)

    return filtered
