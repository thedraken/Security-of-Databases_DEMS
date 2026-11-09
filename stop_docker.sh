#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Use sudo only if the current user cannot talk to the Docker daemon directly.
if docker info >/dev/null 2>&1; then DOCKER=(docker); else DOCKER=(sudo docker); fi
COMPOSE=("${DOCKER[@]}" compose -p dems_hugegraph -f hugegraph/docker/docker-compose.yml)

echo "stop and remove containers (data is kept)"
"${COMPOSE[@]}" down
