from typing import List


class SidebarLayout:
    """A lightweight structure for a future desktop sidebar of saved searches."""

    def __init__(self) -> None:
        self.items: List[dict] = []

    def add_item(self, title: str, session_id: int) -> None:
        self.items.append({"title": title, "session_id": session_id})

    def list_items(self) -> List[dict]:
        return list(self.items)
