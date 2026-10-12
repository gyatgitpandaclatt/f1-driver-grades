from ..cache_base import SeasonCache
from ..config import RACE_SUMMARY_CACHE_TTL_SECONDS
from .pipeline import run_season_summary_pipeline

# Only finished seasons have a summary, and SeasonCache keeps those for the
# life of the process; the TTL here never applies in practice.
_cache = SeasonCache(run_season_summary_pipeline, RACE_SUMMARY_CACHE_TTL_SECONDS, name="season summary")


def get_or_compute(season: int) -> dict:
    return _cache.get_or_compute(season)


def force_refresh(season: int) -> dict:
    return _cache.force_refresh(season)
