from datetime import datetime, timezone

import pandas as pd

from .aggregate import (
    assign_season_label,
    build_driver_season_table,
    filter_gradeable_drivers,
    grading_rounds,
    min_races_for_grade,
)
from .career import rookie_codes
from .config import ROOKIE_SEASON_THRESHOLD, current_season, dropped_score_rule, is_indianapolis_500
from .data_fetch import (
    fetch_constructor_standings,
    fetch_driver_standings,
    fetch_qualifying_results,
    fetch_race_results,
    fetch_sprint_points,
)
from .exceptions import NoRaceDataError
from .features import build_target, engineer_features, merge_qualifying_and_race
from .model import run_model
from .scoring import (
    compute_composite_scores,
    compute_qual_h2h_pairs,
    compute_qual_stats,
    compute_teammate_pts_ratio,
    constructor_tiers,
    primary_constructors,
)


def _row_to_driver_dict(row: pd.Series) -> dict:
    return {
        "driver_code": row["driver_code"],
        "driver_name": row["driver_name"],
        "constructor": row["Constructor"],
        "points": float(row["Points"]),
        "position": int(row["Position"]),
        # "-" not classified in the championship, "D" disqualified from it
        # (Schumacher, 1997), "E" excluded; otherwise the position itself.
        "position_text": str(row["Position Text"]),
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


def _grid_as_qualifying(qual_df: pd.DataFrame, race_df: pd.DataFrame) -> tuple[pd.DataFrame, list[int]]:
    """Qualifying, with the grid standing in for any round that has none.

    There is no qualifying data before the mid-1990s, but until grid
    penalties arrived the grid was the qualifying order, near enough. A
    driver without a grid slot (0: a pit-lane start, or unrecorded) has no
    qualifying position, as before. Returns the rounds filled in.
    """
    missing = sorted(set(race_df["round"]) - set(qual_df["round"]))
    if not missing:
        return qual_df, []
    grid_pos = pd.to_numeric(race_df["grid_pos"], errors="coerce")
    grid = race_df[race_df["round"].isin(missing) & (grid_pos > 0)]
    filled = pd.DataFrame({
        "season": grid["season"],
        "round": grid["round"],
        "driver_code": grid["driver_code"],
        "qual_pos": grid["grid_pos"].astype(int),
        "got_pole": (grid["grid_pos"] == 1).astype(int),
    })
    combined = pd.concat([qual_df[filled.columns], filled], ignore_index=True) if not qual_df.empty else filled
    return combined, [int(r) for r in missing]


def _complete_standings(standings_df: pd.DataFrame, race_df: pd.DataFrame) -> pd.DataFrame:
    """The standings, with anyone who raced but isn't listed added at the end.

    The grades are joined on the standings: without this, a driver missing
    from them would silently vanish from the grades. They share the position
    after the last classified driver with everyone else the championship
    didn't place (see data_fetch._driver_standings), rather than taking an
    order the championship never gave them.
    """
    listed = set(standings_df["Driver Code"])
    missing = race_df[~race_df["driver_code"].isin(listed)]
    if missing.empty:
        return standings_df
    extra = (
        missing.groupby("driver_code")
        .agg(Driver=("driver", "first"), Constructor=("constructor", "first"),
             Points=("points_scored", "sum"), Wins=("got_win", "sum"))
        .reset_index()
        .rename(columns={"driver_code": "Driver Code"})
        .sort_values(["Points", "Wins"], ascending=False)
    )
    classified = standings_df.loc[standings_df["Classified"].astype(bool), "Position"]
    extra["Position"] = (int(classified.max()) if len(classified) else 0) + 1
    extra["Nationality"] = ""
    extra["Classified"] = False
    extra["Position Text"] = "-"
    return pd.concat([standings_df, extra[standings_df.columns]], ignore_index=True)


def _constructor_order(constructor_standings: pd.DataFrame, race_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """The constructors' championship order, for the car tiers.

    There was no constructors' championship before 1958; its order is then
    the constructors' points in the Grand Prix results, the Indianapolis 500
    left out (its makes raced nowhere else), with makes level on points and
    wins sharing a place rather than being split alphabetically.

    A constructor that raced but isn't in the standings (the championship
    lists only scorers in some seasons) and scored nothing is put last, so
    it gets the weakest-car tier, not the default meant for the unknown.
    """
    columns = ["Position", "Constructor", "Points", "Wins"]
    if not constructor_standings.empty:
        order, source = constructor_standings[columns].copy(), "standings"
    else:
        grand_prix = race_df[~race_df["race_name"].map(is_indianapolis_500)]
        order = (
            grand_prix.groupby("constructor")
            .agg(Points=("points_scored", "sum"), Wins=("got_win", "sum"))
            .reset_index()
            .rename(columns={"constructor": "Constructor"})
            .sort_values(["Points", "Wins", "Constructor"], ascending=[False, False, True])
            .reset_index(drop=True)
        )
        keys = list(zip(order["Points"], order["Wins"]))
        order["Position"] = [keys.index(key) + 1 for key in keys]
        order, source = order[columns], "results"
    scored = race_df.groupby("constructor")["points_scored"].sum()
    unlisted = [c for c in scored.index if c not in set(order["Constructor"]) and scored[c] == 0]
    if unlisted:
        last = int(order["Position"].max()) + 1 if len(order) else 1
        order = pd.concat([order, pd.DataFrame({
            "Position": last, "Constructor": sorted(unlisted), "Points": 0.0, "Wins": 0,
        })], ignore_index=True)
    return order, source


# A constructor that ran more cars than this in a race was, almost always, a
# make raced by privateers as well as its works team (the data records the
# make, not the entrant), so its drivers may not all be teammates. Works teams
# ran up to four cars (Mercedes in 1955, Ferrari through the 1950s).
_WORKS_TEAM_MAX_CARS = 4


def _makes_with_privateers(race_df: pd.DataFrame) -> list[str]:
    grand_prix = race_df[~race_df["race_name"].map(is_indianapolis_500)]
    cars = grand_prix.groupby(["round", "constructor"])["driver_id"].nunique()
    many = cars[cars > _WORKS_TEAM_MAX_CARS].reset_index()["constructor"]
    return sorted(set(many))


def run_pipeline(season: int) -> dict:
    # Race results first: they settle the season's driver codes, which every
    # other fetch reads (see data_fetch._driver_code).
    race_df = fetch_race_results(season)

    if race_df.empty:
        raise NoRaceDataError(f"No completed races found for the {season} season yet.", season=season)

    qual_df, grid_rounds = _grid_as_qualifying(fetch_qualifying_results(season), race_df)
    merged_df = merge_qualifying_and_race(qual_df, race_df)
    features_df = engineer_features(merged_df)
    model_df = build_target(features_df)

    entrants_df = build_driver_season_table(model_df, rookie_codes(season, race_df))
    # Before labelling or modelling: a one-race stand-in is noise to train on
    # and would stretch the score normalisation the rest of the grid is
    # measured against.
    driver_season_df, min_races = filter_gradeable_drivers(
        entrants_df, min_races_for_grade(grading_rounds(race_df))
    )
    season_labeled_df = assign_season_label(driver_season_df)

    season_labeled_df, feature_importances, model_note, rf_metrics = run_model(season_labeled_df)

    standings_df = _complete_standings(fetch_driver_standings(season), race_df)
    qual_stats_df = compute_qual_stats(merged_df)
    teammate_df = compute_teammate_pts_ratio(race_df, fetch_sprint_points(season))
    constructor_order, tiers_source = _constructor_order(fetch_constructor_standings(season), race_df)
    tiers_df = constructor_tiers(constructor_order)

    final_df = compute_composite_scores(
        season_labeled_df, standings_df, qual_stats_df, teammate_df, primary_constructors(race_df), tiers_df
    )
    qual_h2h_pairs = compute_qual_h2h_pairs(merged_df, final_df["driver_code"], min_races)

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

    names = race_df.drop_duplicates("driver_code").set_index("driver_code")["driver"]
    excluded_df = entrants_df[~entrants_df["driver_code"].isin(final_df["driver_code"])]
    excluded_drivers = [
        {
            "driver_code": row.driver_code,
            "driver_name": names.get(row.driver_code, row.driver_code),
            "races": int(row.races),
        }
        for row in excluded_df.sort_values("races", ascending=False).itertuples()
    ]

    return {
        "status": "ok",
        "season": season,
        "is_current_season": season == current_season(),
        "current_round": int(race_df["round"].max()),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "drivers": drivers,
        "meta": {
            "feature_importances": feature_importances_list,
            "predicted_vs_actual": predicted_vs_actual,
            "misclassified": misclassified,
            "model_note": model_note,
            "rf_metrics": rf_metrics,
            "performance_label_distribution": performance_label_distribution,
            "total_race_entries": int(len(model_df)),
            "min_races_for_grade": min_races,
            "qual_h2h_pairs": qual_h2h_pairs,
            "excluded_drivers": excluded_drivers,
            "rookie_season_threshold": ROOKIE_SEASON_THRESHOLD,
            "grid_as_qualifying_rounds": grid_rounds,
            "constructor_tiers_source": tiers_source,
            "makes_with_privateers": _makes_with_privateers(race_df),
            "dropped_scores": dropped_score_rule(season) is not None,
            "constructor_tiers": [
                {
                    "constructor": row.Constructor,
                    "position": int(row.Position),
                    "points": float(row.Points),
                    "tier": float(row.tier),
                    "tier_bonus": float(row.tier_bonus),
                }
                for row in tiers_df.itertuples()
            ],
        },
    }
