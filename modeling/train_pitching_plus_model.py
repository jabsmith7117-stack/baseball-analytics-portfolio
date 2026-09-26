import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error
import joblib

pitches = pd.read_csv("data/statcast_2025_engineered.csv")

modelable_pitch_types = [
    "FF", "SI", "SL", "CH", "ST", "FC", "CU", "FS", "KC"
]

# Same shape features as the Stuff+ model, plus location (plate_x,
# plate_z) and count (balls, strikes). This combination reflects
# "Pitching+" as used in public models - physical characteristics,
# location, and situation combined, rather than shape alone.
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
    "vertical_break_diff_from_primary",
    "plate_x",
    "plate_z",
    "balls",
    "strikes"
]

results = []

for pitch_type in modelable_pitch_types:

    pitch_subset = pitches[pitches["pitch_type"] == pitch_type]

    X = pitch_subset[feature_columns]
    y = pitch_subset["delta_run_exp"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

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

    joblib.dump(model, f"model/pitching_plus_model_{pitch_type}.joblib")

    results.append({
        "pitch_type": pitch_type,
        "training_rows": len(X_train),
        "test_rmse": test_rmse
    })

results_df = pd.DataFrame(results)
results_df.to_csv("model/pitching_plus_training_results.csv", index=False)

print("\nAll Pitching+ models trained and saved.")
print(results_df)