from typing import List

from .models import Listing


def apply_filters(listings: List[Listing]) -> List[Listing]:
    """
    Apply intelligent filtering based on provider flags + keyword detection.
    Respects provider-supplied flags and supplements with keyword scanning.
    """
    filtered: List[Listing] = []
    for listing in listings:
        text = " ".join(
            [
                listing.title or "",
                listing.description or "",
                listing.location or "",
                " ".join(listing.tags),
            ]
        ).lower()

        voucher_keywords = [
            "voucher",
            "section 8",
            "housing choice",
            "assistance",
            "accepts vouchers",
            "hcv",
        ]
        record_keywords = [
            "background",
            "felony",
            "record",
            "reentry",
            "second chance",
            "no background",
            "expunged",
            "deferred adjudication",
        ]

        # Preserve provider-detected flags; supplement with keyword detection
        if not listing.voucher_friendly:
            listing.voucher_friendly = any(
                keyword in text for keyword in voucher_keywords
            )
        if not listing.record_friendly:
            listing.record_friendly = any(
                keyword in text for keyword in record_keywords
            )

        # Include any listing that has been marked as voucher or record friendly
        if listing.voucher_friendly or listing.record_friendly:
            filtered.append(listing)

    return filtered
