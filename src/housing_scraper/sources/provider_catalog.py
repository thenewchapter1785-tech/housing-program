from typing import Dict, Type

from .base import BaseScraper
from .apartments import ApartmentsScraper
from .craigslist import CraigslistScraper
from .example import ExampleScraper
from .hotpads import HotpadsScraper
from .neighborly import NeighborlyScraper
from .padmapper import PadmapperScraper
from .realtor import RealtorScraper
from .rentals import RentalsScraper
from .rentometer import RentometerScraper
from .rightmove import RightmoveScraper
from .trulia import TruliaScraper
from .zillow import ZillowScraper


def get_scraper_map() -> Dict[str, Type[BaseScraper]]:
    return {
        "example": ExampleScraper,
        "craigslist": CraigslistScraper,
        "apartments": ApartmentsScraper,
        "rentals": RentalsScraper,
        "rentometer": RentometerScraper,
        "padmapper": PadmapperScraper,
        "neighborly": NeighborlyScraper,
        "rightmove": RightmoveScraper,
        "realtor": RealtorScraper,
        "trulia": TruliaScraper,
        "zillow": ZillowScraper,
        "hotpads": HotpadsScraper,
    }
