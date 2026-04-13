#!/usr/bin/env bash

if (return 0 2>/dev/null); then
  echo "Use './run_main.sh', not 'source run_main.sh'." >&2
  return 1
fi

set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
log_file="$script_dir/run_main.log"

echo "Starting script at $(date)" > "$log_file"
echo "Script directory: $script_dir" >> "$log_file"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

echo "Running main.py with uv..." >> "$log_file"
cd "$script_dir" && uv run python main.py "$@" 2>> "$log_file" || {
  echo "Error: main.py failed to execute. Check the log file for details." >&2
  echo "Error: main.py failed to execute." >> "$log_file"
}

echo "Script finished at $(date)" >> "$log_file"