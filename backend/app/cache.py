import threading
import time

from .config import CACHE_TTL_SECONDS, SEASON
from .pipeline import run_pipeline

_lock = threading.Lock()
_state = {"data": None, "computed_at": None}


def _compute_and_store(season: int) -> dict:
    data = run_pipeline(season)
    with _lock:
        _state["data"] = data
        _state["computed_at"] = time.monotonic()
    return data


def get_or_compute(season: int = SEASON) -> dict:
    with _lock:
        data = _state["data"]
        computed_at = _state["computed_at"]

    is_stale = computed_at is None or (time.monotonic() - computed_at) >= CACHE_TTL_SECONDS
    if data is None or is_stale:
        return _compute_and_store(season)
    return data


def force_refresh(season: int = SEASON) -> dict:
    return _compute_and_store(season)


def try_warm_cache(season: int = SEASON) -> None:
    """Best-effort initial compute for startup — swallow errors so the app
    still boots if the upstream API is briefly unreachable."""
    try:
        _compute_and_store(season)
    except Exception:
        pass
