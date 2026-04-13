# AGENTS.md

## Project Overview

This workspace combines two previously separate repositories into one local project:

- `frontend`: Nuxt 4 application managed with Bun
- `backend`: FastAPI application managed with Poetry

The frontend talks to the backend through Nuxt server routes. By default, the frontend expects the backend API at `http://127.0.0.1:8000/api`.

## Workspace Structure

```text
metly/
├── AGENTS.md
├── dev-backend.sh
├── dev-frontend.sh
├── backend/
└── frontend/
```

## Local Development

### Frontend

```bash
cd frontend
bun install
bun run dev --host 127.0.0.1 --port 3000
```

### Backend

```bash
cd backend
uv sync
uv run uvicorn src.endpoints.getData:app --reload --host 127.0.0.1 --port 8000
```

### Root Helpers

```bash
./dev-frontend.sh
./dev-backend.sh
```

## Environment Notes

- Frontend runtime config uses `API_BASE` and falls back to `http://127.0.0.1:8000/api`.
- Backend reads configuration from `backend/.env`.
- Keep secrets in local `.env` files and out of repository documentation.

## Agent Guidance

- Treat `frontend` as a Bun-managed Nuxt app.
- Treat `backend` as a Poetry-managed Python app.
- Prefer changing project-level workflows in the workspace root when coordinating both apps.
- Do not commit or expose secrets from existing `.env` files.
- When validating integration, verify both `http://127.0.0.1:3000` and `http://127.0.0.1:8000/docs`.
