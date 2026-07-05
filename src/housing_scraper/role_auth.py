"""
Enhanced authentication with role-based access and government email verification.
"""

import re
from typing import Optional, Tuple
from .storage import StorageManager
from . import auth as auth_module


class GovernmentEmailValidator:
    """Validates state and federal email addresses."""

    # State and federal government email domains
    FEDERAL_DOMAINS = [
        "gov",  # Generic .gov
        "nih.gov",
        "hhs.gov",
        "hud.gov",  # Housing and Urban Development
        "va.gov",  # Veterans Affairs
        "usda.gov",
        "opm.gov",
    ]

    STATE_DOMAINS = [
        # All 50 states - simplified pattern
        r"\.gov",  # Any .gov domain
    ]

    @staticmethod
    def is_government_email(email: str) -> Tuple[bool, str]:
        """
        Validate if email is from government domain.
        Returns: (is_government, government_type)
        """
        email = email.lower()
        domain = email.split("@")[1] if "@" in email else ""

        # Check federal
        for fed_domain in GovernmentEmailValidator.FEDERAL_DOMAINS:
            if domain.endswith(fed_domain):
                return True, "federal"

        # Check state/local (.gov domains)
        if domain.endswith(".gov"):
            return True, "state_local"

        return False, None

    @staticmethod
    def whitelist_email(storage: StorageManager, email: str) -> Tuple[bool, str]:
        """
        Add email to government whitelist for secure access.
        Returns: (success, message)
        """
        is_gov, gov_type = GovernmentEmailValidator.is_government_email(email)
        if not is_gov:
            return False, "Email must be from a government domain (.gov)"

        try:
            with storage.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO government_whitelist (email, gov_type)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE verified_at = CURRENT_TIMESTAMP
                    """,
                    (email, gov_type),
                )
            return True, f"Government email {email} whitelisted"
        except Exception as e:
            return False, f"Error whitelisting email: {str(e)}"


class RoleBasedAuthManager:
    """Authentication with role-based access control."""

    USER_ROLES = {
        "searcher": "Housing seeker/tenant",
        "lister": "Real estate agent/property lister",
        "admin": "System administrator",
    }

    def __init__(self, storage: StorageManager):
        self.storage = storage

    def ensure_role_schema(self):
        """Create role and government whitelist tables."""
        with self.storage.connection.cursor() as cursor:
            # User roles table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_roles (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL UNIQUE,
                    role VARCHAR(50) NOT NULL DEFAULT 'searcher',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )

            # Government email whitelist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS government_whitelist (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    gov_type VARCHAR(50),
                    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def register_with_role(
        self,
        email: str,
        password: str,
        display_name: Optional[str],
        role: str = "searcher",
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Register user with specified role.
        Returns: (success, message, user)
        """
        # Validate role
        if role not in self.USER_ROLES:
            return False, f"Invalid role. Must be: {', '.join(self.USER_ROLES.keys())}", None

        # Special handling for lister role - require government email
        if role == "lister":
            is_gov, gov_type = GovernmentEmailValidator.is_government_email(email)
            if not is_gov:
                return (
                    False,
                    "Lister/agent accounts require a government email address (.gov)",
                    None,
                )
            # Verify in whitelist
            with self.storage.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM government_whitelist WHERE email = %s",
                    (email,),
                )
                if not cursor.fetchone():
                    return (
                        False,
                        "Email not yet verified. Please contact administration.",
                        None,
                    )

        # Register via standard auth
        try:
            user = auth_module.register_user(
                self.storage, email=email, password=password, display_name=display_name
            )

            # Set role
            with self.storage.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user_roles (user_id, role) VALUES (%s, %s)",
                    (user["id"], role),
                )

            msg = f"Account created as {self.USER_ROLES[role]}"
            return True, msg, user

        except Exception as e:
            return False, f"Registration failed: {str(e)}", None

    def get_user_role(self, user_id: int) -> Optional[str]:
        """Get user's role."""
        with self.storage.connection.cursor() as cursor:
            cursor.execute(
                "SELECT role FROM user_roles WHERE user_id = %s",
                (user_id,),
            )
            result = cursor.fetchone()
            return result["role"] if result else "searcher"

    def set_user_role(self, user_id: int, role: str) -> bool:
        """Update user role (admin only in production)."""
        if role not in self.USER_ROLES:
            return False
        try:
            with self.storage.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user_roles (user_id, role) VALUES (%s, %s) ON DUPLICATE KEY UPDATE role = %s",
                    (user_id, role, role),
                )
            return True
        except Exception:
            return False

    def is_government_email(self, email: str) -> bool:
        """Check if email is government domain."""
        is_gov, _ = GovernmentEmailValidator.is_government_email(email)
        return is_gov

    def is_lister(self, user_id: int) -> bool:
        """Check if user is a lister/agent."""
        role = self.get_user_role(user_id)
        return role == "lister"

    def is_searcher(self, user_id: int) -> bool:
        """Check if user is a searcher."""
        role = self.get_user_role(user_id)
        return role in ["searcher", "admin"]
