# Metly Backend — Quick Run Instructions

This repository contains the Metly Backend project. The small helper script `run_main.sh` in the project root activates the repository virtual environment (if present at `./.venv`) and runs `main.py`, ensuring you see all print output on your terminal.

## Quick start (recommended)

From the repository root:

```bash
# Make sure you have a virtualenv (optional but recommended)
python3 -m venv .venv

# Activate and install dependencies if you have a requirements file
. .venv/bin/activate
pip install -r requirements.txt  # if you maintain a requirements.txt

# Run the project via the helper script
./run_main.sh
```

The script will:

- Source `./.venv/bin/activate` if it exists, and use the venv's Python.
- Fall back to system `python3` or `python` if no `.venv` is found.
- Forward any arguments to `main.py`.

## Examples

Run with arguments passed to `main.py`:

```bash
./run_main.sh arg1 arg2
```

Run in background (simple):

```bash
./run_main.sh &
```

Capture logs to a file:

```bash
./run_main.sh > metly.log 2>&1 &
```

## Notes & tips

- The script expects `main.py` at the repository root (same directory as this README and `run_main.sh`).
- If you prefer `poetry`, `pipenv`, or other tools, you can edit `run_main.sh` to activate them instead.
- For production / long-running processes consider a proper supervisor (systemd, supervisord, or a container).

## Troubleshooting

- If you see "No python executable found on PATH", install Python 3 or ensure it is available as `python3`/`python` in your PATH.
- If dependencies are missing, create and activate the `.venv` and install required packages. If you don't have `requirements.txt`, check project documentation or the source for required packages.

---

Created by the project helper script generator. If you'd like a systemd unit or a Makefile target for running this service, I can add one.
