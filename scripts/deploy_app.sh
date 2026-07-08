#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=${REPO_DIR:-/opt/bestpi/BestPIClinicalTrialSelector}
BRANCH=${1:-main}
GHCR_USERNAME=${GHCR_USERNAME:-rakirs2}

log() {
  echo "[deploy] $*"
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

if [[ -n "${GHCR_TOKEN:-}" ]]; then
  log "Logging into ghcr.io as ${GHCR_USERNAME}"
  echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin >/dev/null
fi

if [[ ! -d "${REPO_DIR}/.git" ]]; then
  echo "[deploy] Expected git repository at ${REPO_DIR} but .git was not found" >&2
  exit 1
fi

cd "${REPO_DIR}"

log "Syncing branch ${BRANCH}"
git fetch origin
git checkout "${BRANCH}"
git reset --hard "origin/${BRANCH}"

log "Updating frontend service"
run_compose pull frontend || true
run_compose up -d --remove-orphans frontend
