import pandas as pd

# --- Hitters ---
hitter_tendency = pd.read_csv("data/hitter_data_tendency.csv")
hitter_names = pd.read_csv("data/hitter_data_with_names.csv")[["batter", "batter_name"]].drop_duplicates()

hitter_tendency = hitter_tendency.merge(hitter_names, on="batter", how="left")

rows_before = len(hitter_tendency)
hitter_tendency = hitter_tendency.dropna(subset=["batter_name"])
print(f"Hitter tendency rows after dropping unmatched names: {len(hitter_tendency)} (removed {rows_before - len(hitter_tendency)})")

hitter_tendency.to_csv("data/hitter_data_tendency_with_names.csv", index=False)

# --- Pitchers ---
pitcher_tendency = pd.read_csv("data/pitcher_data_tendency.csv")
pitcher_names = pd.read_csv("data/pitcher_data_with_names.csv")[["pitcher", "pitcher_name"]].drop_duplicates()

pitcher_tendency = pitcher_tendency.merge(pitcher_names, on="pitcher", how="left")

rows_before = len(pitcher_tendency)
pitcher_tendency = pitcher_tendency.dropna(subset=["pitcher_name"])
print(f"Pitcher tendency rows after dropping unmatched names: {len(pitcher_tendency)} (removed {rows_before - len(pitcher_tendency)})")

pitcher_tendency.to_csv("data/pitcher_data_tendency_with_names.csv", index=False)

print(f"\nFinal hitter tendency rows: {len(hitter_tendency)}, unique batters: {hitter_tendency['batter'].nunique()}")
print(f"Final pitcher tendency rows: {len(pitcher_tendency)}, unique pitchers: {pitcher_tendency['pitcher'].nunique()}")