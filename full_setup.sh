#!/usr/bin/env bash
#Setting options to stop script if failure
#-e Stop the script if a command fails
#-u treat an unset variable as an error
#-o pipefail fail the script if anything in the pipeline fails
set -euo pipefail
#Moves into the folder where the script itself is saved
cd "$(dirname "$0")"

echo "setup environment"
./scripts/setup_environment.sh
echo "create docker"
./scripts/create_docker.sh "$@"
echo "setup DB"
./scripts/setup_db.sh
curl http://localhost:8080/versions
echo "done. Running at: https://localhost:8443"
