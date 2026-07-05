import os

from housing_scraper.area_refresher import AreaRefreshScheduler
from housing_scraper.master_listing_db import MasterListingDatabase
from housing_scraper.storage import StorageManager


def main() -> None:
    manager = StorageManager(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "housing_app"),
    )
    manager.ensure_schema()

    master_db = MasterListingDatabase(manager.connection)
    master_db.ensure_schema()

    scheduler = AreaRefreshScheduler(master_db)
    interval = int(os.getenv("AUTO_REFRESH_INTERVAL_SECONDS", "900"))

    try:
        scheduler.run_forever(interval_seconds=interval)
    finally:
        manager.close()


if __name__ == "__main__":
    main()
