import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error
import joblib

pitches = pd.read_csv("data/statcast_2023_2026_engineered.csv")

modelable_pitch_types = [
    "FF", "SI", "SL", "CH", "ST", "FC", "CU", "FS", "KC"
]

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
    "spin_axis",
    "vertical_approach_angle",
    "horizontal_approach_angle",
    "velo_diff_from_primary",
    "horizontal_break_diff_from_primary",
    "vertical_break_diff_from_primary"
]

results = []

# Loop through each pitch type, training a separate model for each.
# This reflects that a "good" pitch means something different
# depending on pitch type (e.g., low drop for a four-seamer,
# high break for a slider).
for pitch_type in modelable_pitch_types:

    pitch_subset = pitches[pitches["pitch_type"] == pitch_type]

    X = pitch_subset[feature_columns]
    y = pitch_subset["delta_run_exp"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # For four-seam fastballs specifically, we discovered the model's
    # predicted value plateaus above ~99 mph due to sparse training
    # data in that velocity range - the model stops rewarding
    # additional velocity once data gets thin. A monotonic constraint
    # forces the model to keep improving its prediction as velocity
    # increases, no matter how few training examples exist at the
    # extreme end, since more velocity should never be worse, all
    # else equal.
    if pitch_type == "FF":
        monotone_constraints = tuple(
            -1 if feature in ["release_speed", "effective_speed"] else 0
            for feature in feature_columns
        )
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            random_state=42,
            monotone_constraints=monotone_constraints
        )
    else:
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            random_state=42
        )

    model.fit(X_train, y_train)

    train_predictions = model.predict(X_train)
    train_rmse = root_mean_squared_error(y_train, train_predictions)

    test_predictions = model.predict(X_test)
    test_rmse = root_mean_squared_error(y_test, test_predictions)

    print(
        f"{pitch_type}: trained on {len(X_train)} pitches, "
        f"train RMSE = {train_rmse:.4f}, test RMSE = {test_rmse:.4f}"
    )

    rmse = test_rmse

    joblib.dump(model, f"model/stuff_model_{pitch_type}.joblib")

    results.append({
        "pitch_type": pitch_type,
        "training_rows": len(X_train),
        "rmse": rmse
    })

results_df = pd.DataFrame(results)
results_df.to_csv("model/training_results.csv", index=False)

print("\nAll models trained and saved.")
print(results_df)