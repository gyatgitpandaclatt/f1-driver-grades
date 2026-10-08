import math

import pandas as pd

from .config import MIN_RACE_SHARE_FOR_GRADE, MIN_RACES_FOR_GRADE, ROOKIES


def build_driver_season_table(model_df: pd.DataFrame) -> pd.DataFrame:
    driver_season_df = (
        model_df.groupby("driver_code")
        .agg(
            races=("round", "nunique"),
            avg_finish_minus_grid=("finish_minus_grid", "mean"),
            overperf_share=("performance_label", lambda s: (s == "overperformed").mean()),
            underperf_share=("performance_label", lambda s: (s == "underperformed").mean()),
        )
        .reset_index()
    )
    driver_season_df["is_rookie"] = driver_season_df["driver_code"].isin(ROOKIES).astype(int)
    return driver_season_df


def min_races_for_grade(completed_rounds: int) -> int:
    """Races a driver needs to be graded, given how far the season has run."""
    return max(MIN_RACES_FOR_GRADE, math.ceil(MIN_RACE_SHARE_FOR_GRADE * completed_rounds))


def filter_gradeable_drivers(driver_season_df: pd.DataFrame, min_races: int) -> pd.DataFrame:
    """Drop drivers with too few races to be graded meaningfully.

    Applied to the per-driver table only, so an excluded driver's races
    still count everywhere they are a fact about someone else: the per-race
    label distribution, and their teammate's qualifying head-to-head score.

    Falls back to the unfiltered table if nobody clears the bar — after
    round 1 every driver has a single race, and an empty table would leave
    the page with nothing to show at all.
    """
    eligible = driver_season_df[driver_season_df["races"] >= min_races]
    if eligible.empty:
        return driver_season_df
    return eligible.reset_index(drop=True)


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
