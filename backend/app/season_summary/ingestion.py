"""
Fetch everything the season summarizer needs for one finished season: every
round's results, the sprint points, and the final drivers' and constructors'
standings, from the same Jolpica/Ergast provider as the rest of the app.

There is deliberately no lap data. Jolpica serves at most 100 rows a page
and 500 requests an hour, and one race's laps.json is ~1,200 timing rows: a
season of lap data would be ~290 requests, over half the hourly budget for
one page view. These season-level endpoints cost about a dozen requests
instead, and they are the same fetches the season's grades make, which
data_fetch keeps for the life of the process once a season is over — so
whichever of the two pages is opened second costs nothing upstream.

Career lookups (first points, podiums and wins) are made per driver, and
only for drivers whose season could hold one; see career.py.
"""
from ..data_fetch import (
    fetch_constructor_standings,
    fetch_driver_standings,
    fetch_driver_standings_after,
    fetch_race_results,
    fetch_sprint_points,
)
from ..exceptions import NoRaceDataError


def fetch_season_data(season: int) -> dict:
    race_df = fetch_race_results(season)
    if race_df.empty:
        raise NoRaceDataError(f"No race results found for the {season} season.", season=season)
    return {
        "race_df": race_df,
        "sprint_df": fetch_sprint_points(season),
        "driver_standings": fetch_driver_standings(season),
        "constructor_standings": fetch_constructor_standings(season),
    }


def fetch_standings_by_round(season: int, rounds: list[int]) -> dict:
    """The official drivers' championship after every round: one request a
    round, for the seasons whose summed results don't give it (dropped
    scores, an exclusion; see features.official_championship_table)."""
    return {r: fetch_driver_standings_after(season, r) for r in rounds}
