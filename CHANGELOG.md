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

### Changed
- Scraper configuration now infers `SCRAPER_ENV` (or CI context) to cap non-production runs at five API chunks by default while keeping production runs uncapped unless `MAX_CHUNKS`/`--max-chunks` is explicitly set.
