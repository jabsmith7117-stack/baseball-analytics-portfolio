import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib

# Load the raw file fresh, since "description" (needed to define
# whiffs) was never carried into the cleaned/engineered pipeline.
raw = pd.read_csv("data/statcast_2025_full_season.csv")

feature_columns = [
    "release_speed",
    "effective_speed",
    "release_spin_rate",
    "pfx_x",
    "pfx_z",
    "api_break_z_with_gravity",
    "api_break_x_arm",
    "release_pos_x",
    "release_pos_z",
    "release_pos_y",
    "arm_angle",
    "spin_axis"
]

fastball_family_types = ["FF"]

for pitch_type in fastball_family_types:

    subset = raw[raw["pitch_type"] == pitch_type].copy()

    subset = subset.dropna(subset=feature_columns + ["description"])
    subset = subset[subset["release_speed"] >= 60]

    # Define whiff: a swing where the batter missed entirely.
    subset["is_whiff"] = subset["description"].isin(
        ["swinging_strike", "swinging_strike_blocked"]
    ).astype(int)

    X = subset[feature_columns]
    y = subset["is_whiff"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        random_state=42,
        eval_metric="logloss"
    )

    model.fit(X_train, y_train)

    predictions = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, predictions)

    whiff_rate = y.mean()

    print(
        f"{pitch_type}: trained on {len(X_train)} pitches, "
        f"whiff rate = {whiff_rate:.1%}, test AUC = {auc:.4f}"
    )

    joblib.dump(model, f"model/whiff_model_{pitch_type}.joblib")