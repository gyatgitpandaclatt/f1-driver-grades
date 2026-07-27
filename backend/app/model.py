import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.preprocessing import LabelEncoder, StandardScaler

from .config import SEASON_FEATURE_COLS


def run_model(season_labeled_df: pd.DataFrame):
    """
    Returns (season_labeled_df_with_predictions, feature_importances, model_note, rf_metrics).

    feature_importances is a pandas Series (feature -> importance) or None.
    model_note is a human-readable string explaining why the model was
    skipped, or None if it ran normally.
    rf_metrics is a dict of leave-one-out cross-validated accuracy/precision/
    recall/F1 (macro-averaged and per-class) for the RF classifier, or None
    if the model was skipped.
    """
    df = season_labeled_df.copy()
    n_unique_labels = df["season_label"].nunique()

    if len(df) < 2 or n_unique_labels < 2:
        df["rf_pred_label"] = df["season_label"]
        df["lr_pred_label"] = df["season_label"]
        note = (
            "Not enough class diversity yet to cross-validate a model "
            "(need at least 2 drivers and 2 distinct season labels) — "
            "predicted labels shown are just a copy of the actual labels."
        )
        return df, None, note, None

    X = df[SEASON_FEATURE_COLS].values
    le = LabelEncoder()
    y = le.fit_transform(df["season_label"])
    label_names = le.classes_

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    loo = LeaveOneOut()

    rf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    rf_preds = cross_val_predict(rf, X, y, cv=loo)

    lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    lr_preds = cross_val_predict(lr, X_scaled, y, cv=loo)

    rf_final = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    rf_final.fit(X, y)

    df["rf_pred_label"] = le.inverse_transform(rf_preds)
    df["lr_pred_label"] = le.inverse_transform(lr_preds)

    feature_importances = pd.Series(
        rf_final.feature_importances_, index=SEASON_FEATURE_COLS
    ).sort_values(ascending=False)

    class_labels = range(len(label_names))
    precision, recall, f1, support = precision_recall_fscore_support(
        y, rf_preds, labels=class_labels, zero_division=0
    )
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        y, rf_preds, average="macro", zero_division=0
    )
    rf_metrics = {
        "accuracy": float(accuracy_score(y, rf_preds)),
        "macro_precision": float(macro_precision),
        "macro_recall": float(macro_recall),
        "macro_f1": float(macro_f1),
        "per_class": [
            {
                "label": label_names[i],
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i in class_labels
        ],
    }

    return df, feature_importances, None, rf_metrics
