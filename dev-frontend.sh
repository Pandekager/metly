#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/metly_frontend"
exec bun run dev --host 127.0.0.1 --port 3000
