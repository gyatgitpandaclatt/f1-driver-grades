# F1 Driver Grades

Computes S/A/B/C/D letter grades for F1 drivers (the current season and the previous five) from live qualifying/race results and standings, displaying them in a data-rich web UI with feature-importance and predicted-vs-actual charts.

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
| `/race-summary` | AI-written narrative recap of the most recent completed race, with a position chart (current season only) |
| `/season-summary` | AI-written review of a finished season, with a championship-position chart, quarterly analysis and crucial moments (previous seasons only) |
| `/methodology` | How grading works |

## Key Files

- `backend/app/main.py` — FastAPI app, routes, static file serving
- `backend/app/config.py` — Season window and the thresholds for live rookies, constructor tiers and season-summary moments
- `frontend/src/theme/theme.ts` — Recharts color constants (keep in sync with `index.css`)
- `frontend/src/index.css` — Global styles and design tokens
- `start.sh` — Single entrypoint for Replit

## Notes

- Backend caches results ~20 min in memory; use the Refresh button or `POST /api/refresh` to force recompute
- Every page takes `?season=YYYY` (absent = current season); the season selector at the right of the tabs sets it. Nothing needs editing for a new season
- The Race Summary page (`backend/app/race_summary/`) pulls final classification, lap-by-lap
  positions, and pit stops from the same Jolpica/Ergast API as the rest of the app, then writes
  the narrative with Gemini (Cerebras as fallback) — requires a `GEMINI_API_KEY` and/or
  `CEREBRAS_API_KEY` in the environment. Its cache is
  ~6h (a completed race's data doesn't change).
- This used to run on FastF1 for richer telemetry/tire/weather/safety-car data, but FastF1's
  live-timing source (`livetiming.formula1.com`) blocks Replit's IP ranges outright (confirmed
  via direct `curl` from both the workspace and a deployment — a `403`/CloudFront block, not
  fixable in this codebase). Moved to Jolpica so the feature actually works on Replit; the
  trade-off is no tire strategy or telemetry section/chart, since Ergast doesn't have that data.

## User Preferences

- UI should be visually exciting — dark F1-themed design with red accents, grid background, bold typography
