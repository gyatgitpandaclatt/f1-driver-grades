import logging
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import cache
from .config import SEASON
from .exceptions import (
    NarrativeGenerationError,
    NoRaceDataError,
    RaceSessionNotAvailableError,
    UpstreamAPIError,
    UpstreamRateLimitedError,
)
from .race_summary import cache as race_summary_cache
from .race_summary.models import RaceSummaryResponse
from .schemas import DriverGradesResponse

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

logger = logging.getLogger("f1_driver_grades")

app = FastAPI(title="F1 Driver Grades API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(NoRaceDataError)
async def no_race_data_handler(request: Request, exc: NoRaceDataError):
    # A season with zero completed races (e.g. preseason) is a legitimate
    # empty state, not a server fault — 200 with a status flag the frontend
    # can branch on, not an error status code.
    return JSONResponse(status_code=200, content={
        "status": "no_data",
        "season": SEASON,
        "message": str(exc),
    })


@app.exception_handler(UpstreamRateLimitedError)
async def upstream_rate_limited_handler(request: Request, exc: UpstreamRateLimitedError):
    # A 429 from the provider is "we're busy, come back shortly" — 503 with a
    # Retry-After says exactly that to the browser and to the frontend, where
    # a 502 would claim the gateway itself is broken.
    logger.warning("Upstream rate limited: %s", exc)
    return JSONResponse(
        status_code=503,
        headers={"Retry-After": str(exc.retry_after)},
        content={
            "status": "busy",
            "retry_after": exc.retry_after,
            "message": (
                "The F1 data provider is rate limiting us right now. "
                f"Retrying in about {exc.retry_after}s."
            ),
        },
    )


@app.exception_handler(UpstreamAPIError)
async def upstream_error_handler(request: Request, exc: UpstreamAPIError):
    logger.warning("Upstream API error: %s", exc)
    return JSONResponse(status_code=502, content={
        "status": "error",
        "message": "Could not reach the F1 data provider. Please try again shortly.",
    })


@app.exception_handler(RaceSessionNotAvailableError)
async def race_session_not_available_handler(request: Request, exc: RaceSessionNotAvailableError):
    # Mirrors the NoRaceDataError handler above: a legitimate empty state
    # (results haven't been published for the latest round yet), not a
    # server fault.
    return JSONResponse(status_code=200, content={
        "status": "no_data",
        "season": SEASON,
        "message": str(exc),
    })


@app.exception_handler(NarrativeGenerationError)
async def narrative_generation_error_handler(request: Request, exc: NarrativeGenerationError):
    logger.warning("Narrative generation error: %s", exc)
    return JSONResponse(status_code=502, content={
        "status": "error",
        "message": "Could not generate the race narrative. Please try again shortly.",
    })


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={
        "status": "error",
        "message": "Something went wrong while processing your request.",
    })


def _warm_caches() -> None:
    # Grades first (cheap, and it's the landing page), then the race summary,
    # which is the slow one: a run of upstream pages plus a Claude call. Warm
    # it here so the first visitor to /race-summary reads a cache instead of
    # waiting out the whole pipeline.
    cache.try_warm_cache(SEASON)
    race_summary_cache.try_warm_cache(SEASON)


@app.on_event("startup")
async def startup_event():
    # In a background thread, not awaited: uvicorn does not start accepting
    # connections until startup handlers return, so warming inline made the
    # site unreachable (not merely slow) for the length of the warm.
    threading.Thread(target=_warm_caches, name="cache-warm", daemon=True).start()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/driver-grades", response_model=DriverGradesResponse)
async def get_driver_grades():
    return await run_in_threadpool(cache.get_or_compute, SEASON)


@app.post("/api/refresh", response_model=DriverGradesResponse)
async def refresh_driver_grades():
    return await run_in_threadpool(cache.force_refresh, SEASON)


@app.get("/api/race-summary", response_model=RaceSummaryResponse)
async def get_race_summary():
    return await run_in_threadpool(race_summary_cache.get_or_compute, SEASON)


@app.post("/api/race-summary/refresh", response_model=RaceSummaryResponse)
async def refresh_race_summary():
    return await run_in_threadpool(race_summary_cache.force_refresh, SEASON)


# Serve the built frontend (frontend/dist, produced by `npm run build`) so
# the whole app runs as a single process on a single port — no separate
# frontend server needed in production (e.g. on Replit). Registered last so
# it never shadows the /api/* routes above. Absent in local dev unless you
# run the frontend build; the Vite dev server + proxy is used instead.
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
