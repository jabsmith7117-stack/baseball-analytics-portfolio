import pandas as pd

sequences = pd.read_csv("data/pitch_sequences_2026.csv")

MIN_SAMPLE = 1

# --- Table 1: What pitch does this pitcher tend to throw AT this count? ---
pitch_choice_rows = []

group_cols_1 = ["pitcher", "pitcher_name", "stand", "current_count"]

for group_keys, group_df in sequences.groupby(group_cols_1):
    pitcher, pitcher_name, stand, current_count = group_keys
    total_at_count = len(group_df)

    if total_at_count < MIN_SAMPLE:
        continue

    pitch_counts = group_df["pitch_type"].value_counts()

    for pitch_type, count in pitch_counts.items():
        pitch_choice_rows.append({
            "pitcher": pitcher,
            "pitcher_name": pitcher_name,
            "vs_stand": stand,
            "count": current_count,
            "pitch_type": pitch_type,
            "times_thrown": count,
            "total_pitches_at_count": total_at_count,
            "pitch_rate": round(count / total_at_count, 3)
        })

pitch_choice_df = pd.DataFrame(pitch_choice_rows)
pitch_choice_df = pitch_choice_df.sort_values(
    ["pitcher_name", "vs_stand", "count", "pitch_rate"],
    ascending=[True, True, True, False]
)
pitch_choice_df.to_csv("data/sequencing_pitch_choice.csv", index=False)

# --- Table 2: Given this pitch was thrown, what count resulted? ---
outcome_rows = []

group_cols_2 = ["pitcher", "pitcher_name", "stand", "current_count", "pitch_type"]

for group_keys, group_df in sequences.groupby(group_cols_2):
    pitcher, pitcher_name, stand, current_count, pitch_type = group_keys
    total_thrown = len(group_df)

    if total_thrown < MIN_SAMPLE:
        continue

    outcome_counts = group_df["next_count"].value_counts()

    for next_count, count in outcome_counts.items():
        outcome_rows.append({
            "pitcher": pitcher,
            "pitcher_name": pitcher_name,
            "vs_stand": stand,
            "count": current_count,
            "pitch_type": pitch_type,
            "resulting_count": next_count,
            "times_occurred": count,
            "total_this_pitch_at_count": total_thrown,
            "outcome_rate": round(count / total_thrown, 3)
        })

outcome_df = pd.DataFrame(outcome_rows)
outcome_df = outcome_df.sort_values(
    ["pitcher_name", "vs_stand", "count", "pitch_type", "outcome_rate"],
    ascending=[True, True, True, True, False]
)
outcome_df.to_csv("data/sequencing_count_outcomes.csv", index=False)

print(f"Pitch-choice table rows: {len(pitch_choice_df)}")
print(f"Count-outcome table rows: {len(outcome_df)}")

print("\nSample - what does Littell throw at 0-0 vs lefties:")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(
    pitch_choice_df[
        (pitch_choice_df["pitcher_name"] == "Littell, Zack")
        & (pitch_choice_df["vs_stand"] == "L")
        & (pitch_choice_df["count"] == "0-0")
    ]
)

print("\nSample - if he throws a 0-0 fastball to a lefty, what count results:")
print(
    outcome_df[
        (outcome_df["pitcher_name"] == "Littell, Zack")
        & (outcome_df["vs_stand"] == "L")
        & (outcome_df["count"] == "0-0")
        & (outcome_df["pitch_type"] == "FF")
    ]
)