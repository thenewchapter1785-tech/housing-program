from pathlib import Path
from typing import List


class MigrationManager:
    def __init__(self, connection, migrations_dir: Path | None = None):
        self.connection = connection
        self.migrations_dir = migrations_dir or Path(__file__).resolve().parents[2] / "migrations" / "sql"

    def ensure_migration_table(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(128) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def applied_versions(self) -> set[str]:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT version FROM schema_migrations")
            rows = cursor.fetchall()
        return {row["version"] for row in rows}

    def available_migrations(self) -> List[Path]:
        if not self.migrations_dir.exists():
            return []
        return sorted(self.migrations_dir.glob("*.sql"))

    def apply_all(self) -> int:
        self.ensure_migration_table()
        applied = self.applied_versions()
        count = 0

        for migration in self.available_migrations():
            version = migration.name
            if version in applied:
                continue

            sql = migration.read_text(encoding="utf-8")
            statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
            with self.connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
                cursor.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (version,),
                )
            count += 1

        return count
