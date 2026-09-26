import pandas as pd

data = pd.read_csv("data/statcast_2023_2026_full.csv")

columns_to_keep = [
    "pitch_type",
    "pitch_name",
    "player_name",
    "p_throws",
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
    "vy0",
    "vz0",
    "vx0",
    "ay",
    "az",
    "ax",
    "plate_x",
    "plate_z",
    "balls",
    "strikes",
    "delta_run_exp"
]

pitches = data[columns_to_keep].copy()

# Drop rows missing a value in any of the key model columns.
# A pitch with a missing velocity, spin rate, or run value can't
# be used for training, since the model needs every input and
# the target to be present for that row.
pitches = pitches.dropna(
    subset=[
        "release_speed",
        "effective_speed",
        "release_spin_rate",
        "pfx_x",
        "pfx_z",
        "vy0",
        "vz0",
        "ay",
        "az",
        "delta_run_exp"
    ]
)

# Remove unrealistic pitches - almost certainly position players
# pitching in blowout games, which Statcast's classifier sometimes
# mislabels as breaking balls despite being nothing like a real
# MLB-caliber pitch. No genuine slider, curveball, etc. is thrown
# in the 30s-50s mph range.
rows_before_velocity_filter = len(pitches)

pitches = pitches[pitches["release_speed"] >= 60]

rows_removed = rows_before_velocity_filter - len(pitches)
print(f"Removed {rows_removed} unrealistic-velocity pitches")

print(f"Rows before cleaning: {len(data)}")
print(f"Rows after cleaning: {len(pitches)}")
print(pitches["pitch_type"].value_counts())

pitches.to_csv("data/statcast_2023_2026_cleaned.csv", index=False)