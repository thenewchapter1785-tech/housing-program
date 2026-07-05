# Housing Aggregator

A starter Python project for collecting public housing listings from multiple sources and flagging listings that may be suitable for voucher holders, rental assistance seekers, or applicants with prior records.

## Important note

Use this project only for public, lawful data collection. Respect each site’s terms of service, robots rules, rate limits, and privacy expectations. Avoid scraping private accounts, login-protected pages, or personal data.

## What this starter includes

- A modular scraper architecture for multiple housing sources
- A shared listing model with flags for voucher support and record-friendly housing
- A simple CLI entry point for running a search

## Project structure

- src/housing_scraper/config.py - shared search settings
- src/housing_scraper/models.py - listing data model
- src/housing_scraper/collector.py - orchestrates all scrapers
- src/housing_scraper/sources/ - provider-specific scraper modules
- src/main.py - command-line entry point

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run a sample search:
   ```bash
   python src/main.py --city seattle --query "studio apartment"
   ```

## Next steps

- Add provider-specific parsing logic for Craigslist, Facebook Marketplace, Rent.com, and local private-market sources.
- Add storage for results in JSON, CSV, or a database.
- Add filters for voucher acceptance and other housing criteria.
