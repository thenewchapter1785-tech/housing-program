import os
import sys
from typing import Optional

from .auth import authenticate_user, register_google_user, register_user
from .auth_manager import AuthManager
from .auth_ui import AuthUI
from .collector import Collector
from .filter_builder import FilterBuilder
from .models import Listing
from .result_formatter import ResultFormatter
from .search_history import SearchHistory
from .search_manager import SearchManager
from .storage import StorageManager
from ui.result_window import ResultWindow


def prompt_text(label: str, default: Optional[str] = None) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value if value else (default or "")


def run_auth_flow(auth_manager: AuthManager) -> Optional[dict]:
    """Handle authentication flow with friendly prompts."""
    while True:
        choice = AuthUI.show_login_menu()
        
        if choice == "1":  # Sign in
            AuthUI.print_header("Sign In")
            email = AuthUI.prompt_email()
            password = AuthUI.prompt_password()
            remember_me = AuthUI.prompt_yes_no("Remember me on this computer?", default="n")
            
            success, message, user = auth_manager.login_with_validation(
                email, password, remember_me
            )
            if success:
                AuthUI.print_success(message)
                return user
            else:
                AuthUI.handle_error(message)
        
        elif choice == "2":  # Create account
            AuthUI.print_header("Create Account")
            AuthUI.show_password_requirements()
            
            email = AuthUI.prompt_email()
            password = AuthUI.prompt_password("Password", confirm=True)
            display_name = AuthUI.prompt_display_name(default=email.split("@")[0])
            
            success, message, user = auth_manager.register_with_validation(
                email, password, display_name
            )
            if success:
                AuthUI.print_success(message)
                return user
            else:
                AuthUI.handle_error(message)
        
        elif choice == "3":  # Google
            AuthUI.print_header("Google Sign In")
            email = AuthUI.prompt_email("Google email address")
            display_name = AuthUI.prompt_display_name(default=email.split("@")[0])
            
            success, message, user = auth_manager.register_google(
                email, email, display_name
            )
            if success:
                AuthUI.print_success(message)
                return user
            else:
                AuthUI.handle_error(message)
        
        elif choice == "4":  # Exit
            print("\nGoodbye!")
            return None
        
        else:
            AuthUI.handle_error("Invalid choice. Please try again.")


def run_menu() -> None:
    """Main menu with polished auth and search flow."""
    # Initialize storage and auth
    storage_manager = StorageManager(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "housing_app"),
    )
    storage_manager.ensure_schema()
    
    auth_manager = AuthManager(storage_manager)
    search_mgr = SearchManager(storage_manager)
    
    # Authentication flow
    current_user = run_auth_flow(auth_manager)
    if not current_user:
        storage_manager.close()
        return
    
    search_mgr.set_user(current_user)
    
    # Main menu loop
    while True:
        menu_choice = AuthUI.show_main_menu(current_user.get("display_name", current_user["email"]))
        
        if menu_choice == "1":  # New search
            AuthUI.print_header("New Search")
            location = prompt_text("What city are you searching in?", "Seattle")
            query = prompt_text("What type of housing?", "1 bedroom apartment")
            
            # Filter setup
            filter_builder = FilterBuilder()
            filter_builder.quick_preset()
            filter_builder.show_summary()
            
            # Run search
            print("\n🔍 Searching for listings...\n")
            result = search_mgr.run_search(
                location=location,
                query=query,
                providers=["craigslist", "rentals", "padmapper", "rightmove"],
                filter_builder=filter_builder,
            )
            
            # Display results
            formatter = ResultFormatter()
            formatted_text = formatter.format_results(result["results"])
            
            AuthUI.print_header(f"Search Results - {location}")
            print(formatted_text)
            
            # Show statistics
            stats = result["statistics"]
            print("\n📊 Search Statistics:")
            print(f"   Total listings: {stats['total_listings']}")
            print(f"   Voucher-friendly: {stats['voucher_friendly']}")
            print(f"   Record-friendly: {stats['record_friendly']}")
            if stats["by_source"]:
                print("   By source:")
                for source in stats["by_source"]:
                    print(f"      • {source['source']}: {source['count']}")
            
            input("\nPress Enter to continue...")
        
        elif menu_choice == "2":  # Search history
            AuthUI.print_header("Search History")
            history = search_mgr.get_search_history(limit=20)
            
            if not history:
                print("\nNo previous searches found.")
            else:
                for i, search in enumerate(history, 1):
                    print(f"{i}. {search['query_text']} in {search['location']} (${search['price_max']})")
                    print(f"   Date: {search['created_at']}\n")
            
            input("Press Enter to continue...")
        
        elif menu_choice == "3":  # Favorites
            AuthUI.print_header("Saved Favorites")
            favorites = search_mgr.get_favorites()
            
            if not favorites:
                print("\nNo saved favorites yet.")
            else:
                formatter = ResultFormatter()
                for fav in favorites:
                    listing = Listing(**fav)
                    print(formatter.format_listing(listing))
                    if fav.get("favorite_notes"):
                        print(f"\n   Your notes: {fav['favorite_notes']}\n")
            
            input("Press Enter to continue...")
        
        elif menu_choice == "4":  # Change password
            AuthUI.print_header("Change Password")
            old_password = AuthUI.prompt_password("Current password")
            
            AuthUI.show_password_requirements()
            new_password = AuthUI.prompt_password("New password", confirm=True)
            
            success, message = auth_manager.change_password(
                current_user["id"], old_password, new_password
            )
            if success:
                AuthUI.print_success(message)
            else:
                AuthUI.handle_error(message)
            
            input("\nPress Enter to continue...")
        
        elif menu_choice == "5":  # Sign out
            success, message = auth_manager.logout(current_user["id"])
            AuthUI.print_success(message)
            print("\nSigning out...")
            storage_manager.close()
            return
        
        elif menu_choice == "6":  # Exit
            print("\nGoodbye!")
            storage_manager.close()
            return
        
        else:
            AuthUI.handle_error("Invalid choice. Please try again.")
