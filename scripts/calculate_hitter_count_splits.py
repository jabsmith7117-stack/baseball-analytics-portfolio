import pandas as pd

performance = pd.read_csv("data/hitter_data_with_names.csv")
tendency = pd.read_csv("data/hitter_data_tendency_with_names.csv")

swing_descriptions = [
    "hit_into_play",
    "foul",
    "foul_tip",
    "swinging_strike",
    "swinging_strike_blocked"
]

whiff_descriptions = [
    "swinging_strike",
    "swinging_strike_blocked"
]

for df in [performance, tendency]:
    df["is_swing"] = df["description"].isin(swing_descriptions)
    df["is_whiff"] = df["description"].isin(whiff_descriptions)
    df["is_hard_hit"] = df["launch_speed"] >= 95

performance_pa = performance.dropna(subset=["woba_denom"])


def count_group(balls, strikes):
    if strikes == 2:
        return "Two-Strike"
    if balls > strikes:
        return "Ahead (Hitter)"
    if strikes > balls:
        return "Behind (Hitter)"
    return "Even"


for df in [performance, tendency, performance_pa]:
    df["count_group"] = df.apply(lambda row: count_group(row["balls"], row["strikes"]), axis=1)


def calculate_tendency_stats(tendency_pitches, total_pitches_all):
    total_pitches = len(tendency_pitches)

    if total_pitches < 15:
        return None

    swings = tendency_pitches[tendency_pitches["is_swing"]]
    swing_rate = len(swings) / total_pitches if total_pitches > 0 else None

    pct_pitches_seen = (
        total_pitches / total_pitches_all if total_pitches_all > 0 else None
    )

    return {
        "tendency_pitches_seen": total_pitches,
        "pct_of_pitches_seen": round(pct_pitches_seen, 3) if pct_pitches_seen is not None else None,
        "swing_rate": round(swing_rate, 3) if swing_rate is not None else None
    }


def calculate_performance_stats(perf_pitches, perf_pa):
    total_pa = len(perf_pa)

    if total_pa < 10:
        return None

    woba = (
        perf_pa["woba_value"].sum() / perf_pa["woba_denom"].sum()
        if perf_pa["woba_denom"].sum() > 0 else None
    )
    xwoba = perf_pa["estimated_woba_using_speedangle"].mean()

    k_rate = (perf_pa["events"] == "strikeout").sum() / total_pa

    singles = (perf_pa["events"] == "single").sum()
    doubles = (perf_pa["events"] == "double").sum()
    triples = (perf_pa["events"] == "triple").sum()
    home_runs = (perf_pa["events"] == "home_run").sum()
    walks = (perf_pa["events"] == "walk").sum()
    hit_by_pitch = (perf_pa["events"] == "hit_by_pitch").sum()
    sac_fly = (perf_pa["events"] == "sac_fly").sum()
    sac_bunt = (perf_pa["events"] == "sac_bunt").sum()

    total_hits = singles + doubles + triples + home_runs
    total_bases = singles + (2 * doubles) + (3 * triples) + (4 * home_runs)
    at_bats = total_pa - walks - hit_by_pitch - sac_fly - sac_bunt

    batting_avg = total_hits / at_bats if at_bats > 0 else None
    on_base_pct = (
        (total_hits + walks + hit_by_pitch) /
        (at_bats + walks + hit_by_pitch + sac_fly)
        if (at_bats + walks + hit_by_pitch + sac_fly) > 0 else None
    )
    slugging_pct = total_bases / at_bats if at_bats > 0 else None
    ops = (
        on_base_pct + slugging_pct
        if on_base_pct is not None and slugging_pct is not None else None
    )

    swings = perf_pitches[perf_pitches["is_swing"]]
    whiff_rate = (
        swings["is_whiff"].sum() / len(swings)
        if len(swings) > 0 else None
    )

    balls_in_play = perf_pitches[perf_pitches["bb_type"].notna()]
    hard_hit_rate = (
        balls_in_play["is_hard_hit"].sum() / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )
    avg_exit_velo = balls_in_play["launch_speed"].mean()

    return {
        "performance_pa": total_pa,
        "hits": total_hits,
        "home_runs": home_runs,
        "batting_avg": round(batting_avg, 3) if batting_avg is not None else None,
        "on_base_pct": round(on_base_pct, 3) if on_base_pct is not None else None,
        "slugging_pct": round(slugging_pct, 3) if slugging_pct is not None else None,
        "ops": round(ops, 3) if ops is not None else None,
        "woba": round(woba, 3) if woba is not None else None,
        "xwoba": round(xwoba, 3) if pd.notna(xwoba) else None,
        "k_rate": round(k_rate, 3),
        "whiff_rate": round(whiff_rate, 3) if whiff_rate is not None else None,
        "hard_hit_rate": round(hard_hit_rate, 3) if hard_hit_rate is not None else None,
        "avg_exit_velo": round(avg_exit_velo, 1) if pd.notna(avg_exit_velo) else None
    }


count_group_rows = []
raw_count_rows = []

for batter_id, batter_tendency_pitches in tendency.groupby("batter"):

    batter_name = batter_tendency_pitches["batter_name"].iloc[0]
    current_team = batter_tendency_pitches["current_team"].iloc[0]
    total_tendency_pitches = len(batter_tendency_pitches)

    batter_perf_pitches_all = performance[performance["batter"] == batter_id]

    # Grouped
    for group in ["Ahead (Hitter)", "Even", "Behind (Hitter)", "Two-Strike"]:
        group_tendency = batter_tendency_pitches[batter_tendency_pitches["count_group"] == group]
        group_perf = batter_perf_pitches_all[batter_perf_pitches_all["count_group"] == group]
        group_perf_pa = performance_pa[
            (performance_pa["batter"] == batter_id) & (performance_pa["count_group"] == group)
        ]

        tendency_stats = calculate_tendency_stats(group_tendency, total_tendency_pitches)
        performance_stats = calculate_performance_stats(group_perf, group_perf_pa)

        if tendency_stats is None and performance_stats is None:
            continue

        row = {
            "batter": batter_id,
            "batter_name": batter_name,
            "current_team": current_team,
            "count_group": group
        }
        if tendency_stats:
            row.update(tendency_stats)
        if performance_stats:
            row.update(performance_stats)
        count_group_rows.append(row)

    # Raw
    for balls in range(0, 4):
        for strikes in range(0, 3):
            raw_tendency = batter_tendency_pitches[
                (batter_tendency_pitches["balls"] == balls) & (batter_tendency_pitches["strikes"] == strikes)
            ]
            raw_perf = batter_perf_pitches_all[
                (batter_perf_pitches_all["balls"] == balls) & (batter_perf_pitches_all["strikes"] == strikes)
            ]
            raw_perf_pa = performance_pa[
                (performance_pa["batter"] == batter_id)
                & (performance_pa["balls"] == balls)
                & (performance_pa["strikes"] == strikes)
            ]

            tendency_stats = calculate_tendency_stats(raw_tendency, total_tendency_pitches)
            performance_stats = calculate_performance_stats(raw_perf, raw_perf_pa)

            if tendency_stats is None and performance_stats is None:
                continue

            row = {
                "batter": batter_id,
                "batter_name": batter_name,
                "current_team": current_team,
                "balls": balls,
                "strikes": strikes,
                "count": f"{balls}-{strikes}"
            }
            if tendency_stats:
                row.update(tendency_stats)
            if performance_stats:
                row.update(performance_stats)
            raw_count_rows.append(row)

count_group_df = pd.DataFrame(count_group_rows).sort_values(["batter_name", "count_group"])
raw_count_df = pd.DataFrame(raw_count_rows).sort_values(["batter_name", "balls", "strikes"])

count_group_df.to_csv("data/hitter_count_group_splits.csv", index=False)
raw_count_df.to_csv("data/hitter_raw_count_splits.csv", index=False)

print(f"Count-group rows: {len(count_group_df)}, unique batters: {count_group_df['batter'].nunique()}")
print(count_group_df.head(8))

print(f"\nRaw count rows: {len(raw_count_df)}, unique batters: {raw_count_df['batter'].nunique()}")
print(raw_count_df.head(8))