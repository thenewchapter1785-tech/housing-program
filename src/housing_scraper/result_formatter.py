from typing import List

from .models import Listing


class ResultFormatter:
    def format_listing(self, listing: Listing, show_badges: bool = True) -> str:
        """
        Format a single listing with friendly, user-readable output.
        
        Args:
            listing: The listing to format
            show_badges: Whether to show availability badges
        """
        # Build badges for friendly features
        badges = []
        if listing.voucher_friendly:
            badges.append("✓ Accepts Housing Vouchers")
        if listing.record_friendly:
            badges.append("✓ Second-Chance Housing")
        
        badge_section = (
            "\n  Available For:\n    " + "\n    ".join(badges) 
            if badges 
            else ""
        )

        lines = [
            f"📍 {listing.title}",
            f"   Price: {listing.price or 'Contact for pricing'}",
            f"   Location: {listing.location or 'Not specified'}",
            f"   From: {listing.source.title()}",
            f"   {listing.description or 'Housing listing'}{badge_section}",
            f"   Link: {listing.url}",
        ]
        return "\n".join(lines)

    def format_results(self, listings: List[Listing]) -> str:
        """Format multiple listings with friendly output."""
        if not listings:
            return "\n❌ No listings found matching your criteria.\nTry adjusting your filters or search terms."
        
        header = f"\n✓ Found {len(listings)} matching housing options:\n"
        header += "=" * 70 + "\n"
        formatted = [self.format_listing(listing) for listing in listings]
        return header + "\n\n".join(formatted) + "\n" + "=" * 70
