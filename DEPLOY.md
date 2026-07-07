# Deployment Guide

This document explains how the production environment is wired together and how to operate it manually if GitHub Actions is unavailable.

## Infrastructure

| Role            | Droplet Name | Public IP      | Private IP  | Notes                               |
|-----------------|--------------|----------------|-------------|-------------------------------------|
| App + Workers   | `bestpi-mvp` | `104.236.126.216` | `10.108.0.2` | Hosts Blazor Server, scraper jobs, Docker Compose. |
| PostgreSQL only | `bestpi-db`  | `45.55.216.215`   | `10.108.0.3` | Runs PostgreSQL 16. Access is restricted to the VPC. |

The app droplet no longer runs PostgreSQL locally. All services connect to the DB droplet via the private network.

## Environment Files

The repo’s `.env` is for local development. The app droplet keeps deployment secrets in `/opt/bestpi/.env.deploy` (ignored by git/rsync). Minimal example:

```
POSTGRES_CONNECTION_STRING=Host=10.108.0.3;Port=5432;Database=clinicaltrials;Username=bestpi;Password=<password>;IncludeErrorDetail=true
FRONTEND_IMAGE=ghcr.io/rakirs2/bestpi-frontend:latest

# ASP.NET reads `ConnectionStrings:Postgres` directly, so include:
ConnectionStrings__Postgres=Host=10.108.0.3;Port=5432;Database=clinicaltrials;Username=bestpi;Password=<password>;IncludeErrorDetail=true
```

Update `/opt/bestpi/.env` for Python tooling:

```
POSTGRES_DSN=postgresql://bestpi:<password>@10.108.0.3:5432/clinicaltrials
CTGOV_BASE_URL=...
```

Remember to keep these files outside of git so rsync/Actions do not overwrite credentials.

## Manual Deploy (fallback)

SSH into `bestpi-mvp` and run:

```bash
cd /opt/bestpi
git fetch origin
git checkout main
git reset --hard origin/main
GHCR_TOKEN=<pat> GHCR_USERNAME=rakirs2 ./scripts/deploy_app.sh main
```

The script logs into GHCR (if `GHCR_TOKEN` is set), pulls the latest image, and restarts Docker Compose using `.env.deploy`.

## GitHub Actions Pipeline

- Workflow file: `.github/workflows/deploy.yml`
- Trigger: push to `main`
- Jobs:
  1. `test`: runs pytest + `dotnet build`.
  2. `build`: builds `ghcr.io/<owner>/bestpi-frontend` (tags `latest` and commit SHA).
  3. `deploy-app`: SSHes into `bestpi-mvp` and invokes `scripts/deploy_app.sh main` with GHCR credentials.
  4. `deploy-db`: only runs when schema files change; currently reminds maintainers to perform manual migrations.

### Required repository secrets

| Secret            | Description                                                      |
|-------------------|------------------------------------------------------------------|
| `APP_HOST`        | Public IP or hostname of the app droplet (`104.236.126.216`).     |
| `APP_USER`        | SSH username (typically `root`).                                 |
| `APP_SSH_KEY`     | Private key with access to the droplet (PEM format).             |
| `GHCR_PAT`        | Personal Access Token with `read:packages` to pull from GHCR.    |

The workflow uses the auto-generated `GITHUB_TOKEN` for pushing to GHCR; a PAT is only needed on the droplet for pulling during deploy.

### Database migrations

`deploy-db` currently serves as a notification hook. When the job runs, SSH into `bestpi-db`, take a snapshot, apply schema migrations manually (e.g., via `psql`), and update `RUNBOOK` once an automated process exists.
