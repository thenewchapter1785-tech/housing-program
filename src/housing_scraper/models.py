from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Listing:
    title: str
    url: str
    source: str
    price: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    voucher_friendly: bool = False
    record_friendly: bool = False
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "price": self.price,
            "location": self.location,
            "description": self.description,
            "voucher_friendly": self.voucher_friendly,
            "record_friendly": self.record_friendly,
            "tags": self.tags,
        }
