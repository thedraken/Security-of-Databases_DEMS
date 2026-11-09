#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "setup schema"
.venv/bin/python scripts/setup_schema.py
echo "setup RBAC"
.venv/bin/python scripts/setup_rbac.py
