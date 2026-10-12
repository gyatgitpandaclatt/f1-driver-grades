from .cache_base import SeasonCache
from .config import CACHE_TTL_SECONDS
from .pipeline import run_pipeline
from .snapshots import prefer_snapshot

_cache = SeasonCache(prefer_snapshot("driver_grades", run_pipeline), CACHE_TTL_SECONDS, name="driver grades")


def get_or_compute(season: int) -> dict:
    return _cache.get_or_compute(season)


def force_refresh(season: int) -> dict:
    return _cache.force_refresh(season)


def try_warm_cache(season: int) -> None:
    _cache.try_warm(season)
