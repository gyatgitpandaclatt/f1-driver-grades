import numpy as np
import pandas as pd

from .config import CONSTRUCTOR_TIER, DEFAULT_CONSTRUCTOR_TIER, DEFAULT_TIER_BONUS, TIER_BONUS


def compute_qual_stats(merged_df: pd.DataFrame) -> pd.DataFrame:
    qual_stats = (
        merged_df.groupby("driver_code")
        .agg(
            avg_qual_pos=("qual_pos", "mean"),
            pole_rate=("got_pole", "mean"),
            races_with_qual=("qual_pos", "count"),
        )
        .reset_index()
    )

    # teammate qualifying H2H: for each race, flag who qualified better between teammates
    qual_h2h = merged_df[["round", "driver_code", "constructor", "qual_pos"]].copy()
    qual_h2h = qual_h2h.merge(
        qual_h2h.rename(columns={"driver_code": "tm_code", "qual_pos": "tm_qual_pos"}),
        on=["round", "constructor"],
    )
    qual_h2h = qual_h2h[qual_h2h["driver_code"] != qual_h2h["tm_code"]]
    qual_h2h["beat_tm_qual"] = (qual_h2h["qual_pos"] < qual_h2h["tm_qual_pos"]).astype(int)
    qual_tm_agg = (
        qual_h2h.groupby("driver_code")["beat_tm_qual"].agg(["mean", "sum", "count"]).reset_index()
        .rename(columns={
            "mean": "qual_tm_h2h",
            "sum": "qual_h2h_wins",
            "count": "qual_h2h_races",
        })
    )

    qual_stats = qual_stats.merge(qual_tm_agg, on="driver_code", how="left")
    qual_stats["qual_tm_h2h"] = qual_stats["qual_tm_h2h"].fillna(0.5)
    qual_stats["qual_h2h_wins"] = qual_stats["qual_h2h_wins"].fillna(0).astype(int)
    qual_stats["qual_h2h_races"] = qual_stats["qual_h2h_races"].fillna(0).astype(int)
    return qual_stats


def assign_grade(score: float) -> str:
    if score >= 80:
        return "S"
    elif score >= 65:
        return "A"
    elif score >= 50:
        return "B"
    elif score >= 35:
        return "C"
    else:
        return "D"


def compute_composite_scores(
    season_labeled_df: pd.DataFrame,
    standings_df: pd.DataFrame,
    qual_stats_df: pd.DataFrame,
) -> pd.DataFrame:
    code_to_name = standings_df.set_index("Driver Code")["Driver"].to_dict()

    standings_small = standings_df[["Driver Code", "Points", "Position", "Wins", "Constructor"]].rename(
        columns={"Driver Code": "driver_code"}
    )

    df = season_labeled_df[[
        "driver_code", "races", "avg_finish_minus_grid", "overperf_share", "underperf_share",
        "is_rookie", "season_label", "rf_pred_label", "lr_pred_label",
    ]].merge(standings_small, on="driver_code")

    df["driver_name"] = df["driver_code"].map(code_to_name).fillna(df["driver_code"])
    df = df.merge(qual_stats_df, on="driver_code", how="left")
    # A driver entirely absent from qual_stats_df (no qualifying data at
    # all) would otherwise leave these as NaN post-merge, breaking the
    # int() conversion downstream in pipeline.py.
    df["qual_h2h_wins"] = df["qual_h2h_wins"].fillna(0).astype(int)
    df["qual_h2h_races"] = df["qual_h2h_races"].fillna(0).astype(int)

    df["car_tier"] = df["Constructor"].map(CONSTRUCTOR_TIER).fillna(DEFAULT_CONSTRUCTOR_TIER)

    team_pts = df.groupby("Constructor")["Points"].transform("max")
    df["teammate_pts_ratio"] = (df["Points"] / team_pts.replace(0, np.nan)).fillna(0.5)

    max_pts = df["Points"].max()
    max_pos = df["Position"].max()

    df["pts_score"] = (df["Points"] / max_pts * 100).clip(0).round(1) if max_pts > 0 else 0.0

    # Guard: with only one classified position, (max_pos - 1) would be a
    # divide-by-zero. There's nothing to rank against, so treat everyone as
    # neutral rather than falsely scoring everyone as P1.
    if max_pos > 1:
        df["pos_score"] = ((max_pos - df["Position"]) / (max_pos - 1) * 100).round(1)
    else:
        df["pos_score"] = 50.0

    df["perf_score"] = ((df["overperf_share"] - df["underperf_share"]).clip(-1, 1) * 50 + 50).round(1)
    df["grid_score"] = ((-df["avg_finish_minus_grid"].clip(-8, 8) / 8) * 50 + 50).round(1)
    df["teammate_score"] = (df["teammate_pts_ratio"] * 100).clip(0, 100).round(1)

    max_qual = df["avg_qual_pos"].max()
    min_qual = df["avg_qual_pos"].min()
    # Guard: if every driver has an identical average qualifying position
    # (or there's no qualifying data at all), max_qual - min_qual is 0.
    # Neutral score rather than a NaN/inf blowup.
    if pd.notna(max_qual) and pd.notna(min_qual) and max_qual > min_qual:
        df["qual_pos_score"] = ((max_qual - df["avg_qual_pos"]) / (max_qual - min_qual) * 100).clip(0, 100).round(1)
    else:
        df["qual_pos_score"] = 50.0

    max_pole = df["pole_rate"].max()
    df["qual_pole_score"] = (df["pole_rate"] / (float(max_pole) if pd.notna(max_pole) and float(max_pole) > 0 else 1) * 100).clip(0, 100).round(1)
    df["qual_h2h_score"] = (df["qual_tm_h2h"] * 100).clip(0, 100).round(1)
    df["qual_score"] = (
        df["qual_pos_score"] * 0.60 +
        df["qual_pole_score"] * 0.10 +
        df["qual_h2h_score"] * 0.30
    ).round(1)

    df["tier_bonus"] = df["car_tier"].map(TIER_BONUS).fillna(DEFAULT_TIER_BONUS)

    label_bonus = {"overperformer": 4, "expected": 0, "underperformer": -4}
    df["label_bonus"] = df["season_label"].map(label_bonus).fillna(0)

    df["model_bonus"] = df.apply(
        lambda r: 0.5 if r["season_label"] == r["rf_pred_label"] else -0.5, axis=1
    )

    df["rookie_bonus"] = df["is_rookie"] * 2

    df["composite"] = (
        df["pts_score"] * 0.25 +
        df["pos_score"] * 0.20 +
        df["perf_score"] * 0.13 +
        df["grid_score"] * 0.12 +
        df["teammate_score"] * 0.08 +
        df["qual_score"] * 0.08 +
        df["label_bonus"] * 1.00 +
        df["model_bonus"] * 1.00 +
        df["tier_bonus"] * 1.00 +
        df["rookie_bonus"] * 1.00
    ).round(2)

    df["grade"] = df["composite"].apply(assign_grade)

    return df.sort_values("composite", ascending=False).reset_index(drop=True)
