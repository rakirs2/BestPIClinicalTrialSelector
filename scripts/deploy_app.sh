#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=${REPO_DIR:-/opt/bestpi}
BRANCH=${1:-main}
GHCR_USERNAME=${GHCR_USERNAME:-rakirs2}

if [[ -n "${GHCR_TOKEN:-}" ]]; then
  echo "Logging into ghcr.io as ${GHCR_USERNAME}"
  echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin >/dev/null
fi

cd "${REPO_DIR}"

git fetch origin
git checkout "${BRANCH}"
git reset --hard "origin/${BRANCH}"

docker-compose pull frontend || true
docker-compose up -d --remove-orphans frontend
