import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from housing_scraper.migrations import MigrationManager


class FakeCursor:
    def __init__(self, state):
        self.state = state
        self._rows = []

    def execute(self, sql, params=None):
        sql_up = sql.strip().upper()
        if sql_up.startswith("SELECT VERSION FROM SCHEMA_MIGRATIONS"):
            self._rows = [{"version": version} for version in self.state["applied"]]
            return
        if sql_up.startswith("INSERT INTO SCHEMA_MIGRATIONS"):
            self.state["applied"].add(params[0])
            return
        self.state["executed"].append((sql, params))

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self):
        self.state = {"applied": set(), "executed": []}

    def cursor(self):
        return FakeCursor(self.state)


def test_migrations_apply_only_once(tmp_path):
    migrations_dir = tmp_path / "sql"
    migrations_dir.mkdir(parents=True)
    (migrations_dir / "001_test.sql").write_text("CREATE TABLE a (id INT);", encoding="utf-8")

    conn = FakeConnection()
    mgr = MigrationManager(conn, migrations_dir=migrations_dir)

    first = mgr.apply_all()
    second = mgr.apply_all()

    assert first == 1
    assert second == 0
    assert "001_test.sql" in conn.state["applied"]
