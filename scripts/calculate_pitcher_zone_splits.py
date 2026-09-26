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

all_zones = list(range(1, 10)) + list(range(11, 15))


def calculate_tendency_stats(tendency_pitches, total_pitches_all_zones):
    total_pitches = len(tendency_pitches)

    if total_pitches < 15:
        return None

    swings = tendency_pitches[tendency_pitches["is_swing"]]
    swing_rate_induced = len(swings) / total_pitches if total_pitches > 0 else None

    location_usage_rate = (
        total_pitches / total_pitches_all_zones if total_pitches_all_zones > 0 else None
    )

    return {
        "tendency_pitches": total_pitches,
        "location_usage_rate": round(location_usage_rate, 3) if location_usage_rate is not None else None,
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


zone_rows = []

for pitcher_id, pitcher_tendency_pitches in tendency.groupby("pitcher"):

    pitcher_name = pitcher_tendency_pitches["pitcher_name"].iloc[0]
    current_team = pitcher_tendency_pitches["current_team"].iloc[0]
    total_tendency_pitches = len(pitcher_tendency_pitches)

    pitcher_perf_pitches_all = performance[performance["pitcher"] == pitcher_id]

    for zone in all_zones:
        zone_tendency = pitcher_tendency_pitches[pitcher_tendency_pitches["zone"] == zone]
        zone_perf = pitcher_perf_pitches_all[pitcher_perf_pitches_all["zone"] == zone]
        zone_perf_pa = performance_pa[
            (performance_pa["pitcher"] == pitcher_id) & (performance_pa["zone"] == zone)
        ]

        tendency_stats = calculate_tendency_stats(zone_tendency, total_tendency_pitches)
        performance_stats = calculate_performance_stats(zone_perf, zone_perf_pa)

        if tendency_stats is None and performance_stats is None:
            continue

        row = {
            "pitcher": pitcher_id,
            "pitcher_name": pitcher_name,
            "current_team": current_team,
            "zone": zone,
            "in_strike_zone": zone <= 9
        }
        if tendency_stats:
            row.update(tendency_stats)
        if performance_stats:
            row.update(performance_stats)

        zone_rows.append(row)

zone_df = pd.DataFrame(zone_rows)

zone_df = zone_df.sort_values(["pitcher_name", "zone"])

zone_df.to_csv("data/pitcher_zone_splits.csv", index=False)

print(f"Total pitcher/zone rows: {len(zone_df)}")
print(f"Unique pitchers with at least one zone split: {zone_df['pitcher'].nunique()}")
print(zone_df.head(15))