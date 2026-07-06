# Best PI Clinical Trial Selector

Best PI Clinical Trial Selector aims to help clinical operations teams identify the most suitable principal investigators (PIs) for upcoming trials. The long‑term goal is to combine historical site performance, therapeutic expertise, enrollment velocity, and operational constraints into a single decision support interface.

## Key Objectives

- Centralize profiles for investigators, sites, and prior studies.
- Score potential PIs using transparent, data‑driven criteria.
- Surface tradeoffs (speed, quality, capacity) to support stakeholder discussions.
- Provide exportable shortlists for downstream feasibility and contracting workflows.

## Getting Started

This repository is at the bootstrap stage. The current milestone focuses on a **Python-based ClinicalTrials.gov scraper** that loads every public trial into a local PostgreSQL database. A typical setup involves:

1. **Clone the repo**
   ```bash
   git clone https://github.com/<org>/BestPIClinicalTrialSelector.git
   cd BestPIClinicalTrialSelector
   ```
2. **Provision Python + Postgres**
   - Python 3.14 (system interpreter on macOS works).
   - Local PostgreSQL instance (Docker or native). Create an empty database, e.g. `clinicaltrials`.
3. **Configure environment**
   - Copy `.env.example` to `.env` and update `POSTGRES_DSN` plus optional tuning values.
   - Create a virtual environment and install dependencies:
     ```bash
     python3 -m venv .venv
     .venv/bin/pip install -r requirements.txt
     ```
4. **Run the scraper**
   ```bash
   python -m scrapers.clinicaltrials.runner full-sync --env-file .env
   ```
   The command streams every study through the v2 ClinicalTrials.gov API, stores the raw JSON payload plus tabularized data, and halts automatically if the database exceeds the configured size limit (default 10 GB). Progress is tracked in the `ingest_runs` table.
5. **Run tests**
   ```bash
   .venv/bin/pytest
   ```
   Tests currently cover the normalization pipeline; expand coverage as parsers evolve.

## Continuous Integration

GitHub Actions (`.github/workflows/tests.yml`) automatically installs dependencies and runs `pytest` on every push and pull request targeting `main`, ensuring the scraper stays green before merges.

## Proposed Architecture

- **Ingestion layer**: Python ETL jobs that collect data from ClinicalTrials.gov (current milestone) with planned connectors for CTMS, EDC, and EU CTR.
- **Feature store**: cleansed investigator/site metrics (enrollment rate, screen fail %, deviation rate).
- **Ranking engine**: weighted scoring or ML model to suggest best-fit PIs per protocol.
- **Review UI**: web dashboard for feasibility teams to compare candidates and capture decisions.

See `ARCHITECTURE.md` for the detailed ingestion pipeline and future .NET service layers.

## Contributing

1. Create an issue outlining the feature or fix.
2. Branch from `main` using a descriptive name (e.g., `feature/scoring-engine`).
3. Open a pull request with context, screenshots (if applicable), and test notes.

## Roadmap

- Define tech stack and initial domain model.
- Complete the ClinicalTrials.gov ingestion pipeline (✅ done via Python scraper).
- Ship an MVP scoring heuristic with basic UI output.
- Add automated tests and deployment pipeline.

## License

Add licensing information here once the legal framework is decided.
