#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

#Check for python3-venv being installed
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "python3-venv is missing. On Debian/Ubuntu: sudo apt install python3-venv" >&2
    exit 1
fi

#Create venv if needed
if [ ! -x .venv/bin/python ]; then
    echo "create virtual environment in .venv"
    python3 -m venv .venv
fi

echo "install requirements"
.venv/bin/pip install --upgrade pip >/dev/null
.venv/bin/pip install -r scripts/requirements.txt

if [ -f .env ]; then
    echo ".env already exists; keeping it (delete it to regenerate)"
else
    echo "create .env"
    .venv/bin/python scripts/create_env.py
fi
