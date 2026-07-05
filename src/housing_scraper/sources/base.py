from abc import ABC, abstractmethod
from typing import List

from ..models import Listing


class BaseScraper(ABC):
    name: str = "base"

    @abstractmethod
    def scrape(self, city: str, query: str) -> List[Listing]:
        raise NotImplementedError
