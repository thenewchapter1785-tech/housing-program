import os
import threading
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel, EmailStr, Field

from housing_scraper.auth_manager import AuthManager
from housing_scraper.area_refresher import AreaRefreshScheduler
from housing_scraper.filter_builder import FilterBuilder
from housing_scraper.jwt_auth import JwtService
from housing_scraper.master_listing_db import MasterListingDatabase
from housing_scraper.role_auth import GovernmentEmailValidator, RoleBasedAuthManager
from housing_scraper.search_manager import SearchManager
from housing_scraper.storage import StorageManager


class RegisterSearcherRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: Optional[str] = None


class RegisterListerRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class SearchRequest(BaseModel):
    location: str
    query: str
    voucher_only: bool = False
    record_only: bool = False
    max_price: Optional[int] = None


class AddListingRequest(BaseModel):
    title: str
    location: str
    price: Optional[str] = None
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    voucher_friendly: bool = False
    record_friendly: bool = False


class AppContext:
    def __init__(self) -> None:
        self.storage = StorageManager(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "housing_app"),
        )
        self.storage.ensure_schema()

        self.master_db = MasterListingDatabase(self.storage.connection)
        self.master_db.ensure_schema()

        self.auth_manager = AuthManager(self.storage)
        self.jwt_service = JwtService()
        self.role_auth = RoleBasedAuthManager(self.storage)
        self.role_auth.ensure_role_schema()

        self.scheduler = AreaRefreshScheduler(self.master_db)
        self.scheduler_thread: Optional[threading.Thread] = None


security = HTTPBearer(auto_error=False)

app = FastAPI(title="Housing Search API", version="1.0.0")
_APP_CTX: Optional[AppContext] = None


def get_ctx() -> AppContext:
    injected = getattr(app.state, "ctx", None)
    if injected is not None:
        return injected

    global _APP_CTX
    if _APP_CTX is None:
        _APP_CTX = AppContext()
    return _APP_CTX

allowed_origins = os.getenv("WEB_ALLOWED_ORIGINS", "http://localhost:3000").split(","
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


def _serialize_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for item in items:
        formatted: Dict[str, Any] = {}
        for key, value in item.items():
            if hasattr(value, "isoformat"):
                formatted[key] = value.isoformat()
            else:
                formatted[key] = value
        output.append(formatted)
    return output


def _issue_token_pair(user: dict, role: str) -> Dict[str, Any]:
    ctx = get_ctx()
    access_token = ctx.jwt_service.create_access_token(user=user, role=role)
    refresh_token = ctx.jwt_service.create_refresh_token(user=user, role=role)
    refresh_hash = ctx.jwt_service.hash_token(refresh_token)
    refresh_payload = ctx.jwt_service.decode(refresh_token)
    exp_ts = int(refresh_payload["exp"])
    from datetime import datetime, timezone

    expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    ctx.storage.create_refresh_token(
        user_id=int(user["id"]),
        token_hash=refresh_hash,
        expires_at=expires_at,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "access_expires_minutes": ctx.jwt_service.access_ttl_minutes,
    }


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    ctx = get_ctx()
    try:
        payload = ctx.jwt_service.decode(creds.credentials)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = ctx.storage.get_user_by_email(str(payload.get("email", "")))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def startup_event() -> None:
    ctx = get_ctx()
    if os.getenv("AUTO_REFRESH_IN_WEB", "false").lower() not in {"true", "1", "yes"}:
        return
    interval = int(os.getenv("AUTO_REFRESH_INTERVAL_SECONDS", "900"))
    ctx.scheduler_thread = threading.Thread(
        target=ctx.scheduler.run_forever,
        kwargs={"interval_seconds": interval},
        daemon=True,
    )
    ctx.scheduler_thread.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    ctx = get_ctx()
    ctx.scheduler.stop()


@app.post("/auth/register/searcher")
def register_searcher(payload: RegisterSearcherRequest) -> Dict[str, Any]:
    ctx = get_ctx()
    success, message, user = ctx.role_auth.register_with_role(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        role="searcher",
    )
    if not success or user is None:
        raise HTTPException(status_code=400, detail=message)

    tokens = _issue_token_pair(user, role="searcher")
    return {"message": message, "tokens": tokens, "user": user, "role": "searcher"}


@app.post("/auth/register/lister")
def register_lister(payload: RegisterListerRequest) -> Dict[str, Any]:
    ctx = get_ctx()
    is_gov, gov_type = GovernmentEmailValidator.is_government_email(payload.email)
    if not is_gov:
        raise HTTPException(
            status_code=403,
            detail="Lister accounts require state/federal government email (.gov).",
        )

    whitelist_ok, whitelist_msg = GovernmentEmailValidator.whitelist_email(
        ctx.storage, payload.email
    )
    if not whitelist_ok:
        raise HTTPException(status_code=400, detail=whitelist_msg)

    success, message, user = ctx.role_auth.register_with_role(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        role="lister",
    )
    if not success or user is None:
        raise HTTPException(status_code=400, detail=message)

    tokens = _issue_token_pair(user, role="lister")
    return {
        "message": message,
        "tokens": tokens,
        "user": user,
        "role": "lister",
        "government_type": gov_type,
    }


@app.post("/auth/login")
def login(payload: LoginRequest) -> Dict[str, Any]:
    ctx = get_ctx()
    success, message, user = ctx.auth_manager.login_with_validation(
        payload.email,
        payload.password,
        payload.remember_me,
    )
    if not success or user is None:
        raise HTTPException(status_code=401, detail=message)

    role = ctx.role_auth.get_user_role(int(user["id"])) or "searcher"
    tokens = _issue_token_pair(user, role=role)
    return {"message": message, "tokens": tokens, "user": user, "role": role}


@app.post("/auth/logout")
def logout(
    payload: RefreshRequest,
    user: dict = Depends(get_current_user),
) -> Dict[str, str]:
    ctx = get_ctx()
    refresh_hash = ctx.jwt_service.hash_token(payload.refresh_token)
    ctx.storage.revoke_refresh_token(refresh_hash)
    ctx.auth_manager.session_manager.end_session(int(user["id"]))
    return {"message": "Logged out"}


@app.post("/auth/refresh")
def refresh_tokens(payload: RefreshRequest) -> Dict[str, Any]:
    ctx = get_ctx()
    try:
        token_payload = ctx.jwt_service.decode(payload.refresh_token)
        if token_payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    refresh_hash = ctx.jwt_service.hash_token(payload.refresh_token)
    user = ctx.storage.get_user_by_refresh_token_hash(refresh_hash)
    if not user:
        raise HTTPException(status_code=401, detail="Refresh token revoked or unknown")

    role = ctx.role_auth.get_user_role(int(user["id"])) or "searcher"
    ctx.storage.revoke_refresh_token(refresh_hash)
    tokens = _issue_token_pair(user, role=role)
    return {"tokens": tokens, "user": user, "role": role}


@app.get("/auth/me")
def me(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    ctx = get_ctx()
    role = ctx.role_auth.get_user_role(int(user["id"])) or "searcher"
    return {"user": user, "role": role}


@app.post("/search")
def search(payload: SearchRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    ctx = get_ctx()
    filter_builder = FilterBuilder()
    filter_builder.voucher_accepted = payload.voucher_only if payload.voucher_only else None
    filter_builder.record_friendly = payload.record_only if payload.record_only else None
    filter_builder.max_price = payload.max_price

    search_mgr = SearchManager(ctx.storage, master_db=ctx.master_db)
    search_mgr.set_user(user)
    result = search_mgr.run_search(
        location=payload.location,
        query=payload.query,
        providers=["craigslist", "rentals", "padmapper", "rightmove"],
        filter_builder=filter_builder,
    )

    listings = [listing.to_dict() for listing in result["results"]]
    master_matches = ctx.master_db.get_listings_by_location(payload.location)

    return {
        "search_id": result["search_id"],
        "location": payload.location,
        "query": payload.query,
        "user_results": listings,
        "user_statistics": result["statistics"],
        "master_database_count": len(master_matches),
    }


@app.post("/lister/listings")
def add_listing(
    payload: AddListingRequest,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    ctx = get_ctx()
    role = ctx.role_auth.get_user_role(int(user["id"])) or "searcher"
    if role != "lister" and role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only lister/agent accounts can add properties.",
        )

    from housing_scraper.lister_interface import ListerInterface

    lister = ListerInterface(int(user["id"]), ctx.storage, ctx.master_db)
    success, message, listing_id = lister.add_property(
        title=payload.title,
        location=payload.location,
        price=payload.price,
        description=payload.description,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
        contact_email=str(payload.contact_email) if payload.contact_email else None,
        voucher_friendly=payload.voucher_friendly,
        record_friendly=payload.record_friendly,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"message": message, "listing_id": listing_id}


@app.get("/master/listings")
def get_master_listings(
    location: Optional[str] = None,
    voucher_only: bool = False,
    record_only: bool = False,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    ctx = get_ctx()
    if not location:
        raise HTTPException(status_code=400, detail="location is required")

    listings = ctx.master_db.get_listings_by_location(
        location=location,
        voucher_only=voucher_only,
        record_only=record_only,
    )
    return {
        "location": location,
        "count": len(listings),
        "listings": _serialize_items(listings),
    }


@app.post("/admin/areas/track")
def track_area(
    location: str,
    frequency_hours: int = 24,
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    ctx = get_ctx()
    role = ctx.role_auth.get_user_role(int(user["id"])) or "searcher"
    if role not in {"admin", "lister"}:
        raise HTTPException(status_code=403, detail="Insufficient role for area tracking")
    ok = ctx.master_db.track_area(location, frequency_hours=frequency_hours)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to track area")
    return {"message": "Area tracking updated", "location": location, "frequency_hours": frequency_hours}


@app.post("/admin/areas/refresh-now")
def refresh_now(user: dict = Depends(get_current_user)) -> Dict[str, int]:
    ctx = get_ctx()
    role = ctx.role_auth.get_user_role(int(user["id"])) or "searcher"
    if role not in {"admin", "lister"}:
        raise HTTPException(status_code=403, detail="Insufficient role for refresh")
    updated = ctx.scheduler.run_once()
    return {"updated_records": updated}
