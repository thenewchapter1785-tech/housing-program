import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    city: str = os.getenv("SEARCH_CITY", "seattle")
    query: str = os.getenv("SEARCH_QUERY", "studio apartment")
    data_dir: str = os.getenv("DATA_DIR", "data")
    request_delay_seconds: float = float(os.getenv("REQUEST_DELAY_SECONDS", "2"))


settings = Settings()
