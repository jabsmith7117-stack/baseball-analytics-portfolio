import pandas as pd
import joblib

pitches = pd.read_csv("data/statcast_2025_engineered.csv")

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
    "vertical_break_diff_from_primary",
    "plate_x",
    "plate_z",
    "balls",
    "strikes"
]

scored_pitch_types = []

for pitch_type in modelable_pitch_types:

    pitch_subset = pitches[pitches["pitch_type"] == pitch_type].copy()

    model = joblib.load(f"model/pitching_plus_model_{pitch_type}.joblib")

    X = pitch_subset[feature_columns]

    pitch_subset["predicted_run_value_pitching_plus"] = model.predict(X)

    type_median = pitch_subset["predicted_run_value_pitching_plus"].median()
    absolute_deviations = (
        pitch_subset["predicted_run_value_pitching_plus"] - type_median
    ).abs()
    type_mad = absolute_deviations.median()
    type_mad_scaled = type_mad * 1.4826

    pitch_subset["pitching_plus"] = (
        100 - ((pitch_subset["predicted_run_value_pitching_plus"] - type_median) / type_mad_scaled) * 10
    )

    pitch_subset["pitching_plus"] = pitch_subset["pitching_plus"].clip(lower=40, upper=160)
    pitch_subset["pitching_plus"] = pitch_subset["pitching_plus"].round(1)

    scored_pitch_types.append(pitch_subset)

    print(
        f"{pitch_type}: median run value = {type_median:.4f}, "
        f"pitching+ range = {pitch_subset['pitching_plus'].min():.1f} "
        f"to {pitch_subset['pitching_plus'].max():.1f}"
    )

all_scored_pitches = pd.concat(scored_pitch_types, ignore_index=True)

all_scored_pitches.to_csv("data/statcast_2025_pitching_plus_scored.csv", index=False)

print(f"\nTotal scored pitches: {len(all_scored_pitches)}")