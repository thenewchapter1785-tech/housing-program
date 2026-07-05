from typing import Optional


class AppShell:
    """A simple shell that will later host the Windows GUI."""

    def __init__(self) -> None:
        self.current_user: Optional[dict] = None

    def show_welcome(self) -> None:
        print("Windows app shell ready")

    def set_user(self, user: Optional[dict]) -> None:
        self.current_user = user
