# Local Development Guide

Use this guide to spin up the Best PI Clinical Trial Selector stack entirely on your laptop. The goal is a repeatable workflow for debugging the Blazor frontend and the Python ingestion jobs against a disposable Postgres instance. Our deployment philosophy is "if it deploys here, it deploys there"—local Docker builds are the same artifacts that GitHub Actions pushes to GHCR and the DigitalOcean droplets.

## Prerequisites

- macOS or Linux with Docker Desktop 4.30+ (Compose V2).
- Python 3.12 and the .NET SDK 10.x.
- `git`, `make`, and a shell with bash compatibility.

## 1. Bootstrap the repository

```bash
git clone https://github.com/<org>/BestPIClinicalTrialSelector.git
cd BestPIClinicalTrialSelector
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Update `.env` with any overrides (e.g., `POSTGRES_DSN`, `ConnectionStrings__Postgres`, chunk caps).

## 2. Start the local stack

```bash
docker compose -f docker-compose.local.yml up --build
```

This launches:

- `postgres` listening on `localhost:55432` with the `clinicaltrials` database.
- `frontend` (Blazor Server) listening on `http://localhost:8080/` and pre-wired to the Postgres container.

Use `docker compose -f docker-compose.local.yml down -v` to stop and delete volumes when you want a clean DB.

## 3. Run the scraper against the compose DB

With the stack up, point the scraper to the local DSN in `.env`:

```bash
python -m scrapers.clinicaltrials.runner --env-file .env full-sync --max-chunks 1
```

Adjust `MAX_CHUNKS` / `SCRAPER_ENV` to control workload.

## 4. Iterating on the frontend

For hot reload outside Docker:

```bash
dotnet watch run --project frontend/BestPI.Frontend/BestPI.Frontend.csproj \
  --launch-profile "https"
```

Make sure `ConnectionStrings__Postgres` is set (either via `.env`, `appsettings.Development.json`, or environment variables) so the site can reach your DB.

## 5. Inspecting the database

Use `psql` via Docker:

```bash
docker compose -f docker-compose.local.yml exec postgres psql -U postgres -d clinicaltrials
```

Or point GUI clients to `localhost:55432` with the default credentials (`postgres` / `postgres`).

## 6. Cleaning up

```bash
docker compose -f docker-compose.local.yml down -v
deactivate  # leave the virtualenv
```

You now have a reproducible loop: stand up the stack, run scrapers/tests, iterate on the Blazor UI, and tear everything down when finished.

## Parity checklist before opening a PR

1. Build the frontend image locally (`docker compose -f docker-compose.local.yml build frontend`).
2. Run `docker compose -f docker-compose.local.yml up` and verify the site loads plus scraper APIs respond.
3. Only after local success should you push and trigger the Deploy workflow—production uses the same GHCR image built locally/CI.
