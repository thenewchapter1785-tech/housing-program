# Housing Aggregator

Dual-mode housing platform with:
- Desktop runtime for local installation on Windows/macOS
- Secure web API runtime for server deployment
- Shared authentication and role model for both user types:
   - Housing seekers (search + save)
   - Property listers/agents (government-email-gated listing access)

## Important note

Use this project only for public, lawful data collection. Respect each site’s terms of service, robots rules, rate limits, and privacy expectations. Avoid scraping private accounts, login-protected pages, or personal data.

## What this includes

- Modular scraper architecture for multiple housing sources
- Role-based authentication (searcher/lister/admin)
- Government email validation for lister access
- Personal user search database + separate shared master listing database
- Desktop and secure web deployment entrypoints

## Project structure

- src/housing_scraper/config.py - shared search settings
- src/housing_scraper/models.py - listing data model
- src/housing_scraper/collector.py - orchestrates all scrapers
- src/housing_scraper/sources/ - provider-specific scraper modules
- src/housing_scraper/master_listing_db.py - shared aggregate listing store
- src/housing_scraper/role_auth.py - role + government email rules
- src/housing_scraper/lister_interface.py - lister CRUD operations
- src/housing_scraper/app_launcher.py - role-routed desktop flow
- src/web/server.py - secure FastAPI server
- src/desktop/main.py - desktop packaging entrypoint
- src/main.py - runtime selector entrypoint

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run desktop mode (default):
   ```bash
   python src/main.py
   ```

## Runtime modes

Desktop app flow:
```bash
python src/main.py --platform desktop
```

Secure web API:
```bash
python src/main.py --platform web
```

Background refresh worker:
```bash
python src/main.py --platform worker
```

Legacy collector CLI:
```bash
python src/main.py --platform cli --city seattle --query "studio apartment"
```

## Desktop installation builds

Build a distributable binary on each target OS:
```bash
python scripts/build_desktop.py
```

Notes:
- Build on Windows to produce Windows executable
- Build on macOS to produce macOS executable

## Secure web deployment

Apply migrations first:
```bash
python scripts/apply_migrations.py
```

Run core test suite:
```bash
pytest -q tests/test_jwt_auth.py tests/test_migrations_manager.py tests/test_api_auth_flow.py
```

Run MySQL integration tests (optional):
```bash
RUN_MYSQL_INTEGRATION=true pytest -q tests/test_storage.py
```

Run locally:
```bash
python src/main.py --platform web
```

Run with Docker:
```bash
docker build -t housing-platform .
docker run --env-file .env -p 8000:8000 housing-platform
```

Security controls in web mode:
- JWT access tokens + rotating refresh tokens
- Rate-limited login flow
- Role checks on lister endpoints
- Government-email requirement for lister account registration
- CORS allowlist via `WEB_ALLOWED_ORIGINS`

## Ordered implementation status

1. Automatic area-refresh scheduler:
- Background refresh loop reads due areas from `area_tracking`
- Refreshes provider data and syncs into `master_listings`
- Dedicated worker runtime via `--platform worker`

2. Secure web deployment enhancements:
- Persistent refresh token sessions in MySQL (`auth_refresh_tokens` table)
- HTTPS reverse proxy config via Nginx at `deploy/nginx/default.conf`
- Docker Compose includes `worker` and `nginx` services
- JWT access tokens + rotating refresh tokens for web auth

## CI

- GitHub Actions pipeline at `.github/workflows/ci.yml`
- Runs compile checks and auth/migration/API tests on push and pull requests

3. Native desktop GUI layer:
- Tkinter desktop app at `src/ui/desktop_gui.py`
- Role-aware tabs for auth, search, lister actions, and master DB views
- Desktop entrypoint now launches GUI by default (`src/desktop/main.py`)
- CLI fallback remains available with `DESKTOP_USE_CLI=true`

## Data model behavior

- Every search is saved for the current user in personal search tables
- Every search result is also upserted into the shared `master_listings` database
- Lister-added properties are stored in manual listing tables and synced into `master_listings`
- Master listing source tracking records where each listing came from

## Next steps

- Add endpoint-level integration tests with test containers
- Add role-specific UI tests for desktop tabs
- Add migration CI check before deployment
