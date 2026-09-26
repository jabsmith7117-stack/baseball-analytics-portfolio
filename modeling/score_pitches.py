import pandas as pd
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

scored_pitch_types = []

for pitch_type in modelable_pitch_types:

    pitch_subset = pitches[pitches["pitch_type"] == pitch_type].copy()

    model = joblib.load(f"model/stuff_model_{pitch_type}.joblib")

    X = pitch_subset[feature_columns]

    # Predict expected run value for every pitch of this type.
    pitch_subset["predicted_run_value"] = model.predict(X)

    # Use median and MAD (median absolute deviation) instead of
    # mean and standard deviation. These are "robust statistics" -
    # a small number of extreme outlier predictions barely move
    # the median or MAD at all, whereas even one huge value can
    # drag the mean and standard deviation substantially. This
    # matters because with 700K+ real pitches, there will always
    # be a few unusual predictions no matter how much data is cleaned.
    type_median = pitch_subset["predicted_run_value"].median()
    absolute_deviations = (pitch_subset["predicted_run_value"] - type_median).abs()
    type_mad = absolute_deviations.median()

    # 1.4826 is a standard scaling constant that makes MAD comparable
    # to a normal standard deviation, so the resulting score behaves
    # the same way a typical z-score would.
    type_mad_scaled = type_mad * 1.4826

    pitch_subset["stuff_plus"] = (
        100 - ((pitch_subset["predicted_run_value"] - type_median) / type_mad_scaled) * 20
    )

    # As a final safety net, clip the score to a realistic range.
    # Public Stuff+ models rarely go outside roughly 40-160 even
    # for the most extreme pitches in baseball. This protects
    # against any remaining single-pitch outlier distorting the
    # display, without needing to hunt down every possible bad row.
    pitch_subset["stuff_plus"] = pitch_subset["stuff_plus"].clip(lower=10, upper=190)

    pitch_subset["stuff_plus"] = pitch_subset["stuff_plus"].round(1)

    scored_pitch_types.append(pitch_subset)

    print(
        f"{pitch_type}: median run value = {type_median:.4f}, "
        f"stuff+ range = {pitch_subset['stuff_plus'].min():.1f} "
        f"to {pitch_subset['stuff_plus'].max():.1f}"
    )

all_scored_pitches = pd.concat(scored_pitch_types, ignore_index=True)

all_scored_pitches.to_csv("data/statcast_2025_scored.csv", index=False)

print(f"\nTotal scored pitches: {len(all_scored_pitches)}")