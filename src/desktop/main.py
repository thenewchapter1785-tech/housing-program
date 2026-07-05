import os

from housing_scraper.app_launcher import AppLauncher
from ui.desktop_gui import DesktopApp


def main() -> None:
    # Set DESKTOP_USE_CLI=true to keep previous terminal-only flow.
    if os.getenv("DESKTOP_USE_CLI", "false").lower() in {"true", "1", "yes"}:
        AppLauncher().run()
        return

    DesktopApp().run()


if __name__ == "__main__":
    main()
