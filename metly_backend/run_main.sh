#!/usr/bin/env bash
set -euo pipefail

# run_main.sh - Ensures the repository .venv is used and runs main.py using Poetry
# Usage: ./run_main.sh [args...]

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv="$script_dir/.venv"
log_file="$script_dir/run_main.log"
echo "Starting script at $(date)" > "$log_file"
echo "Script directory: $script_dir" >> "$log_file"

echo "Checking for virtual environment at $venv" >> "$log_file"
if [ -f "$venv/bin/activate" ]; then
  echo "Virtual environment found. Using $venv/bin/python explicitly." >> "$log_file"
else
  echo "Error: Virtual environment not found at $venv" >&2
  echo "Error: Virtual environment not found at $venv" >> "$log_file"
  exit 1
fi

# Check if Poetry is installed in the virtual environment
if ! "$venv/bin/poetry" --version &>/dev/null; then
  echo "Error: Poetry is not installed in the virtual environment. Please install Poetry." >&2
  echo "Error: Poetry is not installed in the virtual environment." >> "$log_file"
  exit 1
fi

echo "Poetry is installed in the virtual environment." >> "$log_file"

# Run the main.py script using Poetry explicitly from the virtual environment
echo "Running main.py with Poetry..." >> "$log_file"
cd "$script_dir" && "$venv/bin/poetry" run python main.py "$@" 2>> "$log_file" || {
  echo "Error: main.py failed to execute. Check the log file for details." >&2
  echo "Error: main.py failed to execute." >> "$log_file"
}

echo "Script finished at $(date)" >> "$log_file"