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
from ..aggregate import min_races_for_grade
from ..career import rookie_codes
from ..config import is_completed_season
from ..exceptions import NoRaceDataError
from ..scoring import primary_constructors
from . import events, features, ingestion, narrator


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
    stats = features.driver_season_stats(race_df, weekend).set_index("driver_code")
    rounds = sorted(int(r) for r in race_df["round"].unique())

    # The same bar the grades use, so a driver left out of this season's
    # grades is exactly a driver footnoted here.
    min_races = min_races_for_grade(len(rounds))
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
        "lineup_changes": lineups.lineup_changes(race_df),
        "rookies": sorted(rookies),
    }

    top_five = [entry["driver_code"] for entry in final_standings[:5]]
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
            "standings_series": features.standings_series(table),
            "rounds": [{"round": r, "race_name": s.race_names[r]} for r in rounds],
            "highlight_drivers": [entry["driver_code"] for entry in final_standings[:3]],
        },
    }
