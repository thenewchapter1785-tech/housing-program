"""
Enhanced authentication manager with validation, security, and user experience improvements.
"""

import re
import time
from typing import Optional, Tuple, Dict, Any
from .storage import StorageManager
from . import auth as auth_module


class AuthValidator:
    """Validates emails, passwords, and other auth inputs."""

    STRONG_PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email format.
        Returns: (is_valid, message)
        """
        email = email.strip()
        if not email:
            return False, "Email cannot be empty"
        if len(email) > 255:
            return False, "Email is too long"
        if not re.match(AuthValidator.EMAIL_REGEX, email):
            return False, "Please enter a valid email address"
        return True, ""

    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> Tuple[bool, str]:
        """
        Validate password strength.
        Returns: (is_valid, message)
        """
        if not password:
            return False, "Password cannot be empty"
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters"
        if len(password) > 128:
            return False, "Password is too long"
        
        # Check for at least one uppercase, lowercase, number, special char
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"
        if not re.search(r"[@$!%*?&#._-]", password):
            return False, "Password must contain at least one special character (@$!%*?&#._-)"
        
        return True, ""

    @staticmethod
    def validate_display_name(name: str) -> Tuple[bool, str]:
        """Validate display name."""
        if not name:
            return False, "Display name cannot be empty"
        if len(name) < 2:
            return False, "Display name must be at least 2 characters"
        if len(name) > 100:
            return False, "Display name is too long"
        return True, ""


class SessionManager:
    """Manages user sessions and login state."""

    def __init__(self):
        self.sessions: Dict[int, Dict[str, Any]] = {}
        self.failed_attempts: Dict[str, Tuple[int, float]] = {}  # email -> (count, last_attempt_time)

    def record_failed_attempt(self, email: str) -> Tuple[bool, str]:
        """
        Record a failed login attempt.
        Returns: (can_retry, message)
        """
        now = time.time()
        count, last_time = self.failed_attempts.get(email, (0, 0))
        
        # Reset if last attempt was more than 15 minutes ago
        if now - last_time > 900:  # 900 seconds = 15 minutes
            count = 0
        
        count += 1
        self.failed_attempts[email] = (count, now)
        
        if count >= 5:
            # Lock out after 5 failed attempts for 15 minutes
            return False, "Too many failed login attempts. Please try again in 15 minutes."
        
        remaining = 5 - count
        if remaining <= 2:
            return True, f"Warning: {remaining} attempts remaining before account lockout"
        
        return True, ""

    def clear_failed_attempts(self, email: str) -> None:
        """Clear failed attempts on successful login."""
        self.failed_attempts.pop(email, None)

    def create_session(self, user: dict, remember_me: bool = False) -> str:
        """
        Create a new session.
        Returns: session_token
        """
        session_token = f"session_{user['id']}_{int(time.time())}"
        self.sessions[user["id"]] = {
            "user": user,
            "token": session_token,
            "created_at": time.time(),
            "remember_me": remember_me,
        }
        return session_token

    def get_session(self, user_id: int) -> Optional[dict]:
        """Get active session for user."""
        return self.sessions.get(user_id)

    def end_session(self, user_id: int) -> None:
        """End a session (logout)."""
        self.sessions.pop(user_id, None)

    def get_current_user(self, user_id: int) -> Optional[dict]:
        """Get current user from session."""
        session = self.get_session(user_id)
        return session["user"] if session else None


class AuthManager:
    """High-level auth management with validation, sessions, and user experience."""

    def __init__(self, storage: StorageManager):
        self.storage = storage
        self.session_manager = SessionManager()
        self.validator = AuthValidator()

    def register_with_validation(
        self, email: str, password: str, display_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Register a new user with full validation.
        Returns: (success, message, user_data)
        """
        # Validate email
        email_valid, email_msg = self.validator.validate_email(email)
        if not email_valid:
            return False, email_msg, None

        # Check if email already exists
        existing = self.storage.get_user_by_email(email)
        if existing:
            return False, "An account with this email already exists", None

        # Validate password
        password_valid, password_msg = self.validator.validate_password(password)
        if not password_valid:
            return False, password_msg, None

        # Validate display name if provided
        if display_name:
            name_valid, name_msg = self.validator.validate_display_name(display_name)
            if not name_valid:
                return False, name_msg, None
        else:
            display_name = email.split("@")[0]

        # Register user
        try:
            user = auth_module.register_user(
                self.storage, email=email, password=password, display_name=display_name
            )
            return True, f"Account created successfully! Welcome, {display_name}!", user
        except Exception as e:
            return False, f"Registration failed: {str(e)}", None

    def login_with_validation(
        self, email: str, password: str, remember_me: bool = False
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Login user with full validation and rate limiting.
        Returns: (success, message, user_data)
        """
        # Validate email format
        email_valid, email_msg = self.validator.validate_email(email)
        if not email_valid:
            return False, email_msg, None

        # Check rate limiting
        can_retry, limit_msg = self.session_manager.record_failed_attempt(email)
        if not can_retry:
            return False, limit_msg, None

        # Authenticate
        user = auth_module.authenticate_user(self.storage, email=email, password=password)
        if not user:
            return False, "Invalid email or password. Please try again.", None

        # Clear failed attempts on success
        self.session_manager.clear_failed_attempts(email)

        # Create session
        self.session_manager.create_session(user, remember_me=remember_me)

        return True, f"Welcome back, {user.get('display_name', email)}!", user

    def register_google(
        self, email: str, google_id: str, display_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Register or link Google account.
        Returns: (success, message, user_data)
        """
        # Validate email
        email_valid, email_msg = self.validator.validate_email(email)
        if not email_valid:
            return False, email_msg, None

        # Validate display name if provided
        if display_name:
            name_valid, name_msg = self.validator.validate_display_name(display_name)
            if not name_valid:
                return False, name_msg, None
        else:
            display_name = email.split("@")[0]

        try:
            user = auth_module.register_google_user(
                self.storage, email=email, google_id=google_id, display_name=display_name
            )
            is_new = self.storage.get_user_by_email(email) == user
            msg = (
                f"Account created with Google! Welcome, {display_name}!"
                if is_new
                else f"Google account linked! Welcome back, {display_name}!"
            )
            self.session_manager.create_session(user)
            return True, msg, user
        except Exception as e:
            return False, f"Google registration failed: {str(e)}", None

    def logout(self, user_id: int) -> Tuple[bool, str]:
        """
        Logout user.
        Returns: (success, message)
        """
        user = self.session_manager.get_current_user(user_id)
        if user:
            self.session_manager.end_session(user_id)
            return True, f"Goodbye, {user.get('display_name', 'user')}!"
        return False, "No active session"

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> Tuple[bool, str]:
        """
        Change user password with validation.
        Returns: (success, message)
        """
        user = self.session_manager.get_current_user(user_id)
        if not user:
            return False, "No active session"

        # Verify old password
        verified = auth_module.authenticate_user(
            self.storage, email=user["email"], password=old_password
        )
        if not verified:
            return False, "Current password is incorrect"

        # Validate new password
        new_valid, new_msg = self.validator.validate_password(new_password)
        if not new_valid:
            return False, f"New password invalid: {new_msg}"

        # Prevent reusing same password
        if old_password == new_password:
            return False, "New password must be different from current password"

        # Update password
        try:
            new_hash = auth_module.hash_password(new_password)
            with self.storage.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (new_hash, user_id),
                )
            return True, "Password changed successfully!"
        except Exception as e:
            return False, f"Failed to change password: {str(e)}"

    def get_current_user(self, user_id: int) -> Optional[dict]:
        """Get current logged-in user."""
        return self.session_manager.get_current_user(user_id)
