from ..cache_base import SeasonCache
from ..config import RACE_SUMMARY_CACHE_TTL_SECONDS
from .pipeline import run_race_summary_pipeline

_cache = SeasonCache(run_race_summary_pipeline, RACE_SUMMARY_CACHE_TTL_SECONDS, name="race summary")


def get_or_compute(season: int) -> dict:
    return _cache.get_or_compute(season)


def force_refresh(season: int) -> dict:
    return _cache.force_refresh(season)


def try_warm_cache(season: int) -> None:
    _cache.try_warm(season)
