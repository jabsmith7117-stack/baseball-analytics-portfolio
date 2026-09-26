import pandas as pd

data = pd.read_csv("data/statcast_2023_2026_full.csv")

columns_to_keep = [
    "game_year",
    "player_name",
    "batter",
    "pitcher",
    "stand",
    "p_throws",
    "pitch_type",
    "balls",
    "strikes",
    "zone",
    "plate_x",
    "plate_z",
    "description",
    "events",
    "type",
    "woba_value",
    "woba_denom",
    "estimated_woba_using_speedangle",
    "estimated_ba_using_speedangle",
    "estimated_slg_using_speedangle",
    "launch_speed",
    "launch_angle",
    "bb_type",
    "release_speed",
    "release_spin_rate",
    "arm_angle",
    "home_team",
    "away_team",
    "inning_topbot",
    "game_date"
]

pitchers = data[columns_to_keep].copy()

rows_before = len(pitchers)
pitchers = pitchers.dropna(subset=["type"])
print(f"Rows before cleaning: {rows_before}")
print(f"Rows after cleaning: {len(pitchers)}")

# Restrict to pitches actually thrown during the 2026 season, per
# updated scope - the report should reflect current-season reality
# only, not performance from prior years.
rows_before_year_filter = len(pitchers)
pitchers = pitchers[pitchers["game_year"] == 2026]
print(f"Rows after restricting to 2026 season only: {len(pitchers)} (removed {rows_before_year_filter - len(pitchers)})")

# Determine each pitcher's team on this specific pitch. The pitching
# team is the home team when inning_topbot is "Top" (home team is
# pitching while the away team bats), and the away team when "Bot".
pitchers["pitching_team"] = pitchers.apply(
    lambda row: row["home_team"] if row["inning_topbot"] == "Top" else row["away_team"],
    axis=1
)

most_recent_team = (
    pitchers.sort_values("game_date")
    .groupby("pitcher")
    .tail(1)
    [["pitcher", "pitching_team", "game_year"]]
    .rename(columns={"pitching_team": "current_team", "game_year": "most_recent_year"})
)

pitchers = pitchers.merge(most_recent_team, on="pitcher", how="left")

rows_before_team_filter = len(pitchers)
pitchers = pitchers[pitchers["most_recent_year"] == 2026]
print(f"Rows after filtering to 2026-active pitchers: {len(pitchers)} (removed {rows_before_team_filter - len(pitchers)})")

print(f"Unique 2026-active pitchers: {pitchers['pitcher'].nunique()}")

pitchers.to_csv("data/pitcher_data_cleaned.csv", index=False)