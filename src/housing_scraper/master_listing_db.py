"""
Master listing database that aggregates and deduplicates listings from all sources.
Shared database updated by searches and manual listings from agents/listers.
"""

from typing import List, Optional, Dict, Any
import pymysql


class MasterListingDatabase:
    """
    Central listing repository tracking all properties in areas.
    Auto-deduplicates listings, tracks sources, and maintains history.
    """

    def __init__(self, storage_connection):
        self.connection = storage_connection

    def ensure_schema(self):
        """Create master listing tables if they don't exist."""
        with self.connection.cursor() as cursor:
            # Master listings table - deduped and aggregated
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS master_listings (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    price VARCHAR(50),
                    location VARCHAR(255) NOT NULL,
                    description TEXT,
                    url TEXT UNIQUE,
                    latitude DECIMAL(10, 8),
                    longitude DECIMAL(11, 8),
                    voucher_friendly TINYINT(1) DEFAULT 0,
                    record_friendly TINYINT(1) DEFAULT 0,
                    is_active TINYINT(1) DEFAULT 1,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_location (location),
                    INDEX idx_active (is_active),
                    INDEX idx_price (price),
                    INDEX idx_voucher (voucher_friendly)
                )
                """
            )

            # Track which sources have this listing
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS listing_sources (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    master_listing_id BIGINT NOT NULL,
                    source VARCHAR(100) NOT NULL,
                    source_listing_id BIGINT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (master_listing_id) REFERENCES master_listings(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_source (master_listing_id, source)
                )
                """
            )

            # Track area data for auto-updates
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS area_tracking (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    area_name VARCHAR(255) NOT NULL UNIQUE,
                    active TINYINT(1) DEFAULT 1,
                    last_scrape TIMESTAMP,
                    scrape_frequency_hours INT DEFAULT 24,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Manual listings from agents/listers
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS manual_listings (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    lister_id BIGINT NOT NULL,
                    master_listing_id BIGINT,
                    title VARCHAR(255) NOT NULL,
                    price VARCHAR(50),
                    location VARCHAR(255) NOT NULL,
                    description TEXT,
                    contact_name VARCHAR(255),
                    contact_phone VARCHAR(50),
                    contact_email VARCHAR(255),
                    voucher_friendly TINYINT(1) DEFAULT 0,
                    record_friendly TINYINT(1) DEFAULT 0,
                    is_active TINYINT(1) DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (lister_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (master_listing_id) REFERENCES master_listings(id) ON DELETE SET NULL
                )
                """
            )

    def add_or_update_listing(
        self,
        title: str,
        location: str,
        price: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        source: Optional[str] = None,
        voucher_friendly: bool = False,
        record_friendly: bool = False,
    ) -> int:
        """
        Add or update a listing in master database.
        Returns: master_listing_id
        """
        with self.connection.cursor() as cursor:
            # Try to find existing listing by URL if provided
            if url:
                cursor.execute("SELECT id FROM master_listings WHERE url = %s", (url,))
                existing = cursor.fetchone()
                if existing:
                    # Update last_seen and flags
                    cursor.execute(
                        """
                        UPDATE master_listings 
                        SET voucher_friendly = voucher_friendly OR %s,
                            record_friendly = record_friendly OR %s,
                            last_seen = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (int(voucher_friendly), int(record_friendly), existing["id"]),
                    )
                    master_id = existing["id"]
                    # Update source tracking
                    if source:
                        cursor.execute(
                            """
                            INSERT INTO listing_sources (master_listing_id, source, last_seen)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON DUPLICATE KEY UPDATE last_seen = CURRENT_TIMESTAMP
                            """,
                            (master_id, source),
                        )
                    return master_id

            # Create new listing
            cursor.execute(
                """
                INSERT INTO master_listings 
                (title, price, location, description, url, voucher_friendly, record_friendly)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    title,
                    price,
                    location,
                    description,
                    url,
                    int(voucher_friendly),
                    int(record_friendly),
                ),
            )
            master_id = int(cursor.lastrowid)

            # Track source
            if source:
                cursor.execute(
                    """
                    INSERT INTO listing_sources (master_listing_id, source)
                    VALUES (%s, %s)
                    """,
                    (master_id, source),
                )

            return master_id

    def get_listings_by_location(
        self,
        location: str,
        voucher_only: bool = False,
        record_only: bool = False,
        active_only: bool = True,
    ) -> List[dict]:
        """Get all listings for a location."""
        query = "SELECT * FROM master_listings WHERE location LIKE %s"
        params = [f"%{location}%"]

        if active_only:
            query += " AND is_active = 1"
        if voucher_only:
            query += " AND voucher_friendly = 1"
        if record_only:
            query += " AND record_friendly = 1"

        query += " ORDER BY last_seen DESC"

        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_listing_sources(self, master_listing_id: int) -> List[dict]:
        """Get all sources tracking this listing."""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT source, source_listing_id, first_seen, last_seen
                FROM listing_sources
                WHERE master_listing_id = %s
                ORDER BY source
                """,
                (master_listing_id,),
            )
            return cursor.fetchall()

    def deactivate_listing(self, master_listing_id: int) -> bool:
        """Mark a listing as inactive."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE master_listings SET is_active = 0 WHERE id = %s",
                    (master_listing_id,),
                )
            return True
        except Exception as e:
            print(f"Error deactivating listing: {e}")
            return False

    def get_area_statistics(self, location: str) -> dict:
        """Get listing statistics for an area."""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) as total, 
                       SUM(voucher_friendly) as voucher_count,
                       SUM(record_friendly) as record_count
                FROM master_listings 
                WHERE location LIKE %s AND is_active = 1
                """,
                (f"%{location}%",),
            )
            stats = cursor.fetchone()

            cursor.execute(
                """
                SELECT source, COUNT(*) as count
                FROM listing_sources ls
                JOIN master_listings ml ON ls.master_listing_id = ml.id
                WHERE ml.location LIKE %s AND ml.is_active = 1
                GROUP BY source
                ORDER BY count DESC
                """,
                (f"%{location}%",),
            )
            by_source = cursor.fetchall()

            return {
                "total": stats["total"] or 0,
                "voucher_friendly": stats["voucher_count"] or 0,
                "record_friendly": stats["record_count"] or 0,
                "by_source": by_source,
            }

    def search_listings(
        self,
        location: Optional[str] = None,
        keyword: Optional[str] = None,
        voucher_only: bool = False,
        record_only: bool = False,
        max_price: Optional[int] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Search master listings."""
        query = "SELECT * FROM master_listings WHERE is_active = 1"
        params = []

        if location:
            query += " AND location LIKE %s"
            params.append(f"%{location}%")
        if keyword:
            query += " AND (title LIKE %s OR description LIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if voucher_only:
            query += " AND voucher_friendly = 1"
        if record_only:
            query += " AND record_friendly = 1"
        if max_price:
            query += " AND CAST(REPLACE(price, '$', '') as UNSIGNED) <= %s"
            params.append(max_price)

        query += " ORDER BY last_seen DESC LIMIT %s"
        params.append(limit)

        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
