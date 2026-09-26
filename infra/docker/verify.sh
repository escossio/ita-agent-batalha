#!/usr/bin/env bash
set -euo pipefail
[[ "${ITA_CI_WORKER:-}" == 1 ]] || { echo 'Container certification requires a worker'; exit 64; }
cd "$(dirname "$0")/../.."
export COMPOSE_PROJECT_NAME="ita-ci-$(git rev-parse --short=12 HEAD)-${RANDOM}"
export ITA_PORT=0
cleanup() { docker compose down --volumes --remove-orphans >/dev/null 2>&1; }
trap cleanup EXIT
docker compose config --quiet
docker compose build --quiet
docker compose up -d --wait --wait-timeout 180
python3 infra/docker/vertical_slice.py
python3 infra/docker/smoke.py
docker compose down --volumes --remove-orphans
trap - EXIT
echo "ITA_CONTAINER_CERTIFICATION=PASS SHA=$(git rev-parse HEAD)"
