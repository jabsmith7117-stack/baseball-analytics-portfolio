import pandas as pd
import numpy as np

pitches = pd.read_csv("data/statcast_2023_2026_cleaned.csv")

# --- Vertical and Horizontal Approach Angle ---
# These describe the angle the pitch is traveling at when it crosses
# home plate, using the pitch's velocity components at that moment.
# A flatter vertical approach angle (closer to 0) means the pitch
# stays "on plane" longer, associated with a fastball that appears
# to "rise" and generates more whiffs up in the zone.

# Time from release to the plate, solved from the vertical velocity
# and acceleration components (standard pitch trajectory physics).
time_to_plate = (
    -pitches["vy0"] - np.sqrt(pitches["vy0"] ** 2 - 2 * pitches["ay"] * 50)
) / pitches["ay"]

vy_at_plate = pitches["vy0"] + pitches["ay"] * time_to_plate
vz_at_plate = pitches["vz0"] + pitches["az"] * time_to_plate
vx_at_plate = pitches["vx0"] + pitches["ax"] * time_to_plate

pitches["vertical_approach_angle"] = -np.degrees(
    np.arctan(vz_at_plate / vy_at_plate)
)
pitches["horizontal_approach_angle"] = -np.degrees(
    np.arctan(vx_at_plate / vy_at_plate)
)

# --- Primary-Pitch-Relative Differentials ---
# For each pitcher, find their single most-thrown pitch type (this
# could be a four-seamer, sinker, cutter, etc.), and use that as the
# baseline for velocity and movement. This captures deception/
# tunneling - a secondary pitch's value partly comes from how
# different it looks from whatever the batter sees most often out of
# that pitcher's hand, not just its own raw shape. Using each
# pitcher's actual primary pitch (rather than assuming it's always a
# four-seamer) means every pitcher gets a valid baseline, including
# sinker-only or cutter-only pitchers.
# A pitcher's baseline for tunneling/deception should be their
# primary FASTBALL specifically (four-seam, sinker, or cutter) -
# not just whichever pitch they throw most often overall. If we
# used "most-thrown pitch" without this restriction, a pitcher
# whose best secondary pitch happens to be thrown slightly more
# than their fastball (e.g. a changeup-heavy pitcher) would end up
# comparing that pitch to itself, producing a meaningless diff of
# zero for exactly the pitch we most want to evaluate.
fastball_family = ["FF", "SI", "FC"]

primary_pitch_by_pitcher = (
    pitches[pitches["pitch_type"].isin(fastball_family)]
    .groupby(["player_name", "pitch_type"])
    .size()
    .reset_index(name="pitch_count")
    .sort_values("pitch_count", ascending=False)
    .drop_duplicates(subset="player_name", keep="first")
    [["player_name", "pitch_type"]]
    .rename(columns={"pitch_type": "primary_pitch_type"})
)

# A small number of pitchers may throw no fastball-family pitch at
# all. For those, fall back to their single most-thrown pitch of
# any kind, since some baseline is better than none.
pitchers_with_fastball = set(primary_pitch_by_pitcher["player_name"])
all_pitchers = set(pitches["player_name"])
pitchers_without_fastball = all_pitchers - pitchers_with_fastball

if pitchers_without_fastball:
    fallback_primary = (
        pitches[pitches["player_name"].isin(pitchers_without_fastball)]
        .groupby(["player_name", "pitch_type"])
        .size()
        .reset_index(name="pitch_count")
        .sort_values("pitch_count", ascending=False)
        .drop_duplicates(subset="player_name", keep="first")
        [["player_name", "pitch_type"]]
        .rename(columns={"pitch_type": "primary_pitch_type"})
    )
    primary_pitch_by_pitcher = pd.concat(
        [primary_pitch_by_pitcher, fallback_primary], ignore_index=True
    )
    print(f"{len(pitchers_without_fastball)} pitchers had no fastball-family pitch; used their most-thrown pitch as a fallback baseline")

pitches = pitches.merge(primary_pitch_by_pitcher, on="player_name", how="left")

# Calculate each pitcher's average velocity/movement on their own
# primary pitch specifically.
primary_pitch_baseline = (
    pitches[pitches["pitch_type"] == pitches["primary_pitch_type"]]
    .groupby("player_name")
    .agg(
        primary_velocity=("release_speed", "mean"),
        primary_pfx_x=("pfx_x", "mean"),
        primary_pfx_z=("pfx_z", "mean")
    )
    .reset_index()
)

pitches = pitches.merge(primary_pitch_baseline, on="player_name", how="left")

pitches["velo_diff_from_primary"] = pitches["release_speed"] - pitches["primary_velocity"]
pitches["horizontal_break_diff_from_primary"] = pitches["pfx_x"] - pitches["primary_pfx_x"]
pitches["vertical_break_diff_from_primary"] = pitches["pfx_z"] - pitches["primary_pfx_z"]

rows_before = len(pitches)
pitches = pitches.dropna(
    subset=[
        "velo_diff_from_primary",
        "horizontal_break_diff_from_primary",
        "vertical_break_diff_from_primary"
    ]
)
print(f"Dropped {rows_before - len(pitches)} pitches with no valid primary-pitch baseline (should be near 0 now)")
pitches.to_csv("data/statcast_2023_2026_engineered.csv", index=False)

print(f"Final engineered dataset: {len(pitches)} rows")
print(pitches[["vertical_approach_angle", "horizontal_approach_angle", "velo_diff_from_primary"]].describe())