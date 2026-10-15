# F1 Driver Grades

Computes S/A/B/C/D letter grades for F1 drivers from live qualifying/race
results and standings, and displays them in a web UI with feature-importance
and predicted-vs-actual charts. The current season is live; a season selector
at the right of the tabs switches every tab to any earlier season, back to the
first World Championship in 1950, where a Season Summary replaces the Race
Summary.

## Prerequisites

- **Python**: this machine only has Python reachable via the `py` launcher.
  Plain `python` resolves to a broken Windows Store stub — always use `py`.
- **Node.js**: not installed on this machine. Install the LTS build (22+)
  from https://nodejs.org before doing any frontend work, then enable pnpm
  (bundled with Node via corepack) and verify with:
  ```
  corepack enable
  node --version
  pnpm --version
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
pnpm install
pnpm run dev
```

App: http://localhost:5173 (proxies `/api/*` to the backend on :8000 — see `vite.config.ts`)

## Running as a single process (production / Replit)

The backend can serve the built frontend directly, so the whole app is one
process on one port — no separate frontend server needed:

```
cd frontend && pnpm install && pnpm run build && cd ..
cd backend && py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or just run `bash start.sh` from the project root, which does both steps.
This is what Replit runs (see `.replit`) — import this repo into Replit via
"Import from GitHub" and it should build and start automatically. If the
Nix channel in `.replit`/`replit.nix` is stale by the time you read this,
Replit will prompt you to fix it, or you can just delete both files and let
Replit auto-detect Python + Node.js instead.

## Deploying to Google Cloud Run

The app deploys as a single container — Docker is used because the image
needs both Node (to build the frontend) and Python (to run the backend).
The `Dockerfile` does the same two steps as `start.sh`: build
`frontend/dist`, then run uvicorn on whatever `PORT` Cloud Run injects
(8080 by default).

1. Push this repo to GitHub (if not already).
2. In the Cloud Run console: **Create service > Continuously deploy from a
   repository**, connect GitHub and pick this repo. Build type: Dockerfile.
3. Set the trigger's branch pattern to `^master$` — the default is `^main$`,
   which matches nothing in this repo, so the first deploy never starts.
4. Under Variables & Secrets add `GEMINI_API_KEY` and `CEREBRAS_API_KEY`
   (Secret Manager secrets or plain env vars) — same values as
   `backend/.env` locally; they are never committed to the repo.
5. Memory: 1 GiB is a safe floor for pandas + scikit-learn. Leave min
   instances at 0 so the service scales to zero and stays inside the free
   tier.
6. Create. Cloud Build builds the image and redeploys on every push to
   `master`.

### Two Cloud Run settings the startup warm depends on

The backend warms both caches in a background thread at startup (see
`_warm_caches` in `backend/app/main.py`), so the first visitor to
`/race-summary` reads a cache instead of waiting out a run of upstream
requests plus an LLM call. On Cloud Run's defaults that warm does not
work, for two separate reasons:

- **CPU is allocated only during request processing by default.** The warm
  thread starts *after* the startup handler returns, so it is throttled to
  almost no CPU and either crawls or times out. Set **CPU allocation** to
  "CPU is always allocated" for the warm to run to completion. The warm
  logs `Startup warm of race summary finished in Ns` or a warning saying
  why it failed — check the logs after a deploy to see which happened.
- **Scale to zero means every cold start warms again.** The caches are
  per-instance and in-memory, so with `min-instances: 0` a low-traffic
  service pays a fresh narrative (one LLM call) on most visits, and the
  6h cache rarely gets used. Either accept that cost, or set
  `min-instances: 1` so one warm instance stays up and the cache survives
  between visits. Note that both of these settings mean paying for an idle
  instance, which takes the service outside the always-free tier.

If you would rather stay scaled to zero, leave both at their defaults and
accept that `/race-summary` is slow on a cold start — it is correct either
way, just not pre-warmed.

No frontend code changes are needed for this move: the frontend only ever
calls relative paths like `/api/driver-grades` (see `frontend/src/api/client.ts`),
so it works unmodified on whatever host/domain serves it, same as it does
on Replit.

To test the exact production image locally before deploying, with Docker
installed:

```
docker build -t f1-driver-grades .
docker run -p 8000:8000 -e GEMINI_API_KEY=... -e CEREBRAS_API_KEY=... f1-driver-grades
```

## Snapshots of finished seasons

A finished season's grades and season summary never change, but computing
them costs ~20–80 Jolpica requests, an LLM call and several seconds of
model fitting — and on Cloud Run, with the in-memory caches empty after
every cold start, that cost comes back again and again. Saving them once
removes it: the site serves a season's snapshot without touching Jolpica
or the LLM.

From `backend/`, on a machine that can reach Jolpica, with
`GEMINI_API_KEY` and/or `CEREBRAS_API_KEY` in `backend/.env`:

```
py -m app.snapshots              # every finished season, 1950 on
py -m app.snapshots 2024 2025    # just these
py -m app.snapshots 1950-1959    # a range
py -m app.snapshots --force      # rebuild ones already saved
py -m app.snapshots --grades-only
```

Then commit `backend/snapshots/*.json`; the Docker image picks them up with
the rest of `backend/`. Every season from 1950 is ~2,500 requests against
Jolpica's 500/hour, so a full run takes five to six hours, most of it waiting
out the rate limit, which the script does by itself before carrying on. It
builds the oldest season first, because each season's rookie check reads the
seasons before it, which are then already in memory. It also writes one
narrative per season; if the LLM's free tier runs out partway, rerun it the
next day: saved seasons are skipped. Snapshots are ~40 KB a season, ~3 MB
for all of them. Rerun it after a season ends to save that one too.

A season without a snapshot is computed live, as before. So is one whose
snapshot no longer matches the response schema (after a field is added,
say): it is logged and ignored until rebuilt with `--force`. A snapshot is
fixed, so the Season Summary page hides its Refresh button for one; to
rewrite a narrative, rebuild that season's snapshot.

## Notes

- Nothing needs updating each season. The current season is the calendar year,
  and `FIRST_SEASON` in `backend/app/config.py` sets how far back the
  season selector reaches (1950, every season Jolpica has). Rookies (fewer than `ROOKIE_SEASON_THRESHOLD`
  full seasons behind them), constructor tiers (from that season's
  constructors' championship order) and lineup changes (from the entry lists)
  are all derived from the data; `config.py` only holds their thresholds.
  `LINEUP_CHANGE_REASONS` there can optionally say *why* a lineup changed
  (e.g. an injury), which the data never carries.
- The backend caches computed results in memory (~20 min TTL) to avoid
  hammering the upstream API on every page load. Use the Refresh button in the
  UI (or `POST /api/refresh`) to force a recompute. A finished season never
  changes, so its grades and season summary come from its snapshot if one is
  saved (see above), or are computed the first time someone opens it and then
  kept for the life of the process; the startup warm only covers the current
  season.
- Jolpica serves at most 100 rows a page and allows 500 requests an hour
  unauthenticated. Opening a past season for the first time costs roughly
  20–80 requests (its results, plus career lookups for rookies and career
  firsts, plus one standings request a round for a season with dropped
  scores), which is why nothing season-wide reads lap data: a single race's
  laps are ~12 requests.
- The early decades' data has gaps, each worked around in the open rather
  than hidden:
  - **No driver codes.** Ergast only has three-letter codes for drivers from
    about the 2000s on. Everyone else gets one made from their surname
    (Fangio is FAN), unique within the season, with the season's regulars
    choosing first.
  - **No qualifying before the mid-1990s.** The starting grid stands in for
    the qualifying order in any round without qualifying data; the
    head-to-head and methodology pages say so for those seasons.
  - **No constructors' championship before 1958.** Car tiers come from the
    constructors' points in the race results instead.
  - **Make of car, not entrant.** The data records a car's constructor, not
    who entered it, so before the 1980s a privateer Maserati or Brabham
    counts as the works drivers' teammate. The pages say so.
  - **Dropped scores.** Until 1990 only a driver's best results counted, so
    summed results crown the wrong champion (Prost outscored Senna in 1988).
    A season whose summed results don't match the official points has its
    championship-by-round chart built from the official standings after
    each round.
  - **Failures to qualify and shared drives.** Results list entrants who
    failed to (pre-)qualify, which are dropped: they never started. Until
    1957 a driver could take over a teammate's car and share its points,
    appearing twice in one race; they get one result, the better one, with
    both sets of points.
  - **The Indianapolis 500** was a championship round until 1960, with its
    own field, so a 1950s season has dozens of one-off entrants. They are
    part-time drivers like any other: footnoted, not graded, and left out of
    the rookie checks and the championship chart.
- The Season Summary page (`/season-summary?season=YYYY`, backed by
  `backend/app/season_summary/`) is for finished seasons only: a quick summary,
  championship position by round, a quarter-by-quarter analysis, the crucial
  moments for the title (lead changes, points swings from wins and
  retirements, close finishes between contenders, where the title was
  decided) and beyond it (first wins and podiums outside the top five,
  rookies' firsts, crucial midfield points), with part-time drivers as
  footnotes. It is built from race results only — no lap data — and uses
  the same narrative providers as the Race Summary below.
- The Race Summary page (`/race-summary`, backed by `backend/app/race_summary/`)
  needs a `GEMINI_API_KEY` and/or `CEREBRAS_API_KEY` to write the race
  narrative (Gemini is tried first, Cerebras is the fallback; both have free
  tiers) — copy `backend/.env.example` to `backend/.env` and fill them in (loaded
  automatically on startup), or set it as a real environment variable. Race
  data comes from the same Jolpica/Ergast API as the rest of the app (final
  classification, lap-by-lap positions, pit stops) — there's deliberately no
  tire compound, weather, or safety-car data, since Ergast doesn't have it;
  the narrative is written from what's available and instructed not to guess
  at the rest.
