import pandas as pd

sequences = pd.read_csv("data/pitch_sequences_2026.csv")

MIN_TRANSITION_SAMPLE = 5

transition_rows = []

# Group by every real starting point: this pitcher, this batter
# handedness, this count, this pitch they just threw.
group_cols = ["pitcher", "pitcher_name", "stand", "current_count", "pitch_type"]

for group_keys, group_df in sequences.groupby(group_cols):
    pitcher, pitcher_name, stand, current_count, pitch_type = group_keys

    total_from_here = len(group_df)

    if total_from_here < MIN_TRANSITION_SAMPLE:
        continue

    next_pitch_counts = group_df["next_pitch_type"].value_counts()

    for next_pitch_type, count in next_pitch_counts.items():
        transition_rows.append({
            "pitcher": pitcher,
            "pitcher_name": pitcher_name,
            "vs_stand": stand,
            "current_count": current_count,
            "pitch_thrown": pitch_type,
            "next_pitch_type": next_pitch_type,
            "times_thrown_next": count,
            "total_from_this_point": total_from_here,
            "next_pitch_rate": round(count / total_from_here, 3)
        })

transitions_df = pd.DataFrame(transition_rows)

transitions_df = transitions_df.sort_values(
    ["pitcher_name", "vs_stand", "current_count", "pitch_thrown", "next_pitch_rate"],
    ascending=[True, True, True, True, False]
)

transitions_df.to_csv("data/pitch_transition_table.csv", index=False)

print(f"Total transition rows: {len(transitions_df)}")
print(f"Unique pitchers with at least one transition: {transitions_df['pitcher'].nunique()}")
print(f"\nSample transitions for Littell, Zack:")
sample = transitions_df[transitions_df["pitcher_name"] == "Littell, Zack"]
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(sample.head(15))