import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt


class JwtService:
    def __init__(self) -> None:
        self.secret = os.getenv("WEB_JWT_SECRET", "change-me-in-production")
        self.algorithm = os.getenv("WEB_JWT_ALG", "HS256")
        self.access_ttl_minutes = int(os.getenv("WEB_ACCESS_TTL_MINUTES", "30"))
        self.refresh_ttl_days = int(os.getenv("WEB_REFRESH_TTL_DAYS", "14"))

    def _base_payload(self, user: dict, role: str) -> Dict[str, Any]:
        return {
            "sub": str(user["id"]),
            "email": user["email"],
            "role": role,
            "iat": int(datetime.now(timezone.utc).timestamp()),
        }

    def create_access_token(self, user: dict, role: str) -> str:
        exp = datetime.now(timezone.utc) + timedelta(minutes=self.access_ttl_minutes)
        payload = self._base_payload(user, role)
        payload.update({"type": "access", "exp": int(exp.timestamp())})
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def create_refresh_token(self, user: dict, role: str) -> str:
        exp = datetime.now(timezone.utc) + timedelta(days=self.refresh_ttl_days)
        payload = self._base_payload(user, role)
        payload.update(
            {
                "type": "refresh",
                "exp": int(exp.timestamp()),
                "jti": secrets.token_urlsafe(16),
            }
        )
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode(self, token: str) -> Dict[str, Any]:
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
