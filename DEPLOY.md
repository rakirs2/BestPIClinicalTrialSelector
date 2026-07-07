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
  3. `deploy-app` – SSHes into `bestpi-mvp`, writes secrets to a temporary `.env.runtime`, runs `docker compose up -d`, and removes the file.
  4. `deploy-db` – fires only when schema files change; currently reminds maintainers to run migrations manually.

### Required repository secrets

| Secret              | Description                                                                           |
|---------------------|---------------------------------------------------------------------------------------|
| `APP_HOST`          | Public IP or hostname of the app droplet (`104.236.126.216`).                          |
| `APP_USER`          | SSH username (typically `root`).                                                      |
| `APP_SSH_KEY`       | Private key (OpenSSH/PEM) with access to the droplet.                                 |
| `APP_SSH_KEY_B64`   | _(Optional)_ Base64-encoded private key if storing the raw PEM is inconvenient.       |
| `DEPLOY_GHCR_PAT`   | PAT with `read:packages` scope so the droplet can `docker login` to GHCR.             |
| `DEPLOY_PG_CONN`    | Value for `ConnectionStrings__Postgres` (used by ASP.NET).                            |
| `DEPLOY_PG_DSN`     | Value for `POSTGRES_CONNECTION_STRING` (used by Python scrapers/CLIs).                |

`GITHUB_TOKEN` handles `docker push`. The PAT is only needed during `docker pull` on the droplet.

### Database migrations

`deploy-db` simply produces a heads-up today. When it runs, connect to `bestpi-db`, snapshot, apply migrations manually (e.g., via `psql`), and update this document once automation lands.

### Rotating the deploy SSH key

1. Generate a new keypair: `ssh-keygen -t ed25519 -f ~/.ssh/bestpi_app -C "ci-deploy"` (no passphrase).
2. Append the public key to `/root/.ssh/authorized_keys` on `bestpi-mvp`.
3. Store the private key contents in the `APP_SSH_KEY` secret (or base64-encode it and store it in `APP_SSH_KEY_B64`).

## Manual deploys

Manual SSH deploys are intentionally disabled. If the GitHub workflow fails, fix the pipeline rather than deploying by hand.
