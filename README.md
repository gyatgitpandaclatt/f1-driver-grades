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

## Notes

- `backend/app/config.py` holds season-specific settings (season year, rookie
  driver codes, constructor tier map) — update these each new season.
- The backend caches computed results in memory (~20 min TTL) to avoid
  hammering the upstream API on every page load. Use the Refresh button in the
  UI (or `POST /api/refresh`) to force a recompute.
- The Race Summary page (`/race-summary`, backed by `backend/app/race_summary/`)
  requires an `ANTHROPIC_API_KEY` (used to write the race narrative) — copy
  `backend/.env.example` to `backend/.env` and fill it in (loaded
  automatically on startup), or set it as a real environment variable. It
  also downloads lap/telemetry data via FastF1 on first request, cached to
  `backend/fastf1_cache/`; the first load for a given race can take a minute
  or two.
