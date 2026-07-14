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

## User Preferences

- UI should be visually exciting — dark F1-themed design with red accents, grid background, bold typography
