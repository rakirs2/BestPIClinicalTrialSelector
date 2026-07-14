#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=${REPO_DIR:-/opt/bestpi/BestPIClinicalTrialSelector}
BRANCH=${1:-main}
GHCR_USERNAME=${GHCR_USERNAME:-rakirs2}

log() {
  echo "[deploy] $*"
}

free_port_80() {
  local ids=()
  while IFS= read -r cid; do
    [[ -n "${cid}" ]] && ids+=("${cid}")
  done < <(docker ps --format '{{.ID}} {{.Ports}}' | awk '/:80->/ {print $1}')

  if [[ ${#ids[@]} -gt 0 ]]; then
    log "Stopping containers using host port 80: ${ids[*]}"
    docker stop "${ids[@]}" >/dev/null
    docker rm "${ids[@]}" >/dev/null || true
  else
    log "No docker containers currently publishing host port 80"
  fi

  local pids=()
  while IFS= read -r pid; do
    [[ -n "${pid}" ]] && pids+=("${pid}")
  done < <(lsof -ti tcp:80 2>/dev/null || true)

  if [[ ${#pids[@]} -gt 0 ]]; then
    log "Killing host processes listening on port 80: ${pids[*]}"
    kill "${pids[@]}" >/dev/null || true
  fi
}

ensure_env_file() {
  local env_target="${REPO_DIR}/.env.deploy"
  local env_source="${DEPLOY_ENV_FILE:-$(dirname "${REPO_DIR}")/.env.deploy}"
  if [[ ! -f "${env_source}" ]]; then
    echo "[deploy] Missing env file at ${env_source}. Create it with deployment secrets (see README/DEPLOY.md)." >&2
    exit 1
  fi

  ln -sf "${env_source}" "${env_target}"
  log "Linked ${env_target} -> ${env_source}"
}

run_compose() {
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  elif docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    echo "docker-compose is required but not installed" >&2
    exit 1
  fi
}

if ! command -v curl >/dev/null 2>&1; then
  echo "[deploy] curl is required for health checks" >&2
  exit 1
fi

wait_for_http() {
  local url="$1"
  local attempts=${2:-12}
  local delay=${3:-5}

  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS --max-time 5 "${url}" >/dev/null; then
      log "Health check succeeded for ${url} (attempt ${i})"
      return 0
    fi
    log "Health check failed for ${url} (attempt ${i}/${attempts}); retrying in ${delay}s"
    sleep "${delay}"
  done

  log "Health check failed for ${url} after ${attempts} attempts"
  return 1
}

if [[ -n "${GHCR_TOKEN:-}" ]]; then
  log "Logging into ghcr.io as ${GHCR_USERNAME}"
  echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin >/dev/null
fi

if [[ ! -d "${REPO_DIR}/.git" ]]; then
  echo "[deploy] Expected git repository at ${REPO_DIR} but .git was not found" >&2
  exit 1
fi

cd "${REPO_DIR}"

ensure_env_file

if [[ -z "${FRONTEND_IMAGE:-}" ]]; then
  echo "[deploy] FRONTEND_IMAGE is required (pass via environment before running deploy_app.sh)" >&2
  exit 1
fi

export FRONTEND_IMAGE

log "Syncing branch ${BRANCH}"
git fetch origin
git checkout "${BRANCH}"
git reset --hard "origin/${BRANCH}"

log "Deploying image ${FRONTEND_IMAGE}"
log "Updating frontend service"
free_port_80
run_compose down --remove-orphans || true
run_compose pull frontend || true
run_compose up -d --remove-orphans frontend
run_compose ps frontend

wait_for_http "http://localhost/api/db-size" 12 5
