import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from housing_scraper.storage import StorageManager


def test_storage_manager_creates_table_and_insert():
    manager = StorageManager(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "housing_app"),
        autostart=False,
    )

    try:
        manager.ensure_schema()
        manager.insert_search_result(
            search_id=1,
            title="Test listing",
            url="https://example.com",
            source="test",
            price="$1000",
            location="Seattle",
            description="A test listing",
            voucher_friendly=True,
            record_friendly=True,
            contact_name="Jane Doe",
            contact_phone="555-1234",
            contact_email="jane@example.com",
            contact_method="Phone",
        )
        row = manager.get_search_results(search_id=1)
        assert len(row) >= 1
    finally:
        manager.close()
