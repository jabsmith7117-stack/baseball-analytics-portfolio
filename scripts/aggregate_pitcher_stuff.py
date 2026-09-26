import pandas as pd

pitches = pd.read_csv("data/statcast_2025_scored.csv")

# Group by pitcher and pitch type, then calculate averages within
# each group. Note: player_name in Statcast data is "Last, First" -
# we'll clean that up for display purposes.
pitcher_pitch_summary = (
    pitches.groupby(["player_name", "pitch_type"])
    .agg(
        pitch_count=("stuff_plus", "count"),
        avg_stuff_plus=("stuff_plus", "mean"),
        avg_velocity=("release_speed", "mean"),
        avg_spin_rate=("release_spin_rate", "mean")
    )
    .reset_index()
)

pitcher_pitch_summary["avg_stuff_plus"] = pitcher_pitch_summary["avg_stuff_plus"].round(1)
pitcher_pitch_summary["avg_velocity"] = pitcher_pitch_summary["avg_velocity"].round(1)
pitcher_pitch_summary["avg_spin_rate"] = pitcher_pitch_summary["avg_spin_rate"].round(0)

# Only keep pitcher/pitch-type combinations with a meaningful sample
# size. A pitcher who threw a slider 3 times all year shouldn't get
# a displayed average - too small a sample to mean anything.
pitcher_pitch_summary = pitcher_pitch_summary[
    pitcher_pitch_summary["pitch_count"] >= 20
]

# Calculate each pitcher's total pitch count across all pitch types,
# so we can calculate usage rate (what % of their pitches is this
# pitch type).
pitcher_totals = (
    pitches.groupby("player_name")["stuff_plus"]
    .count()
    .reset_index()
    .rename(columns={"stuff_plus": "total_pitches"})
)

pitcher_pitch_summary = pitcher_pitch_summary.merge(
    pitcher_totals, on="player_name"
)

pitcher_pitch_summary["usage_rate"] = (
    pitcher_pitch_summary["pitch_count"] / pitcher_pitch_summary["total_pitches"]
).round(3)

pitcher_pitch_summary = pitcher_pitch_summary.sort_values(
    ["player_name", "usage_rate"], ascending=[True, False]
)

pitcher_pitch_summary.to_csv("data/pitcher_stuff_summary.csv", index=False)

print(f"Total pitcher/pitch-type rows: {len(pitcher_pitch_summary)}")
print(f"Unique pitchers: {pitcher_pitch_summary['player_name'].nunique()}")
print(pitcher_pitch_summary.head(10))