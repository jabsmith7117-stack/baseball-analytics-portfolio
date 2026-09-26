import pandas as pd

performance = pd.read_csv("data/pitcher_data_with_names.csv")
tendency = pd.read_csv("data/pitcher_data_tendency_with_names.csv")

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
        return "Behind (Pitcher)"
    if strikes > balls:
        return "Ahead (Pitcher)"
    return "Even"


for df in [performance, tendency, performance_pa]:
    df["count_group"] = df.apply(lambda row: count_group(row["balls"], row["strikes"]), axis=1)


def calculate_tendency_stats(tendency_pitches):
    total_pitches = len(tendency_pitches)

    if total_pitches < 15:
        return None

    swings = tendency_pitches[tendency_pitches["is_swing"]]
    swing_rate_induced = len(swings) / total_pitches if total_pitches > 0 else None

    if len(tendency_pitches) > 0:
        pitch_type_counts = tendency_pitches["pitch_type"].value_counts()
        most_used_pitch = pitch_type_counts.idxmax()
        most_used_pitch_rate = pitch_type_counts.max() / total_pitches
    else:
        most_used_pitch = None
        most_used_pitch_rate = None

    return {
        "tendency_pitches": total_pitches,
        "most_used_pitch": most_used_pitch,
        "most_used_pitch_rate": round(most_used_pitch_rate, 3) if most_used_pitch_rate is not None else None,
        "swing_rate_induced": round(swing_rate_induced, 3) if swing_rate_induced is not None else None
    }


def calculate_performance_stats(perf_pitches, perf_pa):
    total_pa = len(perf_pa)

    if total_pa < 10:
        return None

    woba_against = (
        perf_pa["woba_value"].sum() / perf_pa["woba_denom"].sum()
        if perf_pa["woba_denom"].sum() > 0 else None
    )

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

    avg_against = total_hits / at_bats if at_bats > 0 else None
    slg_against = total_bases / at_bats if at_bats > 0 else None

    swings = perf_pitches[perf_pitches["is_swing"]]
    whiff_rate_induced = (
        swings["is_whiff"].sum() / len(swings)
        if len(swings) > 0 else None
    )

    balls_in_play = perf_pitches[perf_pitches["bb_type"].notna()]
    hard_hit_rate_allowed = (
        balls_in_play["is_hard_hit"].sum() / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )
    avg_exit_velo_allowed = balls_in_play["launch_speed"].mean()

    return {
        "performance_pa": total_pa,
        "hits_allowed": total_hits,
        "home_runs_allowed": home_runs,
        "avg_against": round(avg_against, 3) if avg_against is not None else None,
        "slg_against": round(slg_against, 3) if slg_against is not None else None,
        "woba_against": round(woba_against, 3) if woba_against is not None else None,
        "k_rate": round(k_rate, 3),
        "whiff_rate_induced": round(whiff_rate_induced, 3) if whiff_rate_induced is not None else None,
        "hard_hit_rate_allowed": round(hard_hit_rate_allowed, 3) if hard_hit_rate_allowed is not None else None,
        "avg_exit_velo_allowed": round(avg_exit_velo_allowed, 1) if pd.notna(avg_exit_velo_allowed) else None
    }


count_group_rows = []
raw_count_rows = []

for pitcher_id, pitcher_tendency_pitches in tendency.groupby("pitcher"):

    pitcher_name = pitcher_tendency_pitches["pitcher_name"].iloc[0]
    current_team = pitcher_tendency_pitches["current_team"].iloc[0]

    pitcher_perf_pitches_all = performance[performance["pitcher"] == pitcher_id]

    for stand in ["L", "R"]:
        stand_tendency_all = pitcher_tendency_pitches[pitcher_tendency_pitches["stand"] == stand]
        stand_perf_all = pitcher_perf_pitches_all[pitcher_perf_pitches_all["stand"] == stand]

        # Grouped
        for group in ["Ahead (Pitcher)", "Even", "Behind (Pitcher)", "Two-Strike"]:
            group_tendency = stand_tendency_all[stand_tendency_all["count_group"] == group]
            group_perf = stand_perf_all[stand_perf_all["count_group"] == group]
            group_perf_pa = performance_pa[
                (performance_pa["pitcher"] == pitcher_id)
                & (performance_pa["stand"] == stand)
                & (performance_pa["count_group"] == group)
            ]

            tendency_stats = calculate_tendency_stats(group_tendency)
            performance_stats = calculate_performance_stats(group_perf, group_perf_pa)

            if tendency_stats is None and performance_stats is None:
                continue

            row = {
                "pitcher": pitcher_id,
                "pitcher_name": pitcher_name,
                "current_team": current_team,
                "vs_stand": stand,
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
                raw_tendency = stand_tendency_all[
                    (stand_tendency_all["balls"] == balls) & (stand_tendency_all["strikes"] == strikes)
                ]
                raw_perf = stand_perf_all[
                    (stand_perf_all["balls"] == balls) & (stand_perf_all["strikes"] == strikes)
                ]
                raw_perf_pa = performance_pa[
                    (performance_pa["pitcher"] == pitcher_id)
                    & (performance_pa["stand"] == stand)
                    & (performance_pa["balls"] == balls)
                    & (performance_pa["strikes"] == strikes)
                ]

                tendency_stats = calculate_tendency_stats(raw_tendency)
                performance_stats = calculate_performance_stats(raw_perf, raw_perf_pa)

                if tendency_stats is None and performance_stats is None:
                    continue

                row = {
                    "pitcher": pitcher_id,
                    "pitcher_name": pitcher_name,
                    "current_team": current_team,
                    "vs_stand": stand,
                    "balls": balls,
                    "strikes": strikes,
                    "count": f"{balls}-{strikes}"
                }
                if tendency_stats:
                    row.update(tendency_stats)
                if performance_stats:
                    row.update(performance_stats)
                raw_count_rows.append(row)

count_group_df = pd.DataFrame(count_group_rows).sort_values(["pitcher_name", "vs_stand", "count_group"])
raw_count_df = pd.DataFrame(raw_count_rows).sort_values(["pitcher_name", "vs_stand", "balls", "strikes"])

count_group_df.to_csv("data/pitcher_count_group_splits.csv", index=False)
raw_count_df.to_csv("data/pitcher_raw_count_splits.csv", index=False)

print(f"Count-group rows: {len(count_group_df)}, unique pitchers: {count_group_df['pitcher'].nunique()}")
print(count_group_df.head(8))

print(f"\nRaw count rows: {len(raw_count_df)}, unique pitchers: {raw_count_df['pitcher'].nunique()}")
print(raw_count_df.head(8))