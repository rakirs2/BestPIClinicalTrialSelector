#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=${REPO_DIR:-/opt/bestpi}
BRANCH=${1:-main}
GHCR_USERNAME=${GHCR_USERNAME:-rakirs2}

log() {
  echo "[deploy] $*"
}

ensure_repo_dir() {
  local repo_name=""
  if [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
    repo_name="${GITHUB_REPOSITORY##*/}"
  fi

  if [[ -d "${REPO_DIR}/.git" ]]; then
    log "Using repository at ${REPO_DIR}"
    return
  fi

  local -a candidates=()
  candidates+=("${REPO_DIR}")
  if [[ -n "${repo_name}" ]]; then
    candidates+=("${REPO_DIR}/${repo_name}")
  fi
  candidates+=("${REPO_DIR}/BestPIClinicalTrialSelector")

  for candidate in "${candidates[@]}"; do
    if [[ -d "${candidate}/.git" ]]; then
      REPO_DIR="${candidate}"
      log "Found repository at ${REPO_DIR}"
      return
    fi
  done

  if [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
    local target="${REPO_DIR}"
    if [[ -d "${REPO_DIR}" && -n "${repo_name}" && -n "$(ls -A "${REPO_DIR}" 2>/dev/null)" ]]; then
      target="${REPO_DIR}/${repo_name}"
    fi
    log "Repository not found locally; cloning ${GITHUB_REPOSITORY} into ${target}"
    mkdir -p "${target}"
    if [[ ! -d "${target}/.git" ]]; then
      git clone "https://github.com/${GITHUB_REPOSITORY}.git" "${target}"
    fi
    REPO_DIR="${target}"
    return
  fi

  echo "${REPO_DIR} is not a git repository and GITHUB_REPOSITORY is unset" >&2
  exit 1
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

ensure_repo_dir

cd "${REPO_DIR}"

log "Syncing branch ${BRANCH}"
git fetch origin
git checkout "${BRANCH}"
git reset --hard "origin/${BRANCH}"

log "Updating frontend service"
run_compose pull frontend || true
run_compose up -d --remove-orphans frontend
