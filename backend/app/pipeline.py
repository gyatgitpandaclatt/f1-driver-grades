from datetime import datetime, timezone

import pandas as pd

from .aggregate import assign_season_label, build_driver_season_table
from .config import SEASON
from .data_fetch import fetch_driver_standings, fetch_qualifying_results, fetch_race_results
from .exceptions import NoRaceDataError
from .features import build_target, engineer_features, merge_qualifying_and_race
from .model import run_model
from .scoring import compute_composite_scores, compute_qual_stats


def _row_to_driver_dict(row: pd.Series) -> dict:
    return {
        "driver_code": row["driver_code"],
        "driver_name": row["driver_name"],
        "constructor": row["Constructor"],
        "points": float(row["Points"]),
        "position": int(row["Position"]),
        "wins": int(row["Wins"]),
        "races": int(row["races"]),
        "is_rookie": bool(row["is_rookie"]),
        "season_label": row["season_label"],
        "rf_pred_label": row["rf_pred_label"],
        "lr_pred_label": row["lr_pred_label"],
        "composite": float(row["composite"]),
        "grade": row["grade"],
        "pts_score": float(row["pts_score"]),
        "pos_score": float(row["pos_score"]),
        "perf_score": float(row["perf_score"]),
        "grid_score": float(row["grid_score"]),
        "teammate_score": float(row["teammate_score"]),
        "qual_score": float(row["qual_score"]),
        "qual_pos_score": float(row["qual_pos_score"]),
        "qual_pole_score": float(row["qual_pole_score"]),
        "qual_h2h_score": float(row["qual_h2h_score"]),
        "tier_bonus": float(row["tier_bonus"]),
        "label_bonus": float(row["label_bonus"]),
        "model_bonus": float(row["model_bonus"]),
        "rookie_bonus": float(row["rookie_bonus"]),
        "avg_finish_minus_grid": None if pd.isna(row["avg_finish_minus_grid"]) else float(row["avg_finish_minus_grid"]),
        "avg_qual_pos": None if pd.isna(row["avg_qual_pos"]) else float(row["avg_qual_pos"]),
        "pole_rate": None if pd.isna(row["pole_rate"]) else float(row["pole_rate"]),
        "overperf_share": float(row["overperf_share"]),
        "underperf_share": float(row["underperf_share"]),
        "qual_h2h_wins": int(row["qual_h2h_wins"]),
        "qual_h2h_races": int(row["qual_h2h_races"]),
    }


def run_pipeline(season: int = SEASON) -> dict:
    qual_df = fetch_qualifying_results(season)
    race_df = fetch_race_results(season)

    if race_df.empty:
        raise NoRaceDataError(f"No completed races found for the {season} season yet.")

    merged_df = merge_qualifying_and_race(qual_df, race_df)
    features_df = engineer_features(merged_df)
    model_df = build_target(features_df)

    driver_season_df = build_driver_season_table(model_df)
    season_labeled_df = assign_season_label(driver_season_df)

    season_labeled_df, feature_importances, model_note = run_model(season_labeled_df)

    standings_df = fetch_driver_standings(season)
    qual_stats_df = compute_qual_stats(merged_df)

    final_df = compute_composite_scores(season_labeled_df, standings_df, qual_stats_df)

    drivers = [_row_to_driver_dict(row) for _, row in final_df.iterrows()]

    predicted_vs_actual = [
        {
            "driver_code": row["driver_code"],
            "actual_label": row["season_label"],
            "predicted_label": row["rf_pred_label"],
            "correct": row["season_label"] == row["rf_pred_label"],
        }
        for _, row in final_df.iterrows()
    ]

    misclassified = [
        {
            "driver_code": p["driver_code"],
            "actual_label": p["actual_label"],
            "predicted_label": p["predicted_label"],
        }
        for p in predicted_vs_actual
        if not p["correct"]
    ]

    feature_importances_list = (
        [{"feature": feat, "importance": float(imp)} for feat, imp in feature_importances.items()]
        if feature_importances is not None
        else None
    )

    # Per-race performance label counts (methodology page): exact counts
    # straight from model_df, rather than reconstructing them client-side
    # from the per-driver overperf_share/underperf_share aggregates.
    performance_label_distribution = {
        str(k): int(v) for k, v in model_df["performance_label"].value_counts().items()
    }

    return {
        "status": "ok",
        "season": season,
        "current_round": int(race_df["round"].max()),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "drivers": drivers,
        "meta": {
            "feature_importances": feature_importances_list,
            "predicted_vs_actual": predicted_vs_actual,
            "misclassified": misclassified,
            "model_note": model_note,
            "performance_label_distribution": performance_label_distribution,
            "total_race_entries": int(len(model_df)),
        },
    }
