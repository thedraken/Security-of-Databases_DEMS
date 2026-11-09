#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Use sudo only if the current user cannot talk to the Docker daemon directly.
if docker info >/dev/null 2>&1; then DOCKER=(docker); else DOCKER=(sudo docker); fi

echo "remove old container, if it exists"
"${DOCKER[@]}" compose -p dems_hugegraph -f hugegraph/docker/docker-compose.yml down 2>/dev/null || true

echo "create containers (project dems_hugegraph)"
"${DOCKER[@]}" compose \
  --env-file .env \
  -p dems_hugegraph \
  -f hugegraph/docker/docker-compose.yml \
  up -d --wait
