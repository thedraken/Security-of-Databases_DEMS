#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

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

echo "ensure PII encryption key exists"
.venv/bin/python scripts/pii.py init-key

echo "Create self signed cert, for https"
CERT_DIR="hugegraph/docker/conf/caddy/certs"
CERT_FILE="$CERT_DIR/localhost.pem"
KEY_FILE="$CERT_DIR/localhost-key.pem"
if ! command -v mkcert >/dev/null 2>&1; then
    echo "`mkcert` is missing. On Debian/Ubuntu: sudo apt install mkcert libnss3-tools" >&2
    exit 1
fi

#Installs mkcert's local CA in the trust stores
echo "Ensure local certificate authority is trusted"
mkcert -install

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "TLS certificate already exists; keeping it (delete $CERT_DIR to regenerate)"
else
    echo "Create TLS certificate for localhost"
    mkdir -p "$CERT_DIR"
    mkcert -cert-file "$CERT_FILE" -key-file "$KEY_FILE" localhost 127.0.0.1 ::1
fi
