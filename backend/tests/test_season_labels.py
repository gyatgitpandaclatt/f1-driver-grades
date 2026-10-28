import pandas as pd

from app.aggregate import assign_season_label
from app.model import run_model


def _calm_season(n=20):
    # 2015-shaped: nobody's share clears the old fixed 0.3 bar.
    return pd.DataFrame({
        "driver_code": [f"D{i:02d}" for i in range(n)],
        "races": 19,
        "avg_finish_minus_grid": [0.1 * (i % 5) for i in range(n)],
        "overperf_share": [0.01 * i for i in range(n)],
        "underperf_share": [0.25 - 0.01 * i for i in range(n)],
        "is_rookie": 0,
    })


def test_calm_season_gets_every_label_and_is_cross_validated():
    labeled = assign_season_label(_calm_season())
    counts = labeled["season_label"].value_counts()
    assert counts["overperformer"] == counts["underperformer"] == 3
    assert set(labeled.nlargest(3, "overperf_share")["season_label"]) == {"overperformer"}
    _, _, note, metrics = run_model(labeled)
    assert note is None and metrics is not None


def test_tiny_field_is_skipped_not_crashed():
    labeled = assign_season_label(_calm_season(3))
    _, _, note, metrics = run_model(labeled)
    assert note is not None and metrics is None
