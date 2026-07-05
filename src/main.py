import argparse
from housing_scraper.collector import Collector
from housing_scraper.app_launcher import AppLauncher
from housing_scraper.menu import run_menu
from ui.app_shell import AppShell


def main() -> None:
    parser = argparse.ArgumentParser(description="Housing Search Platform")
    parser.add_argument("--city", default="seattle", help="City to search")
    parser.add_argument("--query", default="studio apartment", help="Search query")
    parser.add_argument("--price-max", default="1500", help="Maximum price to keep")
    parser.add_argument(
        "--providers",
        nargs="*",
        default=["craigslist", "rentals", "padmapper", "rightmove", "example"],
        help="Providers to run",
    )
    parser.add_argument(
        "--menu", action="store_true", help="Launch the legacy interactive menu"
    )
    parser.add_argument(
        "--ui-shell", action="store_true", help="Initialize the future Windows UI shell"
    )
    parser.add_argument(
        "--platform",
        choices=["desktop", "web", "worker", "cli"],
        default="desktop",
        help="Runtime target: desktop app, secure web API, refresh worker, or collector CLI",
    )
    args = parser.parse_args()

    if args.ui_shell:
        shell = AppShell()
        shell.show_welcome()
        return

    if args.menu:
        run_menu()
        return

    if args.platform == "desktop":
        launcher = AppLauncher()
        launcher.run()
        return

    if args.platform == "web":
        from web.main import main as run_web

        run_web()
        return

    if args.platform == "worker":
        from worker.main import main as run_worker

        run_worker()
        return

    collector = Collector()
    listings = collector.run(providers=args.providers)

    print(f"Collected {len(listings)} listing(s)")
    for listing in listings:
        print(f"- {listing.title} | {listing.source} | {listing.price}")


if __name__ == "__main__":
    main()
