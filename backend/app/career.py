"""
Driver career lookups: the live rookie flag, and the career milestones (first
points, first podium, first win) the season summary looks for.

Everything here is about races already run, so it is cached for the life of
the process. Jolpica pages cap at 100 rows and allow 500 requests an hour,
so each question is asked with the narrowest query that answers it rather
than by pulling whole careers: "how many races did this driver start in
2019" is one request whatever their career length.

Drivers are keyed by Ergast's driverId, not their three-letter code. Codes
are only unique within a season (both Schumachers are MSC).
"""
import math
from functools import lru_cache

import pandas as pd

from .config import API_BASE_URL, ROOKIE_FULL_SEASON_RACE_SHARE, ROOKIE_SEASON_THRESHOLD
from .data_fetch import _get_json, fetch_race_results, paginate_races
from .exceptions import UpstreamAPIError

# Every driver who has raced in the seasons on offer fits many times over.
_CACHE_SIZE = 512


def _mrdata_total(url: str) -> int:
    data = _get_json(url)
    try:
        return int(data["MRData"]["total"])
    except (KeyError, ValueError) as exc:
        raise UpstreamAPIError(f"Unexpected response shape from {url}: {exc}") from exc


@lru_cache(maxsize=_CACHE_SIZE)
def _seasons_raced(driver_id: str) -> tuple[int, ...]:
    url = f"{API_BASE_URL}/drivers/{driver_id}/seasons.json?limit=100"
    data = _get_json(url)
    try:
        seasons = data["MRData"]["SeasonTable"]["Seasons"]
        return tuple(sorted(int(s["season"]) for s in seasons))
    except (KeyError, ValueError) as exc:
        raise UpstreamAPIError(f"Unexpected response shape from {url}: {exc}") from exc


@lru_cache(maxsize=_CACHE_SIZE)
def _starts_in(driver_id: str, season: int) -> int:
    return _mrdata_total(f"{API_BASE_URL}/{season}/drivers/{driver_id}/results.json?limit=1")


@lru_cache(maxsize=_CACHE_SIZE)
def _rounds_in(season: int) -> int:
    # Races with a winner: the rounds actually run, not the ones scheduled.
    return _mrdata_total(f"{API_BASE_URL}/{season}/results/1.json?limit=1")


def full_season_bar(rounds: int) -> int:
    """Races a driver must start for a season to count towards experience."""
    return max(1, math.ceil(ROOKIE_FULL_SEASON_RACE_SHARE * rounds))


def _full_seasons_before(driver_id: str, before: int, needed: int) -> int:
    """Full seasons in the driver's career before `before`, counting back
    from the most recent and stopping once `needed` are found."""
    found = 0
    for season in sorted((s for s in _seasons_raced(driver_id) if s < before), reverse=True):
        if _starts_in(driver_id, season) >= full_season_bar(_rounds_in(season)):
            found += 1
            if found >= needed:
                break
    return found


def rookie_codes(season: int, race_df: pd.DataFrame) -> set[str]:
    """Codes of this season's drivers with fewer than ROOKIE_SEASON_THRESHOLD
    full seasons before it.

    Most of a grid raced all of last season, so last season's results (one
    season-level fetch, shared with its own grades) settle most drivers at
    once. Only the rest — newcomers, stand-ins, returning veterans — have
    their careers looked up further back.
    """
    previous = fetch_race_results(season - 1)
    if previous.empty:
        previous_starts: dict[str, int] = {}
        previous_bar = None
    else:
        previous_starts = previous.groupby("driver_id")["round"].nunique().to_dict()
        previous_bar = full_season_bar(int(previous["round"].nunique()))

    rookies = set()
    entrants = race_df[["driver_id", "driver_code"]].drop_duplicates("driver_id")
    for driver_id, code in entrants.itertuples(index=False):
        full = 0
        if previous_bar is not None and previous_starts.get(driver_id, 0) >= previous_bar:
            full = 1
        if full < ROOKIE_SEASON_THRESHOLD:
            full += _full_seasons_before(driver_id, season - 1, ROOKIE_SEASON_THRESHOLD - full)
        if full < ROOKIE_SEASON_THRESHOLD:
            rookies.add(code)
    return rookies


RaceKey = tuple[int, int]  # (season, round), which orders chronologically


@lru_cache(maxsize=_CACHE_SIZE)
def first_finish_at(driver_id: str, position: int) -> RaceKey | None:
    """The first race the driver finished in exactly this classified position.

    Takes the earliest of everything returned rather than trusting the
    provider's order, which costs nothing extra: few drivers have more than
    a page of finishes in any one position.
    """
    races = paginate_races(f"drivers/{driver_id}/results/{position}")
    return min(((int(r["season"]), int(r["round"])) for r in races), default=None)


def first_podium(driver_id: str) -> RaceKey | None:
    finishes = [first_finish_at(driver_id, position) for position in (1, 2, 3)]
    return min((f for f in finishes if f is not None), default=None)


@lru_cache(maxsize=_CACHE_SIZE)
def first_points_at(driver_id: str) -> RaceKey | None:
    """The first Grand Prix the driver scored points in.

    Points-paying positions changed across eras, so this can't be asked as a
    position query and reads the driver's career instead. Only called for
    rookies and part-time drivers, whose careers are short.
    """
    scored = [
        (int(race["season"]), int(race["round"]))
        for race in paginate_races(f"drivers/{driver_id}/results")
        for result in race.get("Results", [])
        if float(result.get("points", 0)) > 0
    ]
    return min(scored, default=None)
