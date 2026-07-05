"""
High-level search management combining database, filtering, and collection.
Simplifies interaction between menu and database layer.
Also updates master listing database with findings.
"""

from typing import List, Optional, Dict, Any
from .models import Listing
from .storage import StorageManager
from .filter_builder import FilterBuilder
from .collector import Collector
from .master_listing_db import MasterListingDatabase


class SearchManager:
    """Manages searches, results, and user data with friendly database integration."""

    def __init__(self, storage: StorageManager, master_db: Optional[MasterListingDatabase] = None):
        self.storage = storage
        self.current_user = None
        self.current_search_id = None
        self.current_results: List[Listing] = []
        
        # Initialize master database if provided
        if master_db is None:
            self.master_db = MasterListingDatabase(storage.connection)
            self.master_db.ensure_schema()
        else:
            self.master_db = master_db

    def set_user(self, user: dict) -> None:
        """Set current authenticated user."""
        self.current_user = user

    def run_search(
        self,
        location: str,
        query: str,
        providers: List[str],
        filter_builder: Optional[FilterBuilder] = None,
    ) -> Dict[str, Any]:
        """
        Execute a full search: collect results, filter, store in DB, update master DB.
        Returns search metadata and results.
        """
        # Create search record
        price_max = (
            str(filter_builder.max_price) if filter_builder and filter_builder.max_price else None
        )
        self.current_search_id = self.storage.create_search(
            user_id=self.current_user["id"] if self.current_user else None,
            location=location,
            price_max=price_max,
            query_text=query,
        )

        # Collect listings
        collector = Collector()
        all_listings = collector.run(
            providers=providers,
            city=location,
            query=query,
        )

        # Apply filters
        if filter_builder:
            filtered_listings = filter_builder.apply_to_listings(all_listings)
        else:
            filtered_listings = all_listings

        self.current_results = filtered_listings

        # Store results in BOTH databases
        for listing in filtered_listings:
            # User's search results database
            self.storage.insert_search_result(
                search_id=self.current_search_id,
                title=listing.title,
                url=listing.url,
                source=listing.source,
                price=listing.price,
                location=listing.location,
                description=listing.description,
                voucher_friendly=listing.voucher_friendly,
                record_friendly=listing.record_friendly,
            )
            
            # Master listing database (shared/aggregated)
            self.master_db.add_or_update_listing(
                title=listing.title,
                location=location,
                price=listing.price,
                description=listing.description,
                url=listing.url,
                source=listing.source,
                voucher_friendly=listing.voucher_friendly,
                record_friendly=listing.record_friendly,
            )

        # Get statistics
        stats = self.storage.get_statistics(self.current_search_id)

        return {
            "search_id": self.current_search_id,
            "location": location,
            "query": query,
            "results": filtered_listings,
            "statistics": stats,
        }

    def get_search_history(self, limit: int = 10) -> List[dict]:
        """Get user's search history."""
        if not self.current_user:
            return []
        return self.storage.get_user_searches(self.current_user["id"], limit)

    def get_search_details(self, search_id: int) -> Optional[Dict[str, Any]]:
        """Get full details of a past search."""
        search = self.storage.get_search_by_id(search_id)
        if not search:
            return None

        results = self.storage.get_search_results(search_id)
        stats = self.storage.get_statistics(search_id)

        return {
            "search": search,
            "results": results,
            "statistics": stats,
        }

    def delete_search(self, search_id: int) -> bool:
        """Delete a search and all its results."""
        return self.storage.delete_search(search_id)

    def add_favorite(self, result_id: int, notes: Optional[str] = None) -> bool:
        """Save a listing as favorite (requires authenticated user)."""
        if not self.current_user:
            return False
        return self.storage.save_favorite(
            self.current_user["id"], result_id, notes
        )

    def remove_favorite(self, result_id: int) -> bool:
        """Remove a favorite."""
        if not self.current_user:
            return False
        return self.storage.remove_favorite(self.current_user["id"], result_id)

    def get_favorites(self) -> List[dict]:
        """Get all user's favorite listings."""
        if not self.current_user:
            return []
        return self.storage.get_user_favorites(self.current_user["id"])

    def is_favorite(self, result_id: int) -> bool:
        """Check if a listing is favorited."""
        if not self.current_user:
            return False
        return self.storage.is_favorite(self.current_user["id"], result_id)

    def reopen_search(self, search_id: int) -> Optional[Dict[str, Any]]:
        """Reopen a previous search from history."""
        search_details = self.get_search_details(search_id)
        if search_details:
            self.current_search_id = search_id
            self.current_results = [
                Listing(**result) for result in search_details["results"]
            ]
        return search_details

    def get_global_search(
        self,
        location: Optional[str] = None,
        keyword: Optional[str] = None,
        voucher_only: bool = False,
        record_only: bool = False,
    ) -> List[dict]:
        """Search across all past results globally."""
        return self.storage.search_listings(
            location=location,
            keyword=keyword,
            voucher_only=voucher_only,
            record_only=record_only,
        )

    def filter_current_results(
        self,
        voucher_only: bool = False,
        record_only: bool = False,
        source: Optional[str] = None,
    ) -> List[dict]:
        """Apply additional filters to current search results."""
        if not self.current_search_id:
            return []
        return self.storage.get_results_by_filter(
            self.current_search_id,
            voucher_only=voucher_only,
            record_only=record_only,
            source=source,
        )

    def get_search_statistics(self) -> Optional[dict]:
        """Get statistics for current search."""
        if not self.current_search_id:
            return None
        return self.storage.get_statistics(self.current_search_id)
