#!/usr/bin/env bash

if (return 0 2>/dev/null); then
  echo "Use './update-data.sh', not 'source update-data.sh'." >&2
  return 1
fi

set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"

exec "$script_dir/backend/run_main.sh" "$@"
