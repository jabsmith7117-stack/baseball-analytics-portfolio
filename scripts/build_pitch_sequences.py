import pandas as pd

raw = pd.read_csv("data/statcast_2023_2026_full.csv")

# Restrict to 2026 only, matching the rest of this project's scope.
pitches_2026 = raw[raw["game_year"] == 2026].copy()

# We only need columns relevant to sequencing: which at-bat, pitch
# order within it, the pitcher, the count BEFORE this pitch was
# thrown, the pitch type, and batter handedness (for splitting by
# platoon later).
sequence_columns = [
    "game_pk", "at_bat_number", "pitch_number",
    "pitcher", "player_name", "stand", "balls", "strikes", "pitch_type"
]

pitches_2026 = pitches_2026[sequence_columns].dropna(subset=["pitch_type", "balls", "strikes"])

# Sort so pitches within each at-bat are in true chronological order.
pitches_2026 = pitches_2026.sort_values(
    ["game_pk", "at_bat_number", "pitch_number"]
)

# Build a "next pitch" view: for each pitch, what count/pitch type
# came immediately after it, WITHIN THE SAME AT-BAT (critical - we
# don't want to accidentally link the last pitch of one at-bat to
# the first pitch of a completely different one).
pitches_2026["next_pitch_type"] = pitches_2026.groupby(
    ["game_pk", "at_bat_number"]
)["pitch_type"].shift(-1)

pitches_2026["next_balls"] = pitches_2026.groupby(
    ["game_pk", "at_bat_number"]
)["balls"].shift(-1)

pitches_2026["next_strikes"] = pitches_2026.groupby(
    ["game_pk", "at_bat_number"]
)["strikes"].shift(-1)

# Drop rows with no "next pitch" - these are the final pitch of each
# at-bat, which by definition has nothing to sequence into.
sequences = pitches_2026.dropna(
    subset=["next_pitch_type", "next_balls", "next_strikes"]
).copy()

sequences["current_count"] = (
    sequences["balls"].astype(int).astype(str) + "-" + sequences["strikes"].astype(int).astype(str)
)
sequences["next_count"] = (
    sequences["next_balls"].astype(int).astype(str) + "-" + sequences["next_strikes"].astype(int).astype(str)
)

sequences = sequences.rename(columns={"player_name": "pitcher_name"})

output_columns = [
    "pitcher", "pitcher_name", "stand",
    "current_count", "pitch_type",
    "next_count", "next_pitch_type"
]

sequences_final = sequences[output_columns]

sequences_final.to_csv("data/pitch_sequences_2026.csv", index=False)

print(f"Total real pitch-to-pitch transitions captured: {len(sequences_final)}")
print(f"Unique pitchers with sequence data: {sequences_final['pitcher'].nunique()}")
print("\nSample transitions:")
print(sequences_final.head(10))