import pandas as pd

performance = pd.read_csv("data/hitter_data_with_names.csv")
tendency = pd.read_csv("data/hitter_data_tendency_with_names.csv")

swing_descriptions = [
    "hit_into_play", "foul", "foul_tip",
    "swinging_strike", "swinging_strike_blocked"
]
whiff_descriptions = ["swinging_strike", "swinging_strike_blocked"]

for df in [performance, tendency]:
    df["is_swing"] = df["description"].isin(swing_descriptions)
    df["is_whiff"] = df["description"].isin(whiff_descriptions)
    df["is_hard_hit"] = df["launch_speed"] >= 95

performance_pa = performance.dropna(subset=["woba_denom"])

modelable_pitch_types = ["FF", "SI", "SL", "CH", "ST", "FC", "CU", "FS", "KC"]
all_counts = [(b, s) for b in range(4) for s in range(3)]
pitcher_hands = ["L", "R"]

rows = []

for batter_id, batter_tendency_pitches in tendency.groupby("batter"):

    batter_name = batter_tendency_pitches["batter_name"].iloc[0]
    batter_perf_all = performance[performance["batter"] == batter_id]

    for ptype in modelable_pitch_types:
        for balls, strikes in all_counts:
            for p_throws in pitcher_hands:

                cell_tendency = batter_tendency_pitches[
                    (batter_tendency_pitches["pitch_type"] == ptype)
                    & (batter_tendency_pitches["balls"] == balls)
                    & (batter_tendency_pitches["strikes"] == strikes)
                    & (batter_tendency_pitches["p_throws"] == p_throws)
                ]
                cell_perf = batter_perf_all[
                    (batter_perf_all["pitch_type"] == ptype)
                    & (batter_perf_all["balls"] == balls)
                    & (batter_perf_all["strikes"] == strikes)
                    & (batter_perf_all["p_throws"] == p_throws)
                ]
                cell_perf_pa = performance_pa[
                    (performance_pa["batter"] == batter_id)
                    & (performance_pa["pitch_type"] == ptype)
                    & (performance_pa["balls"] == balls)
                    & (performance_pa["strikes"] == strikes)
                    & (performance_pa["p_throws"] == p_throws)
                ]

                tendency_pitches_seen = len(cell_tendency)
                performance_pa_count = len(cell_perf_pa)

                if tendency_pitches_seen == 0 and performance_pa_count == 0:
                    continue

                woba = None
                whiff_rate = None
                if performance_pa_count >= 1:
                    denom = cell_perf_pa["woba_denom"].sum()
                    if denom > 0:
                        woba = round(cell_perf_pa["woba_value"].sum() / denom, 3)

                swings = cell_perf[cell_perf["is_swing"]]
                if len(swings) >= 1:
                    whiff_rate = round(swings["is_whiff"].sum() / len(swings), 3)

                rows.append({
                    "batter": batter_id,
                    "batter_name": batter_name,
                    "pitch_type": ptype,
                    "count": f"{balls}-{strikes}",
                    "vs_throws": p_throws,
                    "tendency_pitches_seen": tendency_pitches_seen,
                    "performance_pa": performance_pa_count,
                    "woba": woba,
                    "whiff_rate": whiff_rate
                })

result_df = pd.DataFrame(rows)
result_df = result_df.sort_values(["batter_name", "pitch_type", "count", "vs_throws"])
result_df.to_csv("data/hitter_pitch_type_by_count.csv", index=False)

print(f"Total rows: {len(result_df)}")
print(f"Rows with a real woba value: {result_df['woba'].notna().sum()}")
print(f"Rows with tendency data only (no woba): {result_df['woba'].isna().sum()}")