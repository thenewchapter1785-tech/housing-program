import hashlib
import os
from typing import Optional

from .storage import StorageManager


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate_user(storage: StorageManager, email: str, password: str) -> Optional[dict]:
    user = storage.get_user_by_email(email)
    if not user:
        return None
    if user["password_hash"] != hash_password(password):
        return None
    return user


def register_user(storage: StorageManager, email: str, password: str, display_name: Optional[str] = None) -> dict:
    existing = storage.get_user_by_email(email)
    if existing:
        raise ValueError("User already exists")
    user_id = storage.create_user(email=email, password_hash=hash_password(password), display_name=display_name)
    return {"id": user_id, "email": email, "display_name": display_name}


def register_google_user(storage: StorageManager, email: str, google_id: str, display_name: Optional[str] = None) -> dict:
    existing = storage.get_user_by_email(email)
    if existing:
        if existing.get("google_id") is None:
            with storage.connection.cursor() as cursor:
                cursor.execute("UPDATE users SET google_id = %s WHERE id = %s", (google_id, existing["id"]))
        return {"id": existing["id"], "email": existing["email"], "display_name": existing.get("display_name")}
    user_id = storage.create_user(email=email, password_hash=hash_password("google-oauth"), display_name=display_name, google_id=google_id)
    return {"id": user_id, "email": email, "display_name": display_name}
