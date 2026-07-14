import pandas as pd

from .config import ROOKIES


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
