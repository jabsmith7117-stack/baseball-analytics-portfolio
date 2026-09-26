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
    "home_team",
    "away_team",
    "inning_topbot",
    "game_date",
    "arm_angle",
    "launch_speed_angle",
    "bat_speed",
    "swing_length",
    "hc_x",
    "hc_y",
]

hitters = data[columns_to_keep].copy()

rows_before = len(hitters)
hitters = hitters.dropna(subset=["type"])
print(f"Rows before cleaning: {rows_before}")
print(f"Rows after cleaning: {len(hitters)}")

# Tendency data uses a wider 2025-2026 window (more stable sample
# for usage rates, location tendencies, swing decisions), while
# performance/outcome stats elsewhere use 2026 only. This is a
# deliberate design choice: what a player tends to DO is more
# reliable over a longer window, while how well it's WORKING should
# reflect current-season reality.
rows_before_year_filter = len(hitters)
hitters = hitters[hitters["game_year"].isin([2025, 2026])]
print(f"Rows after restricting to 2025-2026: {len(hitters)} (removed {rows_before_year_filter - len(hitters)})")

hitters["batting_team"] = hitters.apply(
    lambda row: row["away_team"] if row["inning_topbot"] == "Top" else row["home_team"],
    axis=1
)

most_recent_team = (
    hitters.sort_values("game_date")
    .groupby("batter")
    .tail(1)
    [["batter", "batting_team", "game_year"]]
    .rename(columns={"batting_team": "current_team", "game_year": "most_recent_year"})
)

hitters = hitters.merge(most_recent_team, on="batter", how="left")

# Still only keep players who are ACTIVE in 2026 - we're widening
# the history window for their tendencies, not changing which
# players are included in the report.
rows_before_team_filter = len(hitters)
hitters = hitters[hitters["most_recent_year"] == 2026]
print(f"Rows after filtering to 2026-active batters: {len(hitters)} (removed {rows_before_team_filter - len(hitters)})")

print(f"Unique 2026-active batters: {hitters['batter'].nunique()}")

hitters.to_csv("data/hitter_data_tendency.csv", index=False)