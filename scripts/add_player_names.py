import pandas as pd
from pybaseball import playerid_reverse_lookup

hitters = pd.read_csv("data/hitter_data_cleaned.csv")

unique_batter_ids = hitters["batter"].unique().tolist()

print(f"Looking up names for {len(unique_batter_ids)} unique batter IDs...")

name_lookup = playerid_reverse_lookup(unique_batter_ids, key_type="mlbam")

name_lookup["batter_name"] = (
    name_lookup["name_first"].str.title() + " " + name_lookup["name_last"].str.title()
)

name_lookup = name_lookup[["key_mlbam", "batter_name"]].rename(
    columns={"key_mlbam": "batter"}
)

print(f"Names found for {len(name_lookup)} of {len(unique_batter_ids)} batters")

hitters = hitters.merge(name_lookup, on="batter", how="left")

missing_names = hitters["batter_name"].isna().sum()
if missing_names > 0:
    print(f"Warning: {missing_names} rows have no matched name")

missing_ids = hitters[hitters["batter_name"].isna()]["batter"].unique()
print(f"Batter IDs with no matched name: {missing_ids}")

hitters = hitters.dropna(subset=["batter_name"])
print(f"Rows after dropping unmatched names: {len(hitters)}")

# Save only now, after names are merged AND unmatched rows are dropped.
hitters.to_csv("data/hitter_data_with_names.csv", index=False)

print(f"\nSample of matched names:")
print(hitters[["batter", "batter_name"]].drop_duplicates().head(10))