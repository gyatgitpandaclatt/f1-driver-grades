# F1 2026 Driver Grades

Computes S/A/B/C/D letter grades for 2026 F1 drivers from live qualifying/race
results and standings, and displays them in a web UI with feature-importance
and predicted-vs-actual charts.

## Prerequisites

- **Python**: this machine only has Python reachable via the `py` launcher.
  Plain `python` resolves to a broken Windows Store stub — always use `py`.
- **Node.js**: not installed on this machine. Install the LTS build from
  https://nodejs.org before doing any frontend work, then verify with:
  ```
  node --version
  npm --version
  ```

## Backend

```
cd backend
py -m venv venv
venv\Scripts\activate
py -m pip install --upgrade pip
pip install -r requirements.txt
py -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Frontend

```
cd frontend
npm install
npm run dev
```

App: http://localhost:5173 (proxies `/api/*` to the backend on :8000 — see `vite.config.ts`)

## Running as a single process (production / Replit)

The backend can serve the built frontend directly, so the whole app is one
process on one port — no separate frontend server needed:

```
cd frontend && npm install && npm run build && cd ..
cd backend && py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or just run `bash start.sh` from the project root, which does both steps.
This is what Replit runs (see `.replit`) — import this repo into Replit via
"Import from GitHub" and it should build and start automatically. If the
Nix channel in `.replit`/`replit.nix` is stale by the time you read this,
Replit will prompt you to fix it, or you can just delete both files and let
Replit auto-detect Python + Node.js instead.

## Deploying to Render

The app is set up to deploy as a single Docker web service via `render.yaml`
(a Render "Blueprint") — Docker is used because the image needs both Node
(to build the frontend) and Python (to run the backend); Render's native
Python runtime doesn't include Node. The `Dockerfile` does the same two
steps as `start.sh`: build `frontend/dist`, then run uvicorn.

1. Push this repo to GitHub (if not already).
2. In the Render dashboard: **New > Blueprint**, point it at the repo.
   Render reads `render.yaml` and creates the web service automatically.
3. Set the `ANTHROPIC_API_KEY` env var on the service (Render dashboard >
   service > Environment) — it's marked `sync: false` in `render.yaml` so
   it isn't committed to the repo; you enter the real value in the
   dashboard, same as `backend/.env` does locally.
4. Render builds the Docker image and starts the service; `/api/health` is
   used as the health check path.

No frontend code changes are needed for this move: the frontend only ever
calls relative paths like `/api/driver-grades` (see `frontend/src/api/client.ts`),
so it works unmodified on whatever host/domain serves it, same as it does
on Replit.

To test the exact production image locally before deploying, with Docker
installed:

```
docker build -t f1-driver-grades .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-... f1-driver-grades
```

## Notes

- `backend/app/config.py` holds season-specific settings (season year, rookie
  driver codes, constructor tier map) — update these each new season.
- The backend caches computed results in memory (~20 min TTL) to avoid
  hammering the upstream API on every page load. Use the Refresh button in the
  UI (or `POST /api/refresh`) to force a recompute.
- The Race Summary page (`/race-summary`, backed by `backend/app/race_summary/`)
  requires an `ANTHROPIC_API_KEY` (used to write the race narrative) — copy
  `backend/.env.example` to `backend/.env` and fill it in (loaded
  automatically on startup), or set it as a real environment variable. Race
  data comes from the same Jolpica/Ergast API as the rest of the app (final
  classification, lap-by-lap positions, pit stops) — there's deliberately no
  tire compound, weather, or safety-car data, since Ergast doesn't have it;
  the narrative is written from what's available and instructed not to guess
  at the rest.
