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
    "launch_speed_angle",
    "bb_type",
    "release_speed",
    "home_team",
    "away_team",
    "inning_topbot",
    "game_date",
    "arm_angle",
    "bat_speed",
    "swing_length",
    "hc_x",
    "hc_y"
]

hitters = data[columns_to_keep].copy()

rows_before = len(hitters)
hitters = hitters.dropna(subset=["type"])
print(f"Rows before cleaning: {rows_before}")
print(f"Rows after cleaning: {len(hitters)}")

print(f"\nUnique batters: {hitters['batter'].nunique()}")
print(f"Date range: {hitters['game_year'].min()} to {hitters['game_year'].max()}")

# Restrict to pitches actually thrown during the 2026 season, per
# updated scope - the report should reflect current-season reality
# only, not performance from prior years.
rows_before_year_filter = len(hitters)
hitters = hitters[hitters["game_year"] == 2026]
print(f"Rows after restricting to 2026 season only: {len(hitters)} (removed {rows_before_year_filter - len(hitters)})")

# Determine each batter's team on this specific pitch. In Statcast,
# the team batting is the away team when inning_topbot is "Top",
# and the home team when it's "Bot".
hitters["batting_team"] = hitters.apply(
    lambda row: row["away_team"] if row["inning_topbot"] == "Top" else row["home_team"],
    axis=1
)

# For each batter, find their most recent team as of their latest
# game in the dataset - this reflects their CURRENT team, correctly
# handling any in-season trades.
most_recent_team = (
    hitters.sort_values("game_date")
    .groupby("batter")
    .tail(1)
    [["batter", "batting_team", "game_year"]]
    .rename(columns={"batting_team": "current_team", "game_year": "most_recent_year"})
)

hitters = hitters.merge(most_recent_team, on="batter", how="left")

# Only keep batters whose most recent appearance was in the 2026
# season - this scopes the report to currently active, rosterable
# players rather than anyone who appeared at any point since 2023.
rows_before_team_filter = len(hitters)
hitters = hitters[hitters["most_recent_year"] == 2026]
print(f"Rows after filtering to 2026-active batters: {len(hitters)} (removed {rows_before_team_filter - len(hitters)})")

print(f"Unique 2026-active batters: {hitters['batter'].nunique()}")

# Save only now, after all cleaning and filtering is complete.
hitters.to_csv("data/hitter_data_cleaned.csv", index=False)