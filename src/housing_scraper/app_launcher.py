"""
Main application launcher with role-based entry points.
Handles both searchers and listers/agents.
"""

import os
from typing import Optional
from .auth_manager import AuthManager
from .auth_ui import AuthUI
from .role_auth import RoleBasedAuthManager, GovernmentEmailValidator
from .storage import StorageManager
from .search_manager import SearchManager
from .master_listing_db import MasterListingDatabase
from .lister_interface import ListerInterface


class AppLauncher:
    """Main application launcher and router."""

    def __init__(self):
        # Initialize storage
        self.storage = StorageManager(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "housing_app"),
        )
        self.storage.ensure_schema()

        # Initialize role-based auth
        self.role_auth = RoleBasedAuthManager(self.storage)
        self.role_auth.ensure_role_schema()

        # Initialize standard auth
        self.auth_manager = AuthManager(self.storage)

        # Initialize master listing database
        self.master_db = MasterListingDatabase(self.storage.connection)
        self.master_db.ensure_schema()

    def show_welcome_screen(self) -> str:
        """Show welcome screen with role selection."""
        AuthUI.clear_screen()
        AuthUI.print_header("Housing Search Platform")

        print("\nWelcome! Are you a...")
        print("\n1. Housing Seeker")
        print("   → Find available rentals, voucher-friendly, record-friendly housing")
        print("\n2. Real Estate Professional")
        print("   → List properties for rent (requires government email)")
        print("\n3. Returning User")
        print("   → Sign in to your account")
        print("\n4. Exit")

        choice = input("\nChoose an option (1-4): ").strip()
        return choice

    def register_searcher_flow(self) -> Optional[dict]:
        """Registration flow for housing seekers."""
        AuthUI.print_header("Create Housing Seeker Account")

        email = AuthUI.prompt_email()
        AuthUI.show_password_requirements()
        password = AuthUI.prompt_password("Password", confirm=True)
        display_name = AuthUI.prompt_display_name(default=email.split("@")[0])

        success, message, user = self.role_auth.register_with_role(
            email=email,
            password=password,
            display_name=display_name,
            role="searcher",
        )

        if success:
            AuthUI.print_success(message)
            return user
        else:
            AuthUI.handle_error(message)
            return None

    def register_lister_flow(self) -> Optional[dict]:
        """Registration flow for real estate professionals."""
        AuthUI.print_header("Register as Real Estate Professional")

        print("\n📋 Government Email Requirement:")
        print("   To list properties, you must use a government email (.gov domain)")
        print("   This ensures secure access and prevents spam.\n")

        email = AuthUI.prompt_email("Government email address")

        # Validate government email
        is_gov, gov_type = GovernmentEmailValidator.is_government_email(email)
        if not is_gov:
            AuthUI.handle_error(
                "This email is not from a government domain. Please use a .gov email address."
            )
            return None

        AuthUI.print_success(f"Government email verified ({gov_type})!")

        # Whitelist the email
        success, msg = GovernmentEmailValidator.whitelist_email(self.storage, email)
        if success:
            AuthUI.print_success(msg)
        else:
            AuthUI.handle_error(msg)
            return None

        # Continue registration
        AuthUI.show_password_requirements()
        password = AuthUI.prompt_password("Password", confirm=True)
        display_name = AuthUI.prompt_display_name(default=email.split("@")[0])

        agency = input("\nYour agency/organization: ").strip() or "Government Agency"

        success, message, user = self.role_auth.register_with_role(
            email=email,
            password=password,
            display_name=display_name,
            role="lister",
        )

        if success:
            AuthUI.print_success(message)
            print(f"Welcome, {agency} representative!")
            return user
        else:
            AuthUI.handle_error(message)
            return None

    def login_flow(self) -> Optional[dict]:
        """Login flow for returning users."""
        AuthUI.print_header("Sign In")

        email = AuthUI.prompt_email()
        password = AuthUI.prompt_password()
        remember_me = AuthUI.prompt_yes_no("Remember me on this computer?", default="n")

        success, message, user = self.auth_manager.login_with_validation(
            email, password, remember_me
        )

        if success:
            AuthUI.print_success(message)
            return user
        else:
            AuthUI.handle_error(message)
            return None

    def show_auth_menu(self) -> Optional[dict]:
        """Show authentication menu."""
        while True:
            choice = self.show_welcome_screen()

            if choice == "1":  # Housing seeker
                user = self.register_searcher_flow()
                if user:
                    return user
                input("\nPress Enter to continue...")

            elif choice == "2":  # Real estate professional
                user = self.register_lister_flow()
                if user:
                    return user
                input("\nPress Enter to continue...")

            elif choice == "3":  # Existing user
                user = self.login_flow()
                if user:
                    return user
                retry = AuthUI.prompt_yes_no("Try again?", default="y")
                if not retry:
                    return None
                continue

            elif choice == "4":  # Exit
                print("\nGoodbye!")
                return None

            else:
                AuthUI.handle_error("Invalid choice. Please try again.")

    def run_searcher_flow(self, user: dict) -> None:
        """Main flow for housing seekers."""
        search_mgr = SearchManager(self.storage)
        search_mgr.set_user(user)

        from .filter_builder import FilterBuilder
        from .result_formatter import ResultFormatter

        while True:
            menu_choice = AuthUI.show_main_menu(user.get("display_name", user["email"]))

            if menu_choice == "1":  # New search
                AuthUI.print_header("Search for Housing")
                location = input("City or area: ").strip() or "Seattle"
                query = input("Type of housing (e.g., 1 bedroom, studio): ").strip() or "1 bedroom"

                # Filters
                filter_builder = FilterBuilder()
                filter_builder.quick_preset()

                print("\n🔍 Searching...")
                result = search_mgr.run_search(
                    location=location,
                    query=query,
                    providers=["craigslist", "rentals", "padmapper", "rightmove"],
                    filter_builder=filter_builder,
                )

                # Display
                formatter = ResultFormatter()
                print(formatter.format_results(result["results"]))

                # Stats
                stats = result["statistics"]
                print(f"\n📊 Found {stats['total_listings']} listings")
                print(f"   • Voucher-friendly: {stats['voucher_friendly']}")
                print(f"   • Record-friendly: {stats['record_friendly']}")

                input("\nPress Enter to continue...")

            elif menu_choice == "2":  # Search history
                history = search_mgr.get_search_history(limit=10)
                AuthUI.print_header("Your Search History")
                if history:
                    for i, search in enumerate(history, 1):
                        print(f"{i}. {search['query_text']} in {search['location']}")
                else:
                    print("No searches yet.")
                input("\nPress Enter to continue...")

            elif menu_choice == "3":  # Favorites
                favs = search_mgr.get_favorites()
                AuthUI.print_header("Your Saved Favorites")
                if favs:
                    for i, fav in enumerate(favs, 1):
                        print(f"{i}. {fav['title']}")
                        if fav.get("favorite_notes"):
                            print(f"   Notes: {fav['favorite_notes']}")
                else:
                    print("No favorites saved yet.")
                input("\nPress Enter to continue...")

            elif menu_choice == "4":  # Settings
                AuthUI.print_header("Settings")
                old_password = AuthUI.prompt_password("Current password")
                AuthUI.show_password_requirements()
                new_password = AuthUI.prompt_password("New password", confirm=True)

                success, message = self.auth_manager.change_password(
                    user["id"], old_password, new_password
                )
                if success:
                    AuthUI.print_success(message)
                else:
                    AuthUI.handle_error(message)
                input("\nPress Enter to continue...")

            elif menu_choice == "5":  # Sign out
                self.auth_manager.logout(user["id"])
                AuthUI.print_success("Signed out successfully!")
                break

            elif menu_choice == "6":  # Exit
                print("\nGoodbye!")
                self.storage.close()
                return

    def run_lister_flow(self, user: dict) -> None:
        """Main flow for real estate professionals/listers."""
        lister = ListerInterface(user["id"], self.storage, self.master_db)

        while True:
            AuthUI.print_header(f"Property Manager - {user.get('display_name', user['email'])}")
            print("\n1. Add new property")
            print("2. Manage my listings")
            print("3. View area statistics")
            print("4. View master database listings")
            print("5. Sign out")
            print("6. Exit")

            choice = input("\nChoose an option (1-6): ").strip()

            if choice == "1":  # Add property
                AuthUI.print_header("List New Property")
                title = input("Property title/address: ").strip()
                location = input("City/area: ").strip()
                price = input("Monthly rent ($): ").strip()
                description = input("Description: ").strip()
                contact_name = input("Contact name: ").strip()
                contact_phone = input("Contact phone: ").strip()
                contact_email = input("Contact email: ").strip()

                voucher = AuthUI.prompt_yes_no("Accepts housing vouchers?", default="n")
                record_friendly = AuthUI.prompt_yes_no(
                    "Open to people with records?", default="n"
                )

                success, msg, listing_id = lister.add_property(
                    title=title,
                    location=location,
                    price=price,
                    description=description,
                    contact_name=contact_name,
                    contact_phone=contact_phone,
                    contact_email=contact_email,
                    voucher_friendly=voucher,
                    record_friendly=record_friendly,
                )

                if success:
                    AuthUI.print_success(msg)
                else:
                    AuthUI.handle_error(msg)

                input("\nPress Enter to continue...")

            elif choice == "2":  # Manage listings
                listings = lister.get_my_listings()
                AuthUI.print_header("My Listings")
                if listings:
                    for i, listing in enumerate(listings, 1):
                        print(f"{i}. {listing['title']} - {listing['location']}")
                        print(f"   Price: {listing['price']}")
                        print(f"   Active: {'Yes' if listing['is_active'] else 'No'}\n")
                else:
                    print("No listings yet.")
                input("\nPress Enter to continue...")

            elif choice == "3":  # Area statistics
                location = input("City/area: ").strip() or "Seattle"
                stats = self.master_db.get_area_statistics(location)
                print(f"\n📊 Listings in {location}:")
                print(f"   Total: {stats['total']}")
                print(f"   Voucher-friendly: {stats['voucher_friendly']}")
                print(f"   Record-friendly: {stats['record_friendly']}")
                input("\nPress Enter to continue...")

            elif choice == "4":  # Master database
                location = input("City/area: ").strip() or "Seattle"
                listings = self.master_db.get_listings_by_location(location)
                print(f"\n📍 Available listings in {location}: {len(listings)}")
                for i, listing in enumerate(listings[:10], 1):
                    print(f"{i}. {listing['title']} - {listing['price']}")
                if len(listings) > 10:
                    print(f"... and {len(listings) - 10} more")
                input("\nPress Enter to continue...")

            elif choice == "5":  # Sign out
                self.auth_manager.logout(user["id"])
                AuthUI.print_success("Signed out!")
                break

            elif choice == "6":  # Exit
                print("\nGoodbye!")
                self.storage.close()
                return

    def run(self) -> None:
        """Run the main application."""
        # Authentication
        user = self.show_auth_menu()
        if not user:
            self.storage.close()
            return

        # Route based on role
        role = self.role_auth.get_user_role(user["id"])

        if role == "lister":
            self.run_lister_flow(user)
        else:  # searcher or default
            self.run_searcher_flow(user)
