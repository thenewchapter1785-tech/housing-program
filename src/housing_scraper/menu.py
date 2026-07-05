import os
import sys
from typing import Optional

from .auth import authenticate_user, register_google_user, register_user
from .collector import Collector
from .models import Listing
from .result_formatter import ResultFormatter
from .search_history import SearchHistory
from .storage import StorageManager
from ui.result_window import ResultWindow


def prompt_text(label: str, default: Optional[str] = None) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value if value else (default or "")


def run_menu() -> None:
    print("Housing Search Assistant")
    history = SearchHistory()
    manager = StorageManager(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "housing_app"),
    )
    manager.ensure_schema()

    print("1. Sign in")
    print("2. Create account")
    print("3. Continue with Google")
    print("4. View search history")
    print("5. Exit")

    choice = input("Choose an option: ").strip()
    if choice == "5":
        print("Goodbye")
        manager.close()
        return

    if choice == "4":
        print("Search history:")
        for item in history.list_sessions():
            print(f"- {item.id}: {item.title}")
        session_id = input("Select a session ID to reopen (blank to cancel): ").strip()
        if session_id:
            session = history.get_session(int(session_id))
            if session:
                print(f"\nReopened session {session.id}: {session.title}")
                print(
                    ResultFormatter().format_results(
                        [Listing(**result) for result in session.results]
                    )
                )
            else:
                print("Session not found")
        manager.close()
        return

    current_user = None
    if choice == "2":
        email = prompt_text("Email")
        password = input("Password: ").strip()
        display_name = prompt_text("Display name", email.split("@", 1)[0])
        try:
            current_user = register_user(
                manager, email=email, password=password, display_name=display_name
            )
            print(f"Account created for {current_user['email']}")
        except ValueError as exc:
            print(str(exc))
            manager.close()
            return
    elif choice == "3":
        email = prompt_text("Google email")
        google_id = input("Google account ID or token: ").strip() or email
        display_name = prompt_text("Display name", email.split("@", 1)[0])
        current_user = register_google_user(
            manager, email=email, google_id=google_id, display_name=display_name
        )
        print(f"Google account linked for {current_user['email']}")
    else:
        email = prompt_text("Email")
        password = input("Password: ").strip()
        current_user = authenticate_user(manager, email=email, password=password)
        if not current_user:
            print("Invalid email or password")
            manager.close()
            return
        print(f"Signed in as {current_user['email']}")

    location = prompt_text("Location", "Seattle")
    query = prompt_text("Search query", "studio apartment")
    price_max = prompt_text("Maximum price", "1500")

    search_id = manager.create_search(
        user_id=current_user["id"] if current_user else None,
        location=location,
        price_max=price_max,
        query_text=query,
    )

    collector = Collector()
    listings = collector.run(
        providers=["craigslist", "rentals", "padmapper", "rightmove", "example"],
        city=location,
        query=query,
    )

    formatter = ResultFormatter()
    formatted_text = formatter.format_results(listings)
    session = history.add_session(
        location=location,
        query=query,
        price_max=price_max,
        results=[listing.to_dict() for listing in listings],
    )

    print(f"\nSearch session {session.id}: {session.title}")
    print(formatted_text)

    for listing in listings:
        if price_max:
            try:
                price_value = int(str(listing.price).replace("$", "").replace(",", ""))
                if price_value > int(price_max):
                    continue
            except ValueError:
                pass

        manager.insert_search_result(
            search_id=search_id,
            title=listing.title,
            url=listing.url,
            source=listing.source,
            price=listing.price,
            location=listing.location,
            description=listing.description,
            voucher_friendly=listing.voucher_friendly,
            record_friendly=listing.record_friendly,
            contact_name=None,
            contact_phone=None,
            contact_email=None,
            contact_method=None,
        )
        print(f"- {listing.title} | {listing.source} | {listing.price}")

    print("\nRecent search sessions:")
    for item in history.list_sessions():
        print(f"- {item.id}: {item.title}")

    if sys.platform.startswith("win"):
        try:
            window = ResultWindow(f"Housing results - {session.title}", formatted_text)
            window.show()
        except Exception as exc:
            print(f"Popup window unavailable: {exc}")
    else:
        print("Popup window skipped outside Windows.")

    print(f"Saved search #{search_id} to MySQL")
    manager.close()
