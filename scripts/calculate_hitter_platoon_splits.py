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
    df["is_chase"] = df["is_swing"] & (df["zone"] >= 11)
    df["is_out_of_zone"] = df["zone"] >= 11
    df["is_hard_hit"] = df["launch_speed"] >= 95

performance_pa = performance.dropna(subset=["woba_denom"])


def calculate_tendency_stats(tendency_pitches):
    """Usage/decision-based stats, from the wider 2025-2026 window."""
    total_pitches = len(tendency_pitches)

    if total_pitches < 15:
        return None

    out_of_zone_pitches = tendency_pitches[tendency_pitches["is_out_of_zone"]]
    chase_rate = (
        out_of_zone_pitches["is_chase"].sum() / len(out_of_zone_pitches)
        if len(out_of_zone_pitches) > 0 else None
    )

    swings = tendency_pitches[tendency_pitches["is_swing"]]
    swing_rate = len(swings) / total_pitches if total_pitches > 0 else None

    return {
        "tendency_pitches_seen": total_pitches,
        "swing_rate": round(swing_rate, 3) if swing_rate is not None else None,
        "chase_rate": round(chase_rate, 3) if chase_rate is not None else None
    }


def calculate_performance_stats(perf_pitches, perf_pa):
    """Outcome-based stats, from the current 2026-only window."""
    total_pa = len(perf_pa)

    if total_pa < 10:
        return None

    woba = perf_pa["woba_value"].sum() / perf_pa["woba_denom"].sum()
    xwoba = perf_pa["estimated_woba_using_speedangle"].mean()

    k_rate = (perf_pa["events"] == "strikeout").sum() / total_pa
    bb_rate = (perf_pa["events"] == "walk").sum() / total_pa

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
        "batting_avg": round(batting_avg, 3) if batting_avg is not None else None,
        "on_base_pct": round(on_base_pct, 3) if on_base_pct is not None else None,
        "slugging_pct": round(slugging_pct, 3) if slugging_pct is not None else None,
        "ops": round(ops, 3) if ops is not None else None,
        "woba": round(woba, 3),
        "xwoba": round(xwoba, 3) if pd.notna(xwoba) else None,
        "k_rate": round(k_rate, 3),
        "bb_rate": round(bb_rate, 3),
        "whiff_rate": round(whiff_rate, 3) if whiff_rate is not None else None,
        "hard_hit_rate": round(hard_hit_rate, 3) if hard_hit_rate is not None else None,
        "avg_exit_velo": round(avg_exit_velo, 1) if pd.notna(avg_exit_velo) else None
    }


platoon_rows = []

for batter_id, batter_tendency_pitches in tendency.groupby("batter"):

    batter_name = batter_tendency_pitches["batter_name"].iloc[0]
    current_team = batter_tendency_pitches["current_team"].iloc[0]

    batter_perf_pitches_all = performance[performance["batter"] == batter_id]

    for stand in ["L", "R"]:
        vs_stand_tendency = batter_tendency_pitches[batter_tendency_pitches["p_throws"] == stand]
        vs_stand_perf = batter_perf_pitches_all[batter_perf_pitches_all["p_throws"] == stand]
        vs_stand_perf_pa = performance_pa[
            (performance_pa["batter"] == batter_id) & (performance_pa["p_throws"] == stand)
        ]

        tendency_stats = calculate_tendency_stats(vs_stand_tendency)
        performance_stats = calculate_performance_stats(vs_stand_perf, vs_stand_perf_pa)

        if tendency_stats is None and performance_stats is None:
            continue

        row = {
            "batter": batter_id,
            "batter_name": batter_name,
            "current_team": current_team,
            "vs_throws": stand
        }
        if tendency_stats:
            row.update(tendency_stats)
        if performance_stats:
            row.update(performance_stats)

        platoon_rows.append(row)

platoon_df = pd.DataFrame(platoon_rows)

platoon_df = platoon_df.sort_values(["batter_name", "vs_throws"])

platoon_df.to_csv("data/hitter_platoon_splits.csv", index=False)

print(f"Total batter/handedness rows: {len(platoon_df)}")
print(f"Unique batters with at least one split: {platoon_df['batter'].nunique()}")
print(platoon_df.head(10))