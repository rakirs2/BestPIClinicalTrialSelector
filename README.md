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
   - Python 3.12+ (system interpreter on macOS works).
   - Local PostgreSQL instance (Docker or native). Create an empty database, e.g. `clinicaltrials`. You can also rely on `docker-compose.local.yml` (see below) to launch Postgres via Docker.
3. **Configure environment**
   - Copy `.env.example` to `.env` and update `POSTGRES_DSN` plus optional tuning values.
   - Populate `ConnectionStrings__Postgres` so the Blazor frontend reuses the same database as the scraper.
   - Non-production runs (`SCRAPER_ENV` set to `development`, `staging`, `test`, `ci`, etc.) automatically stop after five API chunks. Leave `SCRAPER_ENV=production` (or override with `MAX_CHUNKS`/`--max-chunks`) for uncapped production syncs.
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
   The command streams every study through the v2 ClinicalTrials.gov API, stores the raw JSON payload plus tabularized data, and halts automatically if the database exceeds the configured size limit (default 10 GB). Progress is tracked in the `ingest_runs` table and non-production runs stop after the 5th chunk unless you override the cap.
5. **Run tests**
   ```bash
   .venv/bin/pytest
   dotnet test frontend/BestPI.Frontend.Tests/BestPI.Frontend.Tests.csproj
   ```
   Tests currently cover the normalization pipeline plus frontend services; expand coverage as parsers and UI evolve.

## Frontend Preview (Blazor Server MVP)

The `frontend/BestPI.Frontend` project is a Blazor Server shell modeled after CSRankings. It shows the sticky filter bar, ranking table scaffold, and surfaces live PostgreSQL metadata through a `/api/db-size` endpoint that reads directly from the database.

- The layout ships with a system-aware light/dark theme and a manual toggle (System / Light / Dark) so operators can pick a comfortable palette.
- Status dashboards (Scraper Status, DB Health) use a simplified, high-contrast color scheme for readability.

Local development:

```bash
dotnet watch run --project frontend/BestPI.Frontend/BestPI.Frontend.csproj
```

Set a connection string via `ConnectionStrings__Postgres` in `appsettings.Development.json` or an environment variable (`ConnectionStrings__Postgres="Host=localhost;Port=5432;Database=clinicaltrials;Username=postgres;Password=postgres"`).

### Local Docker stack

Spin up Postgres plus the Blazor app for local parity:

```bash
docker compose -f docker-compose.local.yml up --build
```

Postgres is exposed on `localhost:55432` and the frontend on `http://localhost:8080/`. Tear everything down with `docker compose -f docker-compose.local.yml down -v`.

See `LOCAL_DEV.md` for a full virtualenv + compose workflow.

### Previewing the production artifact

```bash
POSTGRES_CONNECTION_STRING="Host=host.docker.internal;Port=5432;Database=clinicaltrials;Username=postgres;Password=postgres" \
  docker-compose up --build frontend
```

The production compose file maps container port 8080 to host port 80 so you can load `http://localhost/` and hit `http://localhost/api/db-size` without extra tooling.

Exposed operational endpoints (also visualized via `/db-health` and `/scraper-status` pages):

- `GET /api/db-health` – returns database status, uptime, connection utilization, and size.
- `GET /api/scraper-status?limit=20` – returns the latest ingest run, a recent history table driven by `ingest_runs`, and the 50 most recent log entries captured in `scraper_run_logs` so the UI can stream live telemetry.

## Deployment

- Production uses two DigitalOcean droplets (`bestpi-mvp` for the app, `bestpi-db` for PostgreSQL) connected via a private VPC link.
- Secrets for Docker Compose are written to `/opt/bestpi/.env.deploy` during each GitHub Actions deploy (from the `DEPLOY_PG_CONN` and `DEPLOY_PG_DSN` secrets). The workflow symlinks the file into the repo directory as `.env.deploy` before running Docker Compose, so no manual editing on the droplet is required.
- GitHub Actions (`.github/workflows/deploy.yml`) builds/pushes the frontend image to GHCR and redeploys the app droplet after every push to `main`. Schema-aware DB deploys are gated separately.
- The Deploy workflow (specifically the `deploy-app` job) is a required status check—PRs cannot merge until a successful deploy run exists for the exact commit.
- Deploys now include automated health checks: the droplet polls `http://localhost/api/db-size`, and the workflow curls `http://<APP_HOST>/api/db-size` before reporting success.

See `DEPLOY.md` for the full runbook, required secrets, and manual fallback commands.

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
- Add blue/green (or rolling) deployment strategy for the Blazor frontend to avoid downtime.
- Reconsider Dockerization + deployment parity (two DigitalOcean droplets: Postgres + app/jobs) so "if it deploys locally, it deploys remotely" becomes enforceable ([Issue #34](https://github.com/rakirs2/BestPIClinicalTrialSelector/issues/34)).
- Evaluate rewriting all scrapers in C# to maintain a single stack with shared libraries/models ([Issue #35](https://github.com/rakirs2/BestPIClinicalTrialSelector/issues/35)).
- Add PubMed and CMS scrapers to enrich investigator profiles with publication history and claims/coverage context ([Issue #36](https://github.com/rakirs2/BestPIClinicalTrialSelector/issues/36), [Issue #37](https://github.com/rakirs2/BestPIClinicalTrialSelector/issues/37)).
- Build a keyword-driven search page for protocol/condition/intervention filtering ([Issue #38](https://github.com/rakirs2/BestPIClinicalTrialSelector/issues/38)).
- Build a principal investigator lookup page with detailed history, site performance, and cross-dataset signals ([Issue #39](https://github.com/rakirs2/BestPIClinicalTrialSelector/issues/39)).

## License

Add licensing information here once the legal framework is decided.
