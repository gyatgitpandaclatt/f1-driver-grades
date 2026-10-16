import math

import pandas as pd

from .config import MIN_RACE_SHARE_FOR_GRADE, MIN_RACES_FOR_GRADE, is_indianapolis_500
from .features import UNJUDGED_LABELS


def _share(labels: pd.Series, label: str) -> float:
    """The share of a driver's judged races with this label: a first-lap
    collision or a race they never started is in neither column."""
    judged = labels[~labels.isin(UNJUDGED_LABELS)]
    return float((judged == label).mean()) if len(judged) else 0.0


def build_driver_season_table(model_df: pd.DataFrame, rookies: set[str]) -> pd.DataFrame:
    driver_season_df = (
        model_df.groupby("driver_code")
        .agg(
            races=("round", "nunique"),
            avg_finish_minus_grid=("finish_minus_grid", "mean"),
            overperf_share=("performance_label", lambda s: _share(s, "overperformed")),
            underperf_share=("performance_label", lambda s: _share(s, "underperformed")),
        )
        .reset_index()
    )
    driver_season_df["is_rookie"] = driver_season_df["driver_code"].isin(rookies).astype(int)
    return driver_season_df


def grading_rounds(race_df: pd.DataFrame) -> int:
    """The rounds the grading bar is a share of: every round but the
    Indianapolis 500 (a championship round until 1960, with its own field),
    which a Grand Prix regular didn't enter."""
    rounds = race_df.drop_duplicates("round")
    return int((~rounds["race_name"].map(is_indianapolis_500)).sum()) or len(rounds)


def min_races_for_grade(completed_rounds: int) -> int:
    """Races a driver needs to be graded, given how far the season has run."""
    return max(MIN_RACES_FOR_GRADE, math.ceil(MIN_RACE_SHARE_FOR_GRADE * completed_rounds))


def filter_gradeable_drivers(
    driver_season_df: pd.DataFrame, min_races: int
) -> tuple[pd.DataFrame, int | None]:
    """Drop drivers with too few races to be graded meaningfully.

    Applied to the per-driver table only, so an excluded driver's races
    still count everywhere they are a fact about someone else: the per-race
    label distribution, and their teammate's points ratio and qualifying
    head-to-head score.

    Falls back to the unfiltered table if nobody clears the bar — after
    round 1 every driver has a single race, and an empty table would leave
    the page with nothing to show at all.

    Returns the table and the bar actually applied: None when the fallback
    kept everyone.
    """
    eligible = driver_season_df[driver_season_df["races"] >= min_races]
    if eligible.empty:
        return driver_season_df, None
    return eligible.reset_index(drop=True), min_races


def _assign_season_label(row) -> str:
    if row["overperf_share"] > row["underperf_share"] and row["overperf_share"] > 0.3:
        return "overperformer"
    elif row["underperf_share"] > row["overperf_share"] and row["underperf_share"] > 0.3:
        return "underperformer"
    else:
        return "expected"


def assign_season_label(driver_season_df: pd.DataFrame) -> pd.DataFrame:
    season_labeled_df = driver_season_df.copy()
    season_labeled_df["season_label"] = season_labeled_df.apply(_assign_season_label, axis=1)
    return season_labeled_df
