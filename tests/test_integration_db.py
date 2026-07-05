import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from housing_scraper.storage import StorageManager


@pytest.fixture(scope="module")
def storage_with_db():
    """Integration test fixture that uses real MySQL in Docker."""
    storage = StorageManager(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "housing_app"),
        autostart=False,
    )
    storage.connect()
    storage.ensure_schema()
    yield storage
    storage.close()


def test_audit_log_recording(storage_with_db):
    """Test audit logging to MySQL."""
    storage_with_db.log_audit_event(
        user_id=1,
        action="test_action",
        resource_type="test_resource",
        details={"key": "value"},
    )
    logs = storage_with_db.get_audit_logs(limit=1)
    assert len(logs) > 0
    assert logs[0]["action"] == "test_action"


def test_provider_stats(storage_with_db):
    """Test provider stats recording."""
    storage_with_db.record_provider_attempt("test_provider", success=True, latency_ms=100)
    storage_with_db.record_provider_attempt("test_provider", success=False, latency_ms=200)
    stats = storage_with_db.get_provider_stats()
    provider = next((s for s in stats if s["provider_name"] == "test_provider"), None)
    assert provider is not None
    assert provider["total_attempts"] >= 2


def test_user_admin_flags(storage_with_db):
    """Test admin flag management."""
    storage_with_db.set_user_admin(999, is_admin=True)
    assert storage_with_db.is_user_admin(999)
    
    storage_with_db.set_user_admin(999, is_admin=False)
    assert not storage_with_db.is_user_admin(999)


def test_user_ban(storage_with_db):
    """Test user banning."""
    storage_with_db.ban_user(888, reason="test ban")
    assert storage_with_db.is_user_banned(888)
