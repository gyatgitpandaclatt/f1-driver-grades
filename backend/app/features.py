import numpy as np
import pandas as pd


def merge_qualifying_and_race(qual_df: pd.DataFrame, race_df: pd.DataFrame) -> pd.DataFrame:
    return pd.merge(
        race_df,
        qual_df[["season", "round", "driver_code", "qual_pos", "got_pole"]],
        on=["season", "round", "driver_code"],
        how="left",
    )


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["driver_code", "round"]).copy()

    # race result relative to qualifying
    df["finish_minus_grid"] = df["qual_pos"] - df["finish_pos"]

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

    dnf_mask = df["dnf"] == 1
    # A driver can be missing from the qualifying merge (e.g. didn't set a
    # time, or wasn't part of qual_df at all) without being a DNF in the
    # race. That leaves finish_minus_grid as NaN, and every comparison below
    # against NaN evaluates False, so np.select would otherwise silently
    # bucket these into "expected" alongside genuinely-expected results.
    # Label them distinctly so the reason stays visible downstream instead
    # of masquerading as a real "expected" outcome.
    no_qual_mask = (~dnf_mask) & df["finish_minus_grid"].isna()

    conditions = [
        dnf_mask,
        no_qual_mask,
        df["finish_minus_grid"] >= 3,
        df["finish_minus_grid"] <= -3,
    ]
    choices = ["underperformed", "no_qualifying_data", "overperformed", "underperformed"]

    df["performance_label"] = np.select(conditions, choices, default="expected")

    return df
