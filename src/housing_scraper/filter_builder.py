"""
User-friendly filter builder for housing search.
Guides users through simple questions instead of technical parameters.
"""

from typing import List, Optional, Dict, Any
from .models import Listing


class FilterBuilder:
    """Interactive, plain-language filter builder for users of any technical level."""

    def __init__(self):
        self.voucher_accepted = None
        self.record_friendly = None
        self.max_price = None
        self.bedrooms = None
        self.min_price = None

    def clear(self):
        """Reset all filters."""
        self.voucher_accepted = None
        self.record_friendly = None
        self.max_price = None
        self.bedrooms = None
        self.min_price = None

    def simple_yes_no(self, question: str, default: str = "n") -> bool:
        """Ask a simple yes/no question."""
        default_display = "[Y/n]" if default.lower() in ["y", "yes"] else "[y/N]"
        response = (
            input(f"\n{question} {default_display}: ").strip().lower()
        )
        if not response:
            return default.lower() in ["y", "yes"]
        return response in ["y", "yes", "1", "true"]

    def interactive_setup(self) -> None:
        """Walk user through filter setup with friendly language."""
        print("\n" + "=" * 70)
        print("HOUSING FILTER SETUP - Let's find the right place for you!")
        print("=" * 70)

        # Section 1: Housing Assistance
        print("\n[STEP 1/3] Do you receive any housing assistance?")
        print("(This helps us find landlords who accept housing vouchers)")
        self.voucher_accepted = self.simple_yes_no(
            "Do you use a housing voucher or Section 8 assistance?"
        )

        # Section 2: Background/Record Concerns
        print("\n[STEP 2/3] Background and Record Questions")
        print(
            "(We can help find landlords who are open to giving people a second chance)"
        )
        self.record_friendly = self.simple_yes_no(
            "Are you looking for housing that's open to people with a record or background concerns?"
        )

        # Section 3: Budget
        print("\n[STEP 3/3] Budget")
        while True:
            try:
                price_input = input(
                    "\nWhat's your monthly budget for rent? (enter amount, e.g., 1000) [skip]: "
                ).strip()
                if not price_input:
                    print("✓ No price limit set")
                    break
                self.max_price = int(price_input)
                print(f"✓ Looking for rentals up to ${self.max_price}/month")
                break
            except ValueError:
                print("❌ Please enter a valid number (e.g., 1000 or 1500)")

    def quick_preset(self) -> None:
        """Quick preset selection for common scenarios."""
        print("\n" + "=" * 70)
        print("QUICK PRESETS - Choose your situation:")
        print("=" * 70)
        print("\n1. I get housing assistance (Section 8 / Housing Voucher)")
        print("2. I need second-chance housing (record/background friendly)")
        print("3. Both - I get assistance AND need second-chance housing")
        print("4. General search (no special requirements)")
        print("5. Custom filters (I'll answer detailed questions)")

        choice = input("\nChoose 1-5: ").strip()

        if choice == "1":
            self.voucher_accepted = True
            self.record_friendly = False
            print("✓ Set to show housing that accepts Section 8 vouchers")
        elif choice == "2":
            self.voucher_accepted = False
            self.record_friendly = True
            print("✓ Set to show second-chance / record-friendly housing")
        elif choice == "3":
            self.voucher_accepted = True
            self.record_friendly = True
            print("✓ Set to show housing that accepts vouchers AND is record-friendly")
        elif choice == "4":
            self.clear()
            print("✓ Showing all available housing")
        elif choice == "5":
            self.interactive_setup()
        else:
            print("Invalid choice. Showing all housing.")
            self.clear()

    def apply_to_listings(self, listings: List[Listing]) -> List[Listing]:
        """Filter listings based on user preferences."""
        filtered = []

        for listing in listings:
            include = True

            # Check voucher requirement
            if self.voucher_accepted is not None:
                if self.voucher_accepted and not listing.voucher_friendly:
                    include = False
                elif (
                    not self.voucher_accepted
                    and listing.voucher_friendly
                    and not listing.record_friendly
                ):
                    # Exclude if explicitly showing only record-friendly
                    pass

            # Check record-friendly requirement
            if self.record_friendly is not None and include:
                if self.record_friendly and not listing.record_friendly:
                    include = False

            # Check max price
            if self.max_price is not None and include:
                try:
                    price_str = str(listing.price or "").replace("$", "").replace(",", "")
                    if price_str and price_str.isdigit():
                        price_value = int(price_str.split("/")[0])  # Handle "$/month"
                        if price_value > self.max_price:
                            include = False
                except (ValueError, IndexError):
                    pass

            if include:
                filtered.append(listing)

        return filtered

    def get_status(self) -> str:
        """Return readable status of current filters."""
        status_parts = []

        if self.voucher_accepted:
            status_parts.append("Accepts housing vouchers")
        if self.record_friendly:
            status_parts.append("Record-friendly")
        if self.max_price:
            status_parts.append(f"Max ${self.max_price}/month")

        if not status_parts:
            return "No filters active (showing all housing)"
        return " • ".join(status_parts)

    def show_summary(self) -> None:
        """Show user-friendly summary of active filters."""
        print("\n" + "-" * 70)
        print("ACTIVE FILTERS:")
        print(f"  {self.get_status()}")
        print("-" * 70)
