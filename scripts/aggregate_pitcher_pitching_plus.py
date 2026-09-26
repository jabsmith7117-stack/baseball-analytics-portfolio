import pandas as pd

pitches = pd.read_csv("data/statcast_2025_pitching_plus_scored.csv")

pitcher_pitch_summary = (
    pitches.groupby(["player_name", "pitch_type"])
    .agg(
        pitch_count=("pitching_plus", "count"),
        avg_pitching_plus=("pitching_plus", "mean")
    )
    .reset_index()
)

pitcher_pitch_summary["avg_pitching_plus"] = pitcher_pitch_summary["avg_pitching_plus"].round(1)

pitcher_pitch_summary = pitcher_pitch_summary[
    pitcher_pitch_summary["pitch_count"] >= 20
]

pitcher_pitch_summary.to_csv("data/pitcher_pitching_plus_summary.csv", index=False)

print(f"Total rows: {len(pitcher_pitch_summary)}")
print(f"Unique pitchers: {pitcher_pitch_summary['player_name'].nunique()}")