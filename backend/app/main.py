import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import cache
from .config import SEASON
from .exceptions import NoRaceDataError, UpstreamAPIError
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


@app.exception_handler(UpstreamAPIError)
async def upstream_error_handler(request: Request, exc: UpstreamAPIError):
    logger.warning("Upstream API error: %s", exc)
    return JSONResponse(status_code=502, content={
        "status": "error",
        "message": "Could not reach the F1 data provider. Please try again shortly.",
    })


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={
        "status": "error",
        "message": "Something went wrong while computing driver grades.",
    })


@app.on_event("startup")
async def startup_event():
    await run_in_threadpool(cache.try_warm_cache, SEASON)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/driver-grades", response_model=DriverGradesResponse)
async def get_driver_grades():
    return await run_in_threadpool(cache.get_or_compute, SEASON)


@app.post("/api/refresh", response_model=DriverGradesResponse)
async def refresh_driver_grades():
    return await run_in_threadpool(cache.force_refresh, SEASON)


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
