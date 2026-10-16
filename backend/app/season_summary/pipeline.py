"""
Orchestrate the season summarizer for a finished season: season-level
ingestion -> championship-by-round features -> moments and footnotes -> LLM
narrative -> a single JSON-serializable dict matching SeasonSummaryResponse.

The current season has no season summary — it isn't over — and keeps the
race summary of its latest race instead.
"""
from datetime import datetime, timezone

import pandas as pd

from .. import lineups
from ..aggregate import grading_rounds, min_races_for_grade
from ..career import rookie_codes
from ..config import is_completed_season
from ..exceptions import NoRaceDataError
from ..scoring import primary_constructors
from . import events, features, ingestion, narrator


# Wider than any modern grid, so a modern season's chart draws everyone.
_CHART_MAX_FIELD = 26


def run_season_summary_pipeline(season: int) -> dict:
    if not is_completed_season(season):
        raise NoRaceDataError(
            f"The {season} season is still running, so there is no season summary "
            "yet — the Race Summary covers its latest race.",
            season=season,
        )

    data = ingestion.fetch_season_data(season)
    race_df = data["race_df"]
    sprint_df = data["sprint_df"]
    driver_standings = data["driver_standings"].sort_values("Position")
    constructor_standings = data["constructor_standings"]

    weekend = features.weekend_points(race_df, sprint_df)
    table = features.championship_table(race_df, weekend)
    official_standings_by_round = not features.counts_every_result(table, driver_standings)
    if official_standings_by_round:
        # One request a round, only for the seasons that need it.
        table = features.official_championship_table(
            ingestion.fetch_standings_by_round(season, sorted(int(r) for r in race_df["round"].unique()))
        )
    stats = features.driver_season_stats(race_df, weekend).set_index("driver_code")
    rounds = sorted(int(r) for r in race_df["round"].unique())

    # The same bar the grades use, so a driver left out of this season's
    # grades is exactly a driver footnoted here.
    min_races = min_races_for_grade(grading_rounds(race_df))
    part_timers = set(stats.index[stats["races"] < min_races])
    rookies = rookie_codes(season, race_df)

    s = events.SeasonData(
        season, race_df, weekend, table, driver_standings, constructor_standings, rookies, part_timers
    )
    decided = events.title_decided(s, set(int(r) for r in sprint_df["round"].unique()))
    constructors = primary_constructors(race_df).set_index("driver_code")["constructor"]

    final_standings = []
    for row in driver_standings.to_dict("records"):
        code = row["Driver Code"]
        if code not in stats.index:
            continue
        st = stats.loc[code]
        final_standings.append({
            "position": int(row["Position"]),
            "driver_code": code,
            "driver_name": row["Driver"],
            "constructor": constructors.get(code, row["Constructor"]),
            "points": float(row["Points"]),
            "wins": int(row["Wins"]),
            "podiums": int(st["podiums"]),
            "dnfs": int(st["dnfs"]),
            "races": int(st["races"]),
            "part_time": code in part_timers,
        })
    champion = final_standings[0]

    races = []
    for r in rounds:
        podium = race_df[(race_df["round"] == r) & (race_df["finish_pos"] <= 3)].sort_values("finish_pos")
        races.append({
            "round": r,
            "race_name": s.race_names[r],
            "winner": podium["driver_code"].iloc[0] if len(podium) else "",
            "podium": list(podium["driver_code"]),
        })

    context = {
        "season": int(season),
        "rounds": len(rounds),
        "final_standings": final_standings,
        "constructor_standings": [
            {
                "position": int(row.Position),
                "constructor": row.Constructor,
                "points": float(row.Points),
                "wins": int(row.Wins),
            }
            for row in constructor_standings.itertuples()
        ],
        "races": races,
        "quarters": events.quarterly_breakdown(s),
        "title_decided": decided,
        "championship_moments": events.title_moments(s, decided),
        "other_moments": events.other_moments(s),
        "part_time_drivers": events.part_time_footnotes(s),
        "indianapolis_500_only": events.indianapolis_500_only(s),
        "lineup_changes": lineups.lineup_changes(race_df),
        "rookies": sorted(rookies),
        "official_standings_by_round": official_standings_by_round,
    }

    top_five = [entry["driver_code"] for entry in final_standings[:5]]
    # On the chart: full-season drivers, the final top five, and anyone who
    # was in the top three after any round (a part-timer can be, early on),
    # so the lines the title story names are all drawn. A 1950s season had
    # dozens of one-off entrants, each of whom would be another line.
    featured = set(table.loc[table["position"] <= 3, "driver_code"])
    on_chart = table[~table["driver_code"].isin(part_timers) | table["driver_code"].isin(set(top_five) | featured)]
    # A field bigger than a modern grid (the 1950s had 40-80 full-season
    # entrants and non-scorers) would stretch the axis to P80 and squeeze the
    # title fight into a sliver: draw only drivers who were ever in the top 10.
    if on_chart["driver_code"].nunique() > _CHART_MAX_FIELD:
        top_ten = set(table.loc[table["position"] <= 10, "driver_code"])
        on_chart = on_chart[on_chart["driver_code"].isin(top_ten | set(top_five))]
    # Coloured and named: the final top three, and anyone else who led.
    leaders = [s.leader(r) for r in rounds]
    highlight = [entry["driver_code"] for entry in final_standings[:3]]
    highlight += [code for code in dict.fromkeys(leaders) if code not in highlight][:2]
    positions_by_round = {
        code: [int(p) if pd.notna(p) else None for p in s.positions[code]] for code in top_five
    }
    sections = narrator.generate_narrative(context, positions_by_round)

    return {
        "status": "ok",
        "season": int(season),
        "rounds": len(rounds),
        "champion": {
            "driver_code": champion["driver_code"],
            "driver_name": champion["driver_name"],
            "constructor": champion["constructor"],
            "points": champion["points"],
        },
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
        "context": context,
        "charts": {
            "standings_series": features.standings_series(on_chart),
            "rounds": [{"round": r, "race_name": s.race_names[r]} for r in rounds],
            "highlight_drivers": highlight,
        },
    }
