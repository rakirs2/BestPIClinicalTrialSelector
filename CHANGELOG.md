# Changelog

All notable changes to this project will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project aims to adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project README outlining vision, objectives, and roadmap.
- Documentation scaffolding for contributing guidelines, system operations, architecture overview, worklog, and changelog.
- Python ClinicalTrials.gov scraper with async HTTP client, normalization layer, Postgres schema management, CLI runner, environment template, tests, and DB size guard.
- GitHub Actions workflow to install dependencies and run `pytest` on pushes/PRs.
- Checkpointable ingestion runs with resumable CLI (`--resume-latest`, `status` command), signal-aware shutdowns, and enhanced logging/documentation.
- Investigator topic aggregation job (`python -m aggregations.investigator_topics`) plus `investigator_topic_counts` table storing JSON maps for conditions and intervention types, including a `recommend` command that ranks PIs via phase- and recency-weighted scores.
- Scraper telemetry pipeline that persists chunk-by-chunk logs in `scraper_run_logs`, surfaces them through `/api/scraper-status`, and renders the latest 50 entries on the Blazor `/scraper-status` page.
- Frontend MSTest coverage for scraper telemetry, theme management, and formatting helpers along with a browser-side theme client.
- Docker-based local development stack (`docker-compose.local.yml`, `LOCAL_DEV.md`) pairing Postgres + Blazor plus updated `.env` guidance.
- Automated deploy health checks (droplet-side curl plus public endpoint verification) wired into the GitHub Actions Deploy workflow.

### Changed
- Scraper configuration now infers `SCRAPER_ENV` (or CI context) to cap non-production runs at five API chunks by default while keeping production runs uncapped unless `MAX_CHUNKS`/`--max-chunks` is explicitly set.
- Simplified the Blazor UI color palette, added a ready-made light/dark toggle, improved mobile nav highlighting, and cleaned up scraper status pills/logs for readability.
- Deploy workflow now injects `FRONTEND_IMAGE` for Docker Compose, requires GHCR images instead of local builds, and is enforced as a required status check before merging PRs.
- Home page hero now includes a "Deployment verified" note so humans can confirm the latest build landed.
- Fixed ThemeToggle to defer JavaScript interop until after the first render, preventing Blazor prerender crashes that surfaced as 500s in production.
