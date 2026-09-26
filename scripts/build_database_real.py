import sqlite3
import pandas as pd

connection = sqlite3.connect("sql/baseball_real.db")

with open("sql/schema_real.sql", "r") as schema_file:
    schema_sql = schema_file.read()

connection.executescript(schema_sql)

# --- Teams ---
hitter_core = pd.read_csv("data/hitter_core_stats.csv")
pitcher_core = pd.read_csv("data/pitcher_core_stats.csv")

all_teams = pd.concat([
    hitter_core["current_team"],
    pitcher_core["current_team"]
]).dropna().unique()

teams_df = pd.DataFrame({"team_abbr": all_teams})
teams_df.to_sql("teams", connection, if_exists="append", index=False)

# --- Hitters ---
hitters_df = hitter_core[["batter", "batter_name", "current_team", "bats"]].rename(
    columns={"batter": "batter_id", "current_team": "team_abbr"}
)
hitters_df.to_sql("hitters", connection, if_exists="append", index=False)

hitter_season_stats_df = hitter_core[[
    "batter", "total_pa", "at_bats", "hits", "home_runs",
    "batting_avg", "on_base_pct", "slugging_pct", "ops", "iso", "babip",
    "woba", "xwoba", "xba", "xwobacon", "k_rate", "bb_rate", "chase_rate",
    "whiff_rate", "hard_hit_rate", "avg_exit_velo", "avg_bat_speed",
    "avg_swing_length", "barrel_rate", "sweet_spot_rate",
    "in_zone_contact_rate", "out_zone_contact_rate", "pulled_flyball_rate",
    "fly_ball_rate", "line_drive_rate", "ground_ball_rate"
]].rename(columns={"batter": "batter_id"})
hitter_season_stats_df.to_sql("hitter_season_stats", connection, if_exists="append", index=False)

# --- Hitter platoon splits ---
hitter_platoon = pd.read_csv("data/hitter_platoon_splits.csv")
hitter_platoon_df = hitter_platoon[[
    "batter", "vs_throws", "performance_pa", "woba", "xwoba", "k_rate", "whiff_rate", "hard_hit_rate"
]].rename(columns={"batter": "batter_id"})
hitter_platoon_df.to_sql("hitter_platoon_splits", connection, if_exists="append", index=False)

# --- Hitter pitch-type splits ---
hitter_pitch_type = pd.read_csv("data/hitter_pitch_type_splits.csv")
hitter_pitch_type_df = hitter_pitch_type[[
    "batter", "pitch_type", "performance_pa", "woba", "xwoba", "whiff_rate", "hard_hit_rate"
]].rename(columns={"batter": "batter_id"})
hitter_pitch_type_df.to_sql("hitter_pitch_type_splits", connection, if_exists="append", index=False)

# --- Hitter zone splits ---
hitter_zone = pd.read_csv("data/hitter_zone_splits.csv")
hitter_zone_df = hitter_zone[[
    "batter", "zone", "performance_pa", "woba", "hard_hit_rate"
]].rename(columns={"batter": "batter_id"})
hitter_zone_df.to_sql("hitter_zone_splits", connection, if_exists="append", index=False)

# --- Pitchers ---
pitchers_df = pitcher_core[["pitcher", "pitcher_name", "current_team", "throws"]].rename(
    columns={"pitcher": "pitcher_id", "current_team": "team_abbr"}
)
pitchers_df.to_sql("pitchers", connection, if_exists="append", index=False)

pitcher_season_stats_df = pitcher_core[[
    "pitcher", "total_pa", "hits_allowed", "home_runs_allowed",
    "avg_against", "obp_against", "slg_against", "ops_against",
    "woba_against", "xwoba_against", "xba_against", "xwobacon_against",
    "k_rate", "bb_rate", "csw_rate", "chase_rate_induced",
    "whiff_rate_induced", "hard_hit_rate_allowed", "avg_exit_velo_allowed"
]].rename(columns={"pitcher": "pitcher_id"})
pitcher_season_stats_df.to_sql("pitcher_season_stats", connection, if_exists="append", index=False)

# --- Pitcher platoon splits ---
pitcher_platoon = pd.read_csv("data/pitcher_platoon_splits.csv")
pitcher_platoon_df = pitcher_platoon[[
    "pitcher", "vs_stand", "performance_pa", "woba_against", "k_rate", "whiff_rate_induced", "hard_hit_rate_allowed"
]].rename(columns={"pitcher": "pitcher_id"})
pitcher_platoon_df.to_sql("pitcher_platoon_splits", connection, if_exists="append", index=False)

# --- Pitcher pitch-type splits ---
pitcher_pitch_type = pd.read_csv("data/pitcher_pitch_type_splits.csv")
pitcher_pitch_type_df = pitcher_pitch_type[[
    "pitcher", "pitch_type", "usage_rate", "avg_velocity", "avg_spin_rate", "performance_pa", "woba_against", "whiff_rate_induced"
]].rename(columns={"pitcher": "pitcher_id"})
pitcher_pitch_type_df.to_sql("pitcher_pitch_type_splits", connection, if_exists="append", index=False)

connection.close()

print("Database built successfully.")
print("Tables created: teams, hitters, hitter_season_stats, hitter_platoon_splits,")
print("hitter_pitch_type_splits, hitter_zone_splits, pitchers, pitcher_season_stats,")
print("pitcher_platoon_splits, pitcher_pitch_type_splits")