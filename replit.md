# F1 2026 Driver Grades

Computes S/A/B/C/D letter grades for 2026 F1 drivers from live qualifying/race results and standings, displaying them in a data-rich web UI with feature-importance and predicted-vs-actual charts.

## Stack

- **Backend**: Python 3.12 + FastAPI + uvicorn, served on port 5000
- **Frontend**: React 18 + TypeScript + Vite + Recharts (built to `frontend/dist/`, served by FastAPI)
- **Single process**: backend serves both the API (`/api/*`) and the built frontend static files

## How to Run

The workflow `Start application` runs `PORT=5000 bash start.sh`, which:
1. Installs frontend deps and builds (`npm install && npm run build` in `frontend/`)
2. Starts uvicorn serving the app on port 5000

Python packages are managed by Replit (no virtualenv needed).

## Pages

| Route | Description |
|---|---|
| `/` | Driver grades table + model charts |
| `/qualifying-h2h` | Head-to-head qualifying comparisons |
| `/overperformance` | Drivers exceeding model expectations |
| `/grid-improvement` | Progress across the grid |
| `/race-summary` | AI-written narrative recap of the most recent completed race, with position/tire/speed charts — **hidden on Replit**, see Notes |
| `/methodology` | How grading works |

## Key Files

- `backend/app/main.py` — FastAPI app, routes, static file serving
- `backend/app/config.py` — Season settings (year, rookie codes, constructor tier map)
- `frontend/src/theme/theme.ts` — Recharts color constants (keep in sync with `index.css`)
- `frontend/src/index.css` — Global styles and design tokens
- `start.sh` — Single entrypoint for Replit

## Notes

- Backend caches results ~20 min in memory; use the Refresh button or `POST /api/refresh` to force recompute
- To update for a new season: edit `backend/app/config.py`
- The Race Summary page (`backend/app/race_summary/`) pulls lap/telemetry data via FastF1 and
  writes the narrative with Claude — requires an `ANTHROPIC_API_KEY` in the environment. Its
  cache is ~6h (a completed race's data doesn't change) and isn't warmed at startup, since a
  cold FastF1 telemetry load can take over a minute.
- **Race Summary does not work on Replit** (workspace or deployment): FastF1's data source
  (`livetiming.formula1.com`) rejects requests from Replit's IP ranges with a `403` (CloudFront
  `Request blocked`) as an anti-scraping measure — confirmed via direct `curl` from both the
  Replit workspace and a published deployment. `config.RACE_SUMMARY_AVAILABLE` detects Replit
  via the `REPL_ID` env var and the frontend hides the nav tab accordingly; the API also
  short-circuits with a clear message rather than attempting the doomed fetch. This is an
  external network block, not fixable in this codebase — the feature only works when run
  somewhere with a non-datacenter egress IP (e.g. locally).

## User Preferences

- UI should be visually exciting — dark F1-themed design with red accents, grid background, bold typography
