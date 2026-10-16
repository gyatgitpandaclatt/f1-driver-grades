"""
Driver career lookups: the live rookie flag, and the career milestones (first
points, first podium, first win) the season summary looks for.

Everything here is about races already run, so it is cached for the life of
the process. Jolpica pages cap at 100 rows and allow 500 requests an hour,
so each question is asked with the narrowest query that answers it rather
than by pulling whole careers. "How many races did this driver start in
1987" is read from that season's results, which list drivers who failed to
qualify as well as starters: a few requests, shared by every driver asked
about that season and by the season's own pages.

Drivers are keyed by Ergast's driverId, not their three-letter code. Codes
are only unique within a season (both Schumachers are MSC).
"""
import math
from functools import lru_cache

import pandas as pd

from .aggregate import grading_rounds, min_races_for_grade
from .config import (
    API_BASE_URL,
    FIRST_CHAMPIONSHIP_SEASON,
    ROOKIE_ANY_START_COUNTS_BEFORE,
    ROOKIE_FULL_SEASON_RACE_SHARE,
    ROOKIE_SEASON_THRESHOLD,
)
from .data_fetch import _get_json, fetch_race_results, paginate_races
from .exceptions import UpstreamAPIError

# Every driver in the championship's history (about 900) fits several times over.
_CACHE_SIZE = 4096


@lru_cache(maxsize=_CACHE_SIZE)
def _seasons_raced(driver_id: str) -> tuple[int, ...]:
    url = f"{API_BASE_URL}/drivers/{driver_id}/seasons.json?limit=100"
    data = _get_json(url)
    try:
        seasons = data["MRData"]["SeasonTable"]["Seasons"]
        return tuple(sorted(int(s["season"]) for s in seasons))
    except (KeyError, ValueError) as exc:
        raise UpstreamAPIError(f"Unexpected response shape from {url}: {exc}") from exc


def _starts_in(driver_id: str, season: int) -> int:
    # From the season's results rather than a per-driver count: the early
    # decades' results list drivers who failed to qualify, and those aren't
    # starts. Every season asked about is finished, so its results are
    # fetched once and shared with that season's own pages (see data_fetch).
    results = fetch_race_results(season)
    return int(results.loc[results["driver_id"] == driver_id, "round"].nunique())


def _rounds_in(season: int) -> int:
    return grading_rounds(fetch_race_results(season))


def full_season_bar(rounds: int) -> int:
    """Races a driver must start for a season to count towards experience."""
    return max(1, math.ceil(ROOKIE_FULL_SEASON_RACE_SHARE * rounds))


def _counts_as_season(season: int, starts: int) -> bool:
    if season < ROOKIE_ANY_START_COUNTS_BEFORE:
        return starts > 0
    return starts >= full_season_bar(_rounds_in(season))


def _seasons_of_experience(driver_id: str, before: int, needed: int, partial_bar: int) -> int:
    """Seasons of experience in the driver's career before `before`, counting
    back from the most recent and stopping once `needed` are found: full
    seasons, plus one for every `partial_bar` starts in partial ones."""
    found = 0
    partial = 0
    for season in sorted((s for s in _seasons_raced(driver_id) if FIRST_CHAMPIONSHIP_SEASON <= s < before), reverse=True):
        starts = _starts_in(driver_id, season)
        if _counts_as_season(season, starts):
            found += 1
        else:
            partial += starts
            if partial >= partial_bar:
                found += 1
                partial -= partial_bar
        if found >= needed:
            break
    return found


def rookie_codes(season: int, race_df: pd.DataFrame) -> set[str]:
    """Codes of this season's drivers with fewer than ROOKIE_SEASON_THRESHOLD
    seasons of experience before it (see config for what counts).

    Most of a grid raced all of last season, so last season's results (one
    season-level fetch, shared with its own grades) settle most drivers at
    once. Only the rest — newcomers, stand-ins, returning veterans — have
    their careers looked up further back.

    Only drivers who raced enough to be graded are looked at: nothing shows
    a part-time driver's rookie status (they are left out of the grades and
    footnoted in the season summary), and in the 1950s they were most of the
    field — the Indianapolis 500 alone brought 33 — each costing a career
    lookup. If nobody clears the bar yet (after round 1), everyone is.

    Nobody is a rookie in the first championship season. Strictly everyone
    was, which says nothing: Farina and Fangio were veterans of Grand Prix
    racing before there was a championship to count it, and the data has
    no career before it to tell them from a newcomer.
    """
    starts = race_df.groupby("driver_id")["round"].nunique()
    regulars = starts.index[starts >= min_races_for_grade(grading_rounds(race_df))]
    if len(regulars):
        race_df = race_df[race_df["driver_id"].isin(regulars)]
    if season <= FIRST_CHAMPIONSHIP_SEASON:
        return set()
    previous = fetch_race_results(season - 1)
    previous_starts = (
        previous.groupby("driver_id")["round"].nunique().to_dict() if not previous.empty else {}
    )
    partial_bar = full_season_bar(grading_rounds(race_df))

    rookies = set()
    entrants = race_df[["driver_id", "driver_code"]].drop_duplicates("driver_id")
    for driver_id, code in entrants.itertuples(index=False):
        # Last season settles most of a grid without a career lookup.
        if _counts_as_season(season - 1, previous_starts.get(driver_id, 0)):
            experience, before = 1, season - 1
        else:
            experience, before = 0, season
        if experience < ROOKIE_SEASON_THRESHOLD:
            experience += _seasons_of_experience(
                driver_id, before, ROOKIE_SEASON_THRESHOLD - experience, partial_bar
            )
        if experience < ROOKIE_SEASON_THRESHOLD:
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
