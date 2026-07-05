import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from housing_scraper.jwt_auth import JwtService
from web.server import app


class FakeScheduler:
    def stop(self):
        return None

    def run_once(self):
        return 0


class FakeStorage:
    def __init__(self):
        self.users = {
            "user@example.com": {
                "id": 1,
                "email": "user@example.com",
                "display_name": "User",
                "password_hash": "",
            }
        }
        self.refresh_tokens = {}

    def create_refresh_token(self, user_id, token_hash, expires_at):
        self.refresh_tokens[token_hash] = user_id

    def get_user_by_email(self, email):
        return self.users.get(email)

    def get_user_by_refresh_token_hash(self, token_hash):
        user_id = self.refresh_tokens.get(token_hash)
        if user_id == 1:
            return self.users["user@example.com"]
        return None

    def revoke_refresh_token(self, token_hash):
        self.refresh_tokens.pop(token_hash, None)


class FakeAuthManager:
    class SessionMgr:
        @staticmethod
        def end_session(_user_id):
            return None

    session_manager = SessionMgr()

    def login_with_validation(self, email, _password, _remember):
        if email == "user@example.com":
            return True, "ok", {"id": 1, "email": email, "display_name": "User"}
        return False, "invalid", None


class FakeRoleAuth:
    def register_with_role(self, email, password, display_name, role):
        return True, "created", {"id": 1, "email": email, "display_name": display_name or "User"}

    def get_user_role(self, _user_id):
        return "searcher"


class FakeMasterDb:
    def get_listings_by_location(self, location, voucher_only=False, record_only=False):
        return []

    def track_area(self, location, frequency_hours=24):
        return True


class FakeSearchManager:
    def __init__(self):
        self.user = None

    def set_user(self, user):
        self.user = user

    def run_search(self, location, query, providers, filter_builder):
        return {
            "search_id": 10,
            "location": location,
            "query": query,
            "results": [],
            "statistics": {"total_listings": 0, "voucher_friendly": 0, "record_friendly": 0, "by_source": []},
        }


class FakeCtx:
    def __init__(self):
        self.storage = FakeStorage()
        self.jwt_service = JwtService()
        self.auth_manager = FakeAuthManager()
        self.role_auth = FakeRoleAuth()
        self.master_db = FakeMasterDb()
        self.scheduler = FakeScheduler()


def test_healthz_and_login_and_refresh(monkeypatch):
    monkeypatch.setenv("WEB_JWT_SECRET", "test-secret")
    app.state.ctx = FakeCtx()

    client = TestClient(app)

    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    login = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "irrelevant", "remember_me": False},
    )
    assert login.status_code == 200
    tokens = login.json()["tokens"]
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["role"] == "searcher"

    refresh = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200
    assert "tokens" in refresh.json()


def test_register_searcher(monkeypatch):
    monkeypatch.setenv("WEB_JWT_SECRET", "test-secret")
    app.state.ctx = FakeCtx()

    client = TestClient(app)
    response = client.post(
        "/auth/register/searcher",
        json={
            "email": "new-user@example.com",
            "password": "StrongPass1!",
            "display_name": "New User",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "searcher"
    assert "tokens" in body
