import os
from typing import List, Optional

import pymysql


class StorageManager:
    def __init__(self, host: str, port: int, user: str, password: str, database: str, autostart: bool = True):
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

    def create_user(self, email: str, password_hash: str, display_name: Optional[str] = None, google_id: Optional[str] = None) -> int:
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

    def create_search(self, user_id: Optional[int], location: str, price_max: Optional[str], query_text: str) -> int:
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
