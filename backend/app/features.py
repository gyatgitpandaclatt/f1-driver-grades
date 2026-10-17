import numpy as np
import pandas as pd

# A retirement on the opening lap, or the lap after (laps completed, so 0 or
# 1), whatever its recorded cause. Nearly all are crashes, and the data never
# says who caused one: from 2025 Jolpica records every retirement as just
# "Retired", and its "Accident" covers multi-car pile-ups (Singapore 2017).
# So it counts for no one involved, the culprit included, rather than
# against the driver who was hit.
_FIRST_LAP_LAPS = 1

# Races with no race-day performance to judge, left out of the over- and
# underperformance shares (see aggregate.build_driver_season_table).
UNJUDGED_LABELS = {"did_not_start", "first_lap_retirement"}


def merge_qualifying_and_race(qual_df: pd.DataFrame, race_df: pd.DataFrame) -> pd.DataFrame:
    return pd.merge(
        race_df,
        qual_df[["season", "round", "driver_code", "qual_pos", "got_pole"]],
        on=["season", "round", "driver_code"],
        how="left",
    )


def _start_positions(df: pd.DataFrame, rounds_without_qualifying) -> pd.Series:
    """Where each driver started the race: the grid slot, penalties included.

    Grid 0 is a pit-lane start, counted as the back of the field. In a round
    without qualifying data 0 can also be a slot nobody recorded, so the
    start is unknown there. With no grid at all, the qualifying position
    stands in.
    """
    grid = pd.to_numeric(df["grid_pos"], errors="coerce")
    # From 2021 a driver who never took the start stays in the results.
    field = (df["position_text"] != "W").groupby(df["round"]).transform("sum")
    pit_lane = (grid == 0) & ~df["round"].isin(list(rounds_without_qualifying))
    return grid.where(grid > 0).mask(pit_lane, field).fillna(df["qual_pos"])


def engineer_features(df: pd.DataFrame, rounds_without_qualifying=()) -> pd.DataFrame:
    df = df.sort_values(["driver_code", "round"]).copy()

    # Places gained on race day, despite the name: positive when the driver
    # finishes ahead of where they started (started 10th, finished 5th ->
    # +5), negative when they lose places. Only for a car that ran to the
    # end: a retirement's classified position says nothing about its race.
    df["start_pos"] = _start_positions(df, rounds_without_qualifying)
    df["finish_minus_grid"] = (df["start_pos"] - df["finish_pos"]).where(df["retired"] == 0)

    # cumulative season stats
    df["cum_points"] = df.groupby("driver_code")["points_scored"].cumsum()
    df["cum_wins"] = df.groupby("driver_code")["got_win"].cumsum()
    df["cum_poles"] = df.groupby("driver_code")["got_pole"].cumsum()

    # participation count
    df["races_entered"] = df.groupby("driver_code").cumcount() + 1

    # rolling average over/underperformance
    df["mean_finish_minus_grid"] = (
        df.groupby("driver_code")["finish_minus_grid"]
          .expanding()
          .mean()
          .reset_index(level=0, drop=True)
    )

    return df


def build_target(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    retired_mask = df["retired"] == 1
    did_not_start_mask = df["position_text"] == "W"
    # Not a disqualification, and not when the laps completed are unknown (NaN).
    first_lap_retirement_mask = (
        (df["position_text"] == "R") & (df["laps"] <= _FIRST_LAP_LAPS)
    )
    # A finisher with no known start (no grid slot and no qualifying
    # position) leaves finish_minus_grid as NaN, and every comparison below
    # against NaN evaluates False, so np.select would otherwise silently
    # bucket these into "expected" alongside genuinely-expected results.
    # Label them distinctly so the reason stays visible downstream instead
    # of masquerading as a real "expected" outcome.
    unknown_start_mask = (~retired_mask) & df["finish_minus_grid"].isna()

    conditions = [
        did_not_start_mask,
        first_lap_retirement_mask,
        retired_mask,
        unknown_start_mask,
        df["finish_minus_grid"] >= 3,
        df["finish_minus_grid"] <= -3,
    ]
    choices = [
        "did_not_start",
        "first_lap_retirement",
        "underperformed",
        "unknown_start",
        "overperformed",
        "underperformed",
    ]

    df["performance_label"] = np.select(conditions, choices, default="expected")

    return df
