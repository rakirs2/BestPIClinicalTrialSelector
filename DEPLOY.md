# Deployment Guide

Production consists of two DigitalOcean droplets plus a GitHub Actions workflow that is solely responsible for redeployments—there is no manual SSH deploy path.

## Infrastructure

| Role            | Droplet Name | Public IP        | Private IP  | Notes                                               |
|-----------------|--------------|------------------|-------------|-----------------------------------------------------|
| App + Workers   | `bestpi-mvp` | `104.236.126.216`| `10.108.0.2` | Hosts Blazor Server, scraper jobs, Docker Compose.   |
| PostgreSQL only | `bestpi-db`  | `45.55.216.215`  | `10.108.0.3` | Runs PostgreSQL 16 (VPC-only access from `bestpi-mvp`). |

The app droplet connects to Postgres via the VPC private address; the local Postgres service is disabled.

## Secrets & Pipeline

- Workflow file: `.github/workflows/deploy.yml`
- Trigger: any push to `main`.
- Jobs:
  1. `test` – runs pytest + `dotnet build`.
  2. `build` – builds `ghcr.io/<owner>/bestpi-frontend:{sha,latest}`.
  3. `deploy-app` – SSHes into `bestpi-mvp`, writes secrets to `.env.deploy`, exports `FRONTEND_IMAGE=ghcr.io/<owner>/bestpi-frontend:${GITHUB_SHA}`, and drives `scripts/deploy_app.sh` (which runs `docker compose pull/up`).
  4. `deploy-db` – fires only when schema files change; currently reminds maintainers to run migrations manually.

Before calling `scripts/deploy_app.sh`, the workflow clones (or reuses) the repository at `/opt/bestpi/BestPIClinicalTrialSelector` on the droplet. It renders `/opt/bestpi/.env.deploy` from the `DEPLOY_PG_CONN` and `DEPLOY_PG_DSN` GitHub secrets, then symlinks it into the repo as `.env.deploy` so Docker Compose always has the required secrets without duplicating sensitive files. Right before invoking the script, the workflow exports `FRONTEND_IMAGE=ghcr.io/<owner>/bestpi-frontend:${GITHUB_SHA}` so the compose file pulls the exact image built earlier. The deploy script assumes both the repo checkout and env file are present (and will refuse to continue if `FRONTEND_IMAGE` is missing).

### Required repository secrets

| Secret              | Description                                                                           |
|---------------------|---------------------------------------------------------------------------------------|
| `APP_HOST`          | Public IP or hostname of the app droplet (`104.236.126.216`).                          |
| `APP_USER`          | SSH username (typically `root`).                                                      |
| `APP_SSH_KEY`       | Private key (OpenSSH/PEM) with access to the droplet. Include the `-----BEGIN/END OPENSSH PRIVATE KEY-----` markers.  |
| `DEPLOY_GHCR_PAT`   | PAT with `read:packages` scope so the droplet can `docker login` to GHCR.             |
| `DEPLOY_PG_CONN`    | Value for `ConnectionStrings__Postgres` (used by ASP.NET).                            |
| `DEPLOY_PG_DSN`     | Value for `POSTGRES_CONNECTION_STRING` (used by Python scrapers/CLIs).                |

`GITHUB_TOKEN` handles `docker push`. The PAT is only needed during `docker pull` on the droplet.

Set `DEPLOY_ENV_FILE` when calling `scripts/deploy_app.sh` if your secrets file must live somewhere other than `/opt/bestpi/.env.deploy`; otherwise the workflow-managed default is used.

### Branch protection requirement

The Deploy workflow (specifically the `deploy-app` job) is marked as a required status check for `main`. Trigger the workflow—either by pushing to the PR branch or running it manually via **Actions → Deploy → Run workflow**—and wait for the job to succeed before merging. Update repository settings if needed: **Settings → Branches → main → Require status checks → Deploy**.

### Reproducible environments mantra

- Production relies on exactly two droplets: `bestpi-mvp` (frontend + background jobs) and `bestpi-db` (Postgres). No other hosts should run first-party code.
- Every container pulled in production must already be built/tested locally (or in CI) via `docker compose -f docker-compose.local.yml build`. Avoid ad-hoc SSH builds.
- Before running the Deploy workflow, ensure the local compose stack (`docker-compose.local.yml`) works end-to-end; this keeps the "if it deploys here, it deploys there" promise credible.

### Database migrations

`deploy-db` simply produces a heads-up today. When it runs, connect to `bestpi-db`, snapshot, apply migrations manually (e.g., via `psql`), and update this document once automation lands.

### Rotating the deploy SSH key

1. Generate a new keypair: `ssh-keygen -t ed25519 -f ~/.ssh/bestpi_app -C "ci-deploy"` (no passphrase).
2. Append the public key to `/root/.ssh/authorized_keys` on `bestpi-mvp`.
3. Store the private key contents in the `APP_SSH_KEY` secret. Keep the `-----BEGIN/END OPENSSH PRIVATE KEY-----` markers; comments are optional.

### Smoke-testing the deploy pipeline

To verify credentials without touching production:

1. Navigate to **Actions → Deploy → Run workflow**.
2. Choose `deploy_target = smoke`.
3. The workflow builds the image and opens an SSH session, then stops after confirming docker access.

Use `deploy_target = production` (or push to `main`) for the actual rollout.

## Manual deploys

Manual SSH deploys are intentionally disabled. If the GitHub workflow fails, fix the pipeline rather than deploying by hand.
