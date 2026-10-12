"""
Turn a season's race and sprint results into the championship as it stood
after every round, and the per-driver figures the rest of season_summary
works from.
"""
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

# Countback compares finishing positions this far down; nobody classifies lower.
_COUNTBACK_DEPTH = 30


def weekend_points(race_df: pd.DataFrame, sprint_df: pd.DataFrame) -> pd.DataFrame:
    """One row per driver per round: Grand Prix points, sprint points, and their total."""
    weekend = race_df[["round", "race_name", "driver_id", "driver_code", "constructor", "points_scored"]].merge(
        sprint_df, on=["round", "driver_code"], how="left"
    )
    weekend["sprint_points"] = weekend["sprint_points"].fillna(0.0)
    weekend["points"] = weekend["points_scored"] + weekend["sprint_points"]
    return weekend


def championship_table(race_df: pd.DataFrame, weekend: pd.DataFrame) -> pd.DataFrame:
    """Every driver's points and championship position after every round.

    Recomputed from the results rather than fetched (that would be one
    standings request per round): the points are the ones the results
    carry, half-points races included, and ties are broken the FIA way, by
    countback of Grand Prix finishes — most wins, then most seconds, and so
    on.
    """
    totals: dict[str, float] = defaultdict(float)
    finishes: dict[str, Counter] = defaultdict(Counter)
    rows = []
    for round_number in sorted(race_df["round"].unique()):
        for row in weekend[weekend["round"] == round_number].itertuples():
            totals[row.driver_code] += row.points
        for row in race_df[race_df["round"] == round_number].itertuples():
            if pd.notna(row.finish_pos):
                finishes[row.driver_code][int(row.finish_pos)] += 1

        def countback(code: str):
            return (-totals[code], *(-finishes[code][p] for p in range(1, _COUNTBACK_DEPTH + 1)), code)

        for position, code in enumerate(sorted(totals, key=countback), start=1):
            rows.append({
                "round": int(round_number),
                "driver_code": code,
                "points": float(totals[code]),
                "position": position,
            })
    return pd.DataFrame(rows)


def split_quarters(rounds: list[int]) -> list[list[int]]:
    """The season's rounds in four near-equal runs, earliest first."""
    return [[int(r) for r in quarter] for quarter in np.array_split(sorted(rounds), 4) if len(quarter)]


def driver_season_stats(race_df: pd.DataFrame, weekend: pd.DataFrame) -> pd.DataFrame:
    stats = race_df.groupby("driver_code").agg(
        races=("round", "nunique"),
        wins=("finish_pos", lambda s: int((s == 1).sum())),
        podiums=("finish_pos", lambda s: int((s <= 3).sum())),
        dnfs=("dnf", "sum"),
        best_finish=("finish_pos", "min"),
    )
    stats["points"] = weekend.groupby("driver_code")["points"].sum()
    return stats.reset_index()


def standings_series(table: pd.DataFrame) -> list[dict]:
    """Rows of {"round": N, "<driver_code>": position, ...}, shaped like the
    race summary's lap chart so the same chart draws it."""
    series = []
    for round_number, rows in table.groupby("round"):
        entry: dict = {"round": int(round_number)}
        entry.update({row.driver_code: float(row.position) for row in rows.itertuples()})
        series.append(entry)
    return series
