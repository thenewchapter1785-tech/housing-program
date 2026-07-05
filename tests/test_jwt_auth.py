import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from housing_scraper.jwt_auth import JwtService


def test_access_and_refresh_token_types(monkeypatch):
    monkeypatch.setenv("WEB_JWT_SECRET", "test-secret")
    jwt_service = JwtService()

    user = {"id": 42, "email": "user@example.com"}
    access = jwt_service.create_access_token(user, role="searcher")
    refresh = jwt_service.create_refresh_token(user, role="searcher")

    access_payload = jwt_service.decode(access)
    refresh_payload = jwt_service.decode(refresh)

    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    assert access_payload["sub"] == "42"
    assert refresh_payload["sub"] == "42"


def test_hash_token_stable(monkeypatch):
    monkeypatch.setenv("WEB_JWT_SECRET", "test-secret")
    jwt_service = JwtService()

    token = "sample-token"
    h1 = jwt_service.hash_token(token)
    h2 = jwt_service.hash_token(token)
    assert h1 == h2
    assert len(h1) == 64
