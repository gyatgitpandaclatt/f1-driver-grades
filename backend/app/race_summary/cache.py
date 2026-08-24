from ..cache_base import TTLCache
from ..config import RACE_SUMMARY_CACHE_TTL_SECONDS, SEASON
from .pipeline import run_race_summary_pipeline

_cache = TTLCache(run_race_summary_pipeline, RACE_SUMMARY_CACHE_TTL_SECONDS)


def get_or_compute(season: int = SEASON) -> dict:
    return _cache.get_or_compute(season)


def force_refresh(season: int = SEASON) -> dict:
    return _cache.force_refresh(season)


def try_warm_cache(season: int = SEASON) -> None:
    _cache.try_warm(season)
