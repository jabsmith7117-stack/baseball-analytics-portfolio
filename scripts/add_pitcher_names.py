import pandas as pd
from pybaseball import playerid_reverse_lookup

pitchers = pd.read_csv("data/pitcher_data_cleaned.csv")

unique_pitcher_ids = pitchers["pitcher"].unique().tolist()

print(f"Looking up names for {len(unique_pitcher_ids)} unique pitcher IDs...")

name_lookup = playerid_reverse_lookup(unique_pitcher_ids, key_type="mlbam")

name_lookup["pitcher_name"] = (
    name_lookup["name_first"].str.title() + " " + name_lookup["name_last"].str.title()
)

name_lookup = name_lookup[["key_mlbam", "pitcher_name"]].rename(
    columns={"key_mlbam": "pitcher"}
)

print(f"Names found for {len(name_lookup)} of {len(unique_pitcher_ids)} pitchers")

pitchers = pitchers.merge(name_lookup, on="pitcher", how="left")

missing_names = pitchers["pitcher_name"].isna().sum()
if missing_names > 0:
    print(f"Warning: {missing_names} rows have no matched name")

missing_ids = pitchers[pitchers["pitcher_name"].isna()]["pitcher"].unique()
print(f"Pitcher IDs with no matched name: {missing_ids}")

pitchers = pitchers.dropna(subset=["pitcher_name"])
print(f"Rows after dropping unmatched names: {len(pitchers)}")

# Save only now, after names are merged AND unmatched rows are dropped.
pitchers.to_csv("data/pitcher_data_with_names.csv", index=False)

print(f"\nSample of matched names:")
print(pitchers[["pitcher", "pitcher_name"]].drop_duplicates().head(10))