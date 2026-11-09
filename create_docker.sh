#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

RESET_VALUE=false
if [ "${1:-}" = "--reset" ]; then
    RESET_VALUE=true
fi

echo "reset status set to $RESET_VALUE"

# Use sudo only if the current user cannot talk to the Docker daemon directly.
if docker info >/dev/null 2>&1; then DOCKER=(docker); else DOCKER=(sudo docker); fi
COMPOSE=("${DOCKER[@]}" compose -p dems_hugegraph -f hugegraph/docker/docker-compose.yml)

if [ "$RESET_VALUE" = true ]; then
    read -r -p "This deletes ALL graph data (volumes). Continue? [y/N] " answer
    if [ "$answer" != "y" ]; then
        echo "aborted"
        exit 1
    fi
    echo "remove old containers and their data"
    "${COMPOSE[@]}" down -v || true
else
    echo "remove old containers (data is kept)"
    "${COMPOSE[@]}" down || true
fi

echo "create containers (project dems_hugegraph)"
"${COMPOSE[@]}" --env-file .env up -d --wait
