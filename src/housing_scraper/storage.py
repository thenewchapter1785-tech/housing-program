import os
from datetime import datetime
from typing import List, Optional

import pymysql

from .migrations import MigrationManager


class StorageManager:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        autostart: bool = True,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.autostart = autostart
        if autostart:
            self.connect()

    def connect(self):
        self.connection = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        )
        return self.connection

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def ensure_schema(self):
        if self.connection is None:
            self.connect()
        self.run_migrations()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    google_id VARCHAR(255) NULL,
                    display_name VARCHAR(255) NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS searches (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NULL,
                    location VARCHAR(255) NOT NULL,
                    price_max VARCHAR(50) NULL,
                    query_text VARCHAR(255) NOT NULL,
                    notes TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS search_results (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    search_id BIGINT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    url TEXT NOT NULL,
                    source VARCHAR(100) NOT NULL,
                    price VARCHAR(50) NULL,
                    location VARCHAR(255) NULL,
                    description TEXT NULL,
                    voucher_friendly TINYINT(1) DEFAULT 0,
                    record_friendly TINYINT(1) DEFAULT 0,
                    contact_name VARCHAR(255) NULL,
                    contact_phone VARCHAR(50) NULL,
                    contact_email VARCHAR(255) NULL,
                    contact_method VARCHAR(100) NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS favorites (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    result_id BIGINT NOT NULL,
                    notes TEXT NULL,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (result_id) REFERENCES search_results(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_favorite (user_id, result_id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    token_hash CHAR(64) NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    revoked TINYINT(1) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_active (user_id, revoked, expires_at)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    token_hash CHAR(64) NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    revoked TINYINT(1) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_refresh_user_active (user_id, revoked, expires_at)
                )
                """
            )

    def run_migrations(self) -> int:
        if self.connection is None:
            self.connect()
        manager = MigrationManager(self.connection)
        return manager.apply_all()

    def create_user(
        self,
        email: str,
        password_hash: str,
        display_name: Optional[str] = None,
        google_id: Optional[str] = None,
    ) -> int:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (email, password_hash, display_name, google_id) VALUES (%s, %s, %s, %s)",
                (email, password_hash, display_name, google_id),
            )
            return int(cursor.lastrowid)

    def get_user_by_email(self, email: str) -> Optional[dict]:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cursor.fetchone()

    def create_search(
        self,
        user_id: Optional[int],
        location: str,
        price_max: Optional[str],
        query_text: str,
    ) -> int:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO searches (user_id, location, price_max, query_text) VALUES (%s, %s, %s, %s)",
                (user_id, location, price_max, query_text),
            )
            return int(cursor.lastrowid)

    def insert_search_result(
        self,
        search_id: int,
        title: str,
        url: str,
        source: str,
        price: Optional[str],
        location: Optional[str],
        description: Optional[str],
        voucher_friendly: bool,
        record_friendly: bool,
        contact_name: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_method: Optional[str] = None,
    ) -> None:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO search_results (
                    search_id, title, url, source, price, location, description,
                    voucher_friendly, record_friendly, contact_name, contact_phone,
                    contact_email, contact_method
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    search_id,
                    title,
                    url,
                    source,
                    price,
                    location,
                    description,
                    int(voucher_friendly),
                    int(record_friendly),
                    contact_name,
                    contact_phone,
                    contact_email,
                    contact_method,
                ),
            )

    def get_search_results(self, search_id: int) -> List[dict]:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM search_results WHERE search_id = %s ORDER BY id DESC",
                (search_id,),
            )
            return cursor.fetchall()

    def get_user_searches(
        self, user_id: int, limit: int = 10
    ) -> List[dict]:
        """Get recent searches for a user."""
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, location, query_text, price_max, created_at
                FROM searches
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            return cursor.fetchall()

    def get_search_by_id(self, search_id: int) -> Optional[dict]:
        """Get search details by ID."""
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM searches WHERE id = %s",
                (search_id,),
            )
            return cursor.fetchone()

    def delete_search(self, search_id: int) -> bool:
        """Delete a search and all its results."""
        if self.connection is None:
            self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM search_results WHERE search_id = %s", (search_id,))
                cursor.execute("DELETE FROM searches WHERE id = %s", (search_id,))
            return True
        except Exception as e:
            print(f"Error deleting search: {e}")
            return False

    def update_search_notes(self, search_id: int, notes: str) -> bool:
        """Add or update notes for a search."""
        if self.connection is None:
            self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE searches SET notes = %s WHERE id = %s",
                    (notes, search_id),
                )
            return True
        except Exception:
            # Notes column may not exist yet, will be added in schema migration
            return False

    def get_results_by_filter(
        self,
        search_id: int,
        voucher_only: bool = False,
        record_only: bool = False,
        source: Optional[str] = None,
    ) -> List[dict]:
        """Get filtered results from a search."""
        if self.connection is None:
            self.connect()
        
        query = "SELECT * FROM search_results WHERE search_id = %s"
        params = [search_id]
        
        if voucher_only:
            query += " AND voucher_friendly = 1"
        if record_only:
            query += " AND record_friendly = 1"
        if source:
            query += " AND source = %s"
            params.append(source)
        
        query += " ORDER BY id DESC"
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_statistics(self, search_id: int) -> dict:
        """Get search statistics."""
        if self.connection is None:
            self.connect()
        
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as total FROM search_results WHERE search_id = %s",
                (search_id,),
            )
            total = cursor.fetchone()["total"]
            
            cursor.execute(
                "SELECT COUNT(*) as voucher_count FROM search_results WHERE search_id = %s AND voucher_friendly = 1",
                (search_id,),
            )
            voucher_count = cursor.fetchone()["voucher_count"]
            
            cursor.execute(
                "SELECT COUNT(*) as record_count FROM search_results WHERE search_id = %s AND record_friendly = 1",
                (search_id,),
            )
            record_count = cursor.fetchone()["record_count"]
            
            cursor.execute(
                "SELECT source, COUNT(*) as count FROM search_results WHERE search_id = %s GROUP BY source ORDER BY count DESC",
                (search_id,),
            )
            sources = cursor.fetchall()
        
        return {
            "total_listings": total,
            "voucher_friendly": voucher_count,
            "record_friendly": record_count,
            "by_source": sources,
        }

    def search_listings(
        self,
        location: Optional[str] = None,
        keyword: Optional[str] = None,
        voucher_only: bool = False,
        record_only: bool = False,
        limit: int = 50,
    ) -> List[dict]:
        """Search across all past search results."""
        if self.connection is None:
            self.connect()
        
        query = "SELECT * FROM search_results WHERE 1=1"
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
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def save_favorite(
        self, user_id: int, result_id: int, notes: Optional[str] = None
    ) -> bool:
        """Save a listing as favorite."""
        if self.connection is None:
            self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO favorites (user_id, result_id, notes) VALUES (%s, %s, %s)",
                    (user_id, result_id, notes),
                )
            return True
        except Exception as e:
            # Listing already favorited
            if "Duplicate entry" in str(e):
                return False
            print(f"Error saving favorite: {e}")
            return False

    def remove_favorite(self, user_id: int, result_id: int) -> bool:
        """Remove a saved favorite."""
        if self.connection is None:
            self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM favorites WHERE user_id = %s AND result_id = %s",
                    (user_id, result_id),
                )
            return True
        except Exception as e:
            print(f"Error removing favorite: {e}")
            return False

    def get_user_favorites(self, user_id: int) -> List[dict]:
        """Get all favorited listings for a user."""
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT sr.*, f.notes as favorite_notes, f.saved_at
                FROM favorites f
                JOIN search_results sr ON f.result_id = sr.id
                WHERE f.user_id = %s
                ORDER BY f.saved_at DESC
                """,
                (user_id,),
            )
            return cursor.fetchall()

    def is_favorite(self, user_id: int, result_id: int) -> bool:
        """Check if a listing is favorited."""
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM favorites WHERE user_id = %s AND result_id = %s",
                (user_id, result_id),
            )
            return cursor.fetchone() is not None

    def update_favorite_notes(
        self, user_id: int, result_id: int, notes: str
    ) -> bool:
        """Update notes for a favorited listing."""
        if self.connection is None:
            self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE favorites SET notes = %s WHERE user_id = %s AND result_id = %s",
                    (notes, user_id, result_id),
                )
            return True
        except Exception as e:
            print(f"Error updating favorite notes: {e}")
            return False

    def create_auth_session(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        """Persist a web auth session token hash."""
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO auth_sessions (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token_hash, expires_at),
            )

    def get_user_by_auth_token_hash(self, token_hash: str) -> Optional[dict]:
        """Return user for valid, non-revoked, non-expired auth token hash."""
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.*
                FROM auth_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s
                  AND s.revoked = 0
                  AND s.expires_at > CURRENT_TIMESTAMP
                LIMIT 1
                """,
                (token_hash,),
            )
            return cursor.fetchone()

    def revoke_auth_session(self, token_hash: str) -> None:
        """Revoke one auth session by token hash."""
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auth_sessions SET revoked = 1 WHERE token_hash = %s",
                (token_hash,),
            )

    def revoke_all_user_auth_sessions(self, user_id: int) -> None:
        """Revoke all auth sessions for a user."""
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auth_sessions SET revoked = 1 WHERE user_id = %s",
                (user_id,),
            )

    def create_refresh_token(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO auth_refresh_tokens (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token_hash, expires_at),
            )

    def get_user_by_refresh_token_hash(self, token_hash: str) -> Optional[dict]:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.*
                FROM auth_refresh_tokens t
                JOIN users u ON u.id = t.user_id
                WHERE t.token_hash = %s
                  AND t.revoked = 0
                  AND t.expires_at > CURRENT_TIMESTAMP
                LIMIT 1
                """,
                (token_hash,),
            )
            return cursor.fetchone()

    def revoke_refresh_token(self, token_hash: str) -> None:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auth_refresh_tokens SET revoked = 1 WHERE token_hash = %s",
                (token_hash,),
            )

    def revoke_all_user_refresh_tokens(self, user_id: int) -> None:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auth_refresh_tokens SET revoked = 1 WHERE user_id = %s",
                (user_id,),
            )

    def log_audit_event(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        if self.connection is None:
            self.connect()
        import json
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, action, resource_type, resource_id, json.dumps(details) if details else None, ip_address),
            )

    def get_audit_logs(self, limit: int = 100, offset: int = 0) -> List[dict]:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM audit_logs
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            return cursor.fetchall()

    def record_provider_attempt(self, provider: str, success: bool, latency_ms: int = 0) -> None:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            if success:
                cursor.execute(
                    """
                    INSERT INTO provider_stats (provider_name, total_attempts, successful_attempts, last_success_at)
                    VALUES (%s, 1, 1, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        total_attempts = total_attempts + 1,
                        successful_attempts = successful_attempts + 1,
                        last_success_at = CURRENT_TIMESTAMP
                    """,
                    (provider,),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO provider_stats (provider_name, total_attempts, failed_attempts, last_failure_at)
                    VALUES (%s, 1, 1, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        total_attempts = total_attempts + 1,
                        failed_attempts = failed_attempts + 1,
                        last_failure_at = CURRENT_TIMESTAMP
                    """,
                    (provider,),
                )

    def get_provider_stats(self) -> List[dict]:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM provider_stats
                ORDER BY reliability_score DESC
                """
            )
            return cursor.fetchall()

    def set_user_admin(self, user_id: int, is_admin: bool) -> None:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_admin_flags (user_id, is_admin)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE is_admin = VALUES(is_admin)
                """,
                (user_id, int(is_admin)),
            )

    def is_user_admin(self, user_id: int) -> bool:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT is_admin FROM user_admin_flags WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
        return row["is_admin"] == 1 if row else False

    def ban_user(self, user_id: int, reason: Optional[str] = None) -> None:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_admin_flags (user_id, is_banned, ban_reason)
                VALUES (%s, 1, %s)
                ON DUPLICATE KEY UPDATE is_banned = 1, ban_reason = VALUES(ban_reason)
                """,
                (user_id, reason),
            )

    def is_user_banned(self, user_id: int) -> bool:
        if self.connection is None:
            self.connect()
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT is_banned FROM user_admin_flags WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
        return row["is_banned"] == 1 if row else False
