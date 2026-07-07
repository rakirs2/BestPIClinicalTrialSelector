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
   - Set `RESUME_LATEST=true` if you’d like the scraper to automatically pick up the most recent unfinished run.
   - Create a virtual environment and install dependencies:
     ```bash
     python3 -m venv .venv
     .venv/bin/pip install -r requirements.txt
     ```
4. **Run the scraper**
   ```bash
   python -m scrapers.clinicaltrials.runner --env-file .env full-sync
   ```
   The command streams every study through the v2 ClinicalTrials.gov API, stores the raw JSON payload plus tabularized data, and halts automatically if the database exceeds the configured size limit (default 10 GB). Progress is tracked in the `ingest_runs` table.
5. **Run tests**
   ```bash
   .venv/bin/pytest
   ```
   Tests currently cover the normalization pipeline; expand coverage as parsers evolve.

## Frontend Preview (Blazor Server MVP)

The `frontend/BestPI.Frontend` project is a Blazor Server shell modeled after CSRankings. It shows the sticky filter bar, ranking table scaffold, and surfaces live PostgreSQL metadata through a `/api/db-size` endpoint that reads directly from the database.

Local development:

```bash
dotnet watch run --project frontend/BestPI.Frontend/BestPI.Frontend.csproj
```

Set a connection string via `ConnectionStrings__Postgres` in `appsettings.Development.json` or an environment variable (`ConnectionStrings__Postgres="Host=localhost;Port=5432;Database=clinicaltrials;Username=postgres;Password=postgres"`).

To preview the same artifact we deploy to DigitalOcean:

```bash
POSTGRES_CONNECTION_STRING="Host=host.docker.internal;Port=5432;Database=clinicaltrials;Username=postgres;Password=postgres" \
  docker-compose up --build frontend
```

The compose file maps container port 8080 to host port 80 so you can load `http://localhost/` and hit `http://localhost/api/db-size` without extra tooling.

### Resuming & Monitoring

- View recent ingest runs (status, processed count, notes):
  ```bash
  python -m scrapers.clinicaltrials.runner --env-file .env status --limit 10
  ```
- Resume the latest incomplete run or a specific run ID:
  ```bash
  python -m scrapers.clinicaltrials.runner --env-file .env full-sync --resume-latest
  python -m scrapers.clinicaltrials.runner --env-file .env full-sync --resume-run <run_uuid>
  ```
- To run unattended, use your preferred supervisor or a simple `nohup` invocation:
  ```bash
  nohup python -m scrapers.clinicaltrials.runner --env-file .env full-sync --resume-latest > scraper.log 2>&1 &
  ```
  The process can be stopped with `kill <pid>`; rerun with `--resume-latest` to continue from the saved checkpoint.

## Continuous Integration

GitHub Actions (`.github/workflows/tests.yml`) automatically installs dependencies and runs `pytest` on every push and pull request targeting `main`, ensuring the scraper stays green before merges.

## Investigator Topic Aggregation

Use the aggregation job to summarize condition/intervention experience per investigator (keyed by `investigators.id`).

```bash
python -m aggregations.investigator_topics --env-file .env aggregate          # all investigators
python -m aggregations.investigator_topics --env-file .env aggregate --limit 10  # pilot subset
python -m aggregations.investigator_topics --env-file .env count               # summary stats
python -m aggregations.investigator_topics --env-file .env recommend condition "Heart Failure" --limit 5
```

JSON layout example for a single investigator:

```json
{
  "condition_counts": {
    "Heart Failure": 12,
    "Cardiomyopathy": 5
  },
  "intervention_counts": {
    "DRUG": {
      "Sacubitril/Valsartan": 3
    },
    "DEVICE": {
      "Left Ventricular Assist Device": 1
    }
  }
}
```

A 10-investigator pilot completed in ~0.01 s on a dev laptop, implying a full refresh for ~75k investigators should finish in roughly 1–2 minutes. Use the `recommend` command to score PIs for any condition/intervention using phase- and recency-weighted heuristics (exponential decay toward the current date).

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
