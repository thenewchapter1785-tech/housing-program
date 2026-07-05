import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from housing_scraper.storage import StorageManager


def main() -> None:
    manager = StorageManager(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "housing_app"),
    )
    try:
        applied = manager.run_migrations()
        print(f"Applied {applied} migration(s)")
    finally:
        manager.close()


if __name__ == "__main__":
    main()
