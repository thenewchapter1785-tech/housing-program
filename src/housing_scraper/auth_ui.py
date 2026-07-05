"""
User-friendly authentication interface with guided prompts and error handling.
"""

from typing import Optional, Tuple
import getpass
import sys


class AuthUI:
    """Friendly UI for authentication flows."""

    @staticmethod
    def clear_screen():
        """Clear terminal screen."""
        try:
            import os
            os.system("cls" if sys.platform == "win32" else "clear")
        except:
            print("\n" * 3)

    @staticmethod
    def print_header(title: str):
        """Print a nice header."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    @staticmethod
    def print_error(message: str):
        """Print error message."""
        print(f"\n❌ {message}")

    @staticmethod
    def print_success(message: str):
        """Print success message."""
        print(f"\n✓ {message}")

    @staticmethod
    def print_warning(message: str):
        """Print warning message."""
        print(f"\n⚠️  {message}")

    @staticmethod
    def prompt_email(label: str = "Email address") -> str:
        """Prompt for email with validation feedback."""
        while True:
            email = input(f"\n{label}: ").strip()
            if not email:
                AuthUI.print_error("Email cannot be empty")
                continue
            return email

    @staticmethod
    def prompt_password(label: str = "Password", confirm: bool = False) -> str:
        """Prompt for password (hidden input)."""
        while True:
            password = getpass.getpass(f"\n{label}: ")
            if not password:
                AuthUI.print_error("Password cannot be empty")
                continue
            
            if confirm:
                password_confirm = getpass.getpass("Confirm password: ")
                if password != password_confirm:
                    AuthUI.print_error("Passwords do not match")
                    continue
            
            return password

    @staticmethod
    def prompt_display_name(default: Optional[str] = None) -> str:
        """Prompt for display name."""
        prompt = f"Display name"
        if default:
            prompt += f" [{default}]"
        prompt += ": "
        
        name = input(f"\n{prompt}").strip()
        return name if name else default

    @staticmethod
    def prompt_yes_no(question: str, default: str = "n") -> bool:
        """Prompt for yes/no answer."""
        default_display = "[Y/n]" if default.lower() in ["y", "yes"] else "[y/N]"
        response = input(f"\n{question} {default_display}: ").strip().lower()
        
        if not response:
            return default.lower() in ["y", "yes"]
        return response in ["y", "yes", "1", "true"]

    @staticmethod
    def show_login_menu() -> str:
        """Show friendly login menu."""
        AuthUI.print_header("Housing Search Assistant - Sign In")
        
        print("\n1. Sign in with email and password")
        print("2. Create a new account")
        print("3. Continue with Google")
        print("4. Exit")
        
        choice = input("\nChoose an option (1-4): ").strip()
        return choice

    @staticmethod
    def show_main_menu(user_name: str) -> str:
        """Show main menu after login."""
        AuthUI.print_header(f"Welcome, {user_name}!")
        
        print("\n1. Start a new search")
        print("2. View search history")
        print("3. View saved favorites")
        print("4. Change password")
        print("5. Sign out")
        print("6. Exit")
        
        choice = input("\nChoose an option (1-6): ").strip()
        return choice

    @staticmethod
    def show_password_requirements():
        """Show password requirements."""
        print("\n📋 Password Requirements:")
        print("   • At least 8 characters long")
        print("   • At least one uppercase letter (A-Z)")
        print("   • At least one lowercase letter (a-z)")
        print("   • At least one number (0-9)")
        print("   • At least one special character (@$!%*?&#._-)")

    @staticmethod
    def handle_error(error_message: str, retry_available: bool = True):
        """Handle and display error."""
        AuthUI.print_error(error_message)
        if retry_available:
            print("Please try again.")

    @staticmethod
    def handle_warning(warning_message: str):
        """Handle and display warning."""
        AuthUI.print_warning(warning_message)
