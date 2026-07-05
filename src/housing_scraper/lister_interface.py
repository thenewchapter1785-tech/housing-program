"""
Lister/Agent interface for managing property listings.
Allows real estate professionals to add and manage properties.
"""

from typing import Optional, Tuple, List
from .master_listing_db import MasterListingDatabase
from .storage import StorageManager


class ListerInterface:
    """Interface for real estate agents/listers to manage properties."""

    def __init__(self, lister_id: int, storage: StorageManager, master_db: MasterListingDatabase):
        self.lister_id = lister_id
        self.storage = storage
        self.master_db = master_db

    def add_property(
        self,
        title: str,
        location: str,
        price: Optional[str] = None,
        description: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        voucher_friendly: bool = False,
        record_friendly: bool = False,
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Add a new property listing.
        Returns: (success, message, listing_id)
        """
        if not title or not location:
            return False, "Title and location are required", None

        try:
            # Add to master listing database
            master_id = self.master_db.add_or_update_listing(
                title=title,
                location=location,
                price=price,
                description=description,
                source="manual_listing",
                voucher_friendly=voucher_friendly,
                record_friendly=record_friendly,
            )

            # Add to manual listings
            with self.storage.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO manual_listings 
                    (lister_id, master_listing_id, title, price, location, description,
                     contact_name, contact_phone, contact_email, voucher_friendly, record_friendly)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.lister_id,
                        master_id,
                        title,
                        price,
                        location,
                        description,
                        contact_name,
                        contact_phone,
                        contact_email,
                        int(voucher_friendly),
                        int(record_friendly),
                    ),
                )
                listing_id = int(cursor.lastrowid)

            return True, "Property added successfully!", listing_id

        except Exception as e:
            return False, f"Error adding property: {str(e)}", None

    def update_property(
        self,
        listing_id: int,
        **updates,
    ) -> Tuple[bool, str]:
        """Update an existing property."""
        try:
            # Verify ownership
            with self.storage.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT lister_id FROM manual_listings WHERE id = %s",
                    (listing_id,),
                )
                listing = cursor.fetchone()
                if not listing or listing["lister_id"] != self.lister_id:
                    return False, "Permission denied: You can only edit your own listings"

                # Build update query
                set_clauses = []
                params = []
                for key, value in updates.items():
                    if key in [
                        "title",
                        "price",
                        "location",
                        "description",
                        "contact_name",
                        "contact_phone",
                        "contact_email",
                        "voucher_friendly",
                        "record_friendly",
                    ]:
                        if key in ["voucher_friendly", "record_friendly"]:
                            value = int(value)
                        set_clauses.append(f"{key} = %s")
                        params.append(value)

                if not set_clauses:
                    return False, "No valid fields to update"

                params.append(listing_id)
                query = f"UPDATE manual_listings SET {', '.join(set_clauses)} WHERE id = %s"
                cursor.execute(query, params)

            return True, "Property updated successfully!"

        except Exception as e:
            return False, f"Error updating property: {str(e)}"

    def deactivate_property(self, listing_id: int) -> Tuple[bool, str]:
        """Deactivate a property listing."""
        try:
            # Verify ownership
            with self.storage.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT lister_id, master_listing_id FROM manual_listings WHERE id = %s",
                    (listing_id,),
                )
                listing = cursor.fetchone()
                if not listing or listing["lister_id"] != self.lister_id:
                    return False, "Permission denied"

                # Deactivate
                cursor.execute(
                    "UPDATE manual_listings SET is_active = 0 WHERE id = %s",
                    (listing_id,),
                )

                # Also deactivate in master if this was the only lister's listing
                if listing["master_listing_id"]:
                    cursor.execute(
                        """
                        SELECT COUNT(*) as count FROM manual_listings 
                        WHERE master_listing_id = %s AND is_active = 1
                        """,
                        (listing["master_listing_id"],),
                    )
                    if cursor.fetchone()["count"] == 0:
                        self.master_db.deactivate_listing(listing["master_listing_id"])

            return True, "Property deactivated successfully!"

        except Exception as e:
            return False, f"Error deactivating property: {str(e)}"

    def get_my_listings(self, active_only: bool = True) -> List[dict]:
        """Get all properties listed by this agent."""
        query = "SELECT * FROM manual_listings WHERE lister_id = %s"
        params = [self.lister_id]

        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY updated_at DESC"

        with self.storage.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_property_details(self, listing_id: int) -> Optional[dict]:
        """Get details of a property."""
        with self.storage.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM manual_listings WHERE id = %s AND lister_id = %s",
                (listing_id, self.lister_id),
            )
            listing = cursor.fetchone()

            if listing and listing.get("master_listing_id"):
                # Get master listing info and sources
                cursor.execute(
                    "SELECT * FROM master_listings WHERE id = %s",
                    (listing["master_listing_id"],),
                )
                master = cursor.fetchone()

                if master:
                    cursor.execute(
                        "SELECT * FROM listing_sources WHERE master_listing_id = %s",
                        (listing["master_listing_id"],),
                    )
                    sources = cursor.fetchall()
                    return {
                        "manual": listing,
                        "master": master,
                        "sources": sources,
                    }

            return {"manual": listing} if listing else None

    def get_listings_stats(self) -> dict:
        """Get statistics on this lister's properties."""
        with self.storage.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                       SUM(voucher_friendly) as voucher_count,
                       SUM(record_friendly) as record_count
                FROM manual_listings
                WHERE lister_id = %s
                """,
                (self.lister_id,),
            )
            stats = cursor.fetchone()

        return {
            "total_listings": stats["total"] or 0,
            "active_listings": stats["active"] or 0,
            "voucher_friendly": stats["voucher_count"] or 0,
            "record_friendly": stats["record_count"] or 0,
        }
