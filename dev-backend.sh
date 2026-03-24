#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/metly_backend"

if [ -x ".venv/bin/poetry" ]; then
  exec .venv/bin/poetry run uvicorn src.endpoints.getData:app --reload --host 127.0.0.1 --port 8000
fi

exec poetry run uvicorn src.endpoints.getData:app --reload --host 127.0.0.1 --port 8000
