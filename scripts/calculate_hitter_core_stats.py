import pandas as pd
import math

pitches = pd.read_csv("data/hitter_data_with_names.csv")

swing_descriptions = [
    "hit_into_play", "foul", "foul_tip",
    "swinging_strike", "swinging_strike_blocked"
]
whiff_descriptions = ["swinging_strike", "swinging_strike_blocked"]

pitches["is_swing"] = pitches["description"].isin(swing_descriptions)
pitches["is_whiff"] = pitches["description"].isin(whiff_descriptions)
pitches["is_chase"] = pitches["is_swing"] & (pitches["zone"] >= 11)
pitches["is_out_of_zone"] = pitches["zone"] >= 11
pitches["is_hard_hit"] = pitches["launch_speed"] >= 95
pitches["is_in_zone"] = pitches["zone"] <= 9
pitches["is_contact"] = pitches["is_swing"] & (~pitches["is_whiff"])
pitches["is_barrel"] = pitches["launch_speed_angle"] == 6
pitches["is_sweet_spot"] = (pitches["launch_angle"] >= 8) & (pitches["launch_angle"] <= 32)
pitches["is_fly_ball"] = pitches["bb_type"] == "fly_ball"
pitches["is_line_drive"] = pitches["bb_type"] == "line_drive"
pitches["is_ground_ball"] = pitches["bb_type"] == "ground_ball"

pitches["spray_angle"] = None
valid_coords = pitches["hc_x"].notna() & pitches["hc_y"].notna()
pitches.loc[valid_coords, "spray_angle"] = (
    (pitches.loc[valid_coords, "hc_x"] - 125.42)
    / (198.27 - pitches.loc[valid_coords, "hc_y"])
).apply(lambda x: math.degrees(math.atan(x)))

pitches["is_pulled"] = None
pitches.loc[valid_coords & (pitches["stand"] == "R"), "is_pulled"] = (
    pitches.loc[valid_coords & (pitches["stand"] == "R"), "spray_angle"] < 0
)
pitches.loc[valid_coords & (pitches["stand"] == "L"), "is_pulled"] = (
    pitches.loc[valid_coords & (pitches["stand"] == "L"), "spray_angle"] > 0
)

pa_ending = pitches.dropna(subset=["woba_denom"])

core_stats = []

for batter_id, batter_pitches in pitches.groupby("batter"):

    batter_name = batter_pitches["batter_name"].iloc[0]
    current_team = batter_pitches["current_team"].iloc[0]
    side_counts = batter_pitches["stand"].value_counts()
    # Statcast stand records the side used for each pitch, not the batter's
    # season-long handedness. Require repeated appearances on both sides to
    # guard against an isolated tracking error.
    bats = (
        "S" if side_counts.get("L", 0) >= 10 and side_counts.get("R", 0) >= 10
        else side_counts.idxmax() if not side_counts.empty else None
    )

    batter_pa = pa_ending[pa_ending["batter"] == batter_id]

    total_pitches = len(batter_pitches)
    total_pa = len(batter_pa)

    if total_pa < 20:
        continue

    woba = batter_pa["woba_value"].sum() / batter_pa["woba_denom"].sum()
    xwoba = batter_pa["estimated_woba_using_speedangle"].mean()
    xba = batter_pa["estimated_ba_using_speedangle"].mean()

    contact_pa = batter_pa[batter_pa["bb_type"].notna()]
    xwobacon = (
        contact_pa["estimated_woba_using_speedangle"].mean()
        if len(contact_pa) > 0 else None
    )

    k_rate = (batter_pa["events"] == "strikeout").sum() / total_pa
    bb_rate = (batter_pa["events"] == "walk").sum() / total_pa

    singles = (batter_pa["events"] == "single").sum()
    doubles = (batter_pa["events"] == "double").sum()
    triples = (batter_pa["events"] == "triple").sum()
    home_runs = (batter_pa["events"] == "home_run").sum()
    walks = (batter_pa["events"] == "walk").sum()
    hit_by_pitch = (batter_pa["events"] == "hit_by_pitch").sum()
    sac_fly = (batter_pa["events"] == "sac_fly").sum()
    sac_bunt = (batter_pa["events"] == "sac_bunt").sum()

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
    iso = (
        slugging_pct - batting_avg
        if slugging_pct is not None and batting_avg is not None else None
    )

    balls_in_play_count = at_bats - (batter_pa["events"] == "strikeout").sum() - home_runs
    babip = (
        (total_hits - home_runs) / balls_in_play_count
        if balls_in_play_count > 0 else None
    )

    out_of_zone_pitches = batter_pitches[batter_pitches["is_out_of_zone"]]
    chase_rate = (
        out_of_zone_pitches["is_chase"].sum() / len(out_of_zone_pitches)
        if len(out_of_zone_pitches) > 0 else None
    )

    swings = batter_pitches[batter_pitches["is_swing"]]
    whiff_rate = (
        swings["is_whiff"].sum() / len(swings)
        if len(swings) > 0 else None
    )

    balls_in_play = batter_pitches[batter_pitches["bb_type"].notna()]
    hard_hit_rate = (
        balls_in_play["is_hard_hit"].sum() / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )
    avg_exit_velo = balls_in_play["launch_speed"].mean()

    avg_bat_speed = swings["bat_speed"].mean()
    avg_swing_length = swings["swing_length"].mean()

    barrel_rate = (
        balls_in_play["is_barrel"].sum() / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )
    sweet_spot_rate = (
        balls_in_play["is_sweet_spot"].sum() / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )

    in_zone_pitches = batter_pitches[batter_pitches["is_in_zone"]]
    in_zone_swings = in_zone_pitches[in_zone_pitches["is_swing"]]
    in_zone_contact_rate = (
        in_zone_swings["is_contact"].sum() / len(in_zone_swings)
        if len(in_zone_swings) > 0 else None
    )

    out_zone_pitches = batter_pitches[batter_pitches["is_out_of_zone"]]
    out_zone_swings = out_zone_pitches[out_zone_pitches["is_swing"]]
    out_zone_contact_rate = (
        out_zone_swings["is_contact"].sum() / len(out_zone_swings)
        if len(out_zone_swings) > 0 else None
    )

    fly_balls = balls_in_play[balls_in_play["is_fly_ball"]]
    pulled_flyballs_count = fly_balls["is_pulled"].sum()
    pulled_flyball_rate = (
        pulled_flyballs_count / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )

    fly_ball_rate = (
        balls_in_play["is_fly_ball"].sum() / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )
    line_drive_rate = (
        balls_in_play["is_line_drive"].sum() / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )
    ground_ball_rate = (
        balls_in_play["is_ground_ball"].sum() / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )
    core_stats.append({
        "batter": batter_id,
        "batter_name": batter_name,
        "current_team": current_team,
        "bats": bats,
        "total_pitches_seen": total_pitches,
        "total_pa": total_pa,
        "at_bats": at_bats,
        "hits": total_hits,
        "singles": singles,
        "doubles": doubles,
        "triples": triples,
        "home_runs": home_runs,
        "walks": walks,
        "hit_by_pitch": hit_by_pitch,
        "batting_avg": round(batting_avg, 3) if batting_avg is not None else None,
        "on_base_pct": round(on_base_pct, 3) if on_base_pct is not None else None,
        "slugging_pct": round(slugging_pct, 3) if slugging_pct is not None else None,
        "ops": round(ops, 3) if ops is not None else None,
        "iso": round(iso, 3) if iso is not None else None,
        "babip": round(babip, 3) if babip is not None else None,
        "woba": round(woba, 3),
        "xwoba": round(xwoba, 3) if pd.notna(xwoba) else None,
        "xba": round(xba, 3) if pd.notna(xba) else None,
        "xwobacon": round(xwobacon, 3) if xwobacon is not None and pd.notna(xwobacon) else None,
        "k_rate": round(k_rate, 3),
        "bb_rate": round(bb_rate, 3),
        "chase_rate": round(chase_rate, 3) if chase_rate is not None else None,
        "whiff_rate": round(whiff_rate, 3) if whiff_rate is not None else None,
        "hard_hit_rate": round(hard_hit_rate, 3) if hard_hit_rate is not None else None,
        "avg_exit_velo": round(avg_exit_velo, 1) if pd.notna(avg_exit_velo) else None,
        "avg_bat_speed": round(avg_bat_speed, 1) if pd.notna(avg_bat_speed) else None,
        "avg_swing_length": round(avg_swing_length, 2) if pd.notna(avg_swing_length) else None,
        "barrel_rate": round(barrel_rate, 3) if barrel_rate is not None else None,
        "sweet_spot_rate": round(sweet_spot_rate, 3) if sweet_spot_rate is not None else None,
        "in_zone_contact_rate": round(in_zone_contact_rate, 3) if in_zone_contact_rate is not None else None,
        "out_zone_contact_rate": round(out_zone_contact_rate, 3) if out_zone_contact_rate is not None else None,
        "pulled_flyball_rate": round(pulled_flyball_rate, 3) if pulled_flyball_rate is not None else None,
        "fly_ball_rate": round(fly_ball_rate, 3) if fly_ball_rate is not None else None,
        "line_drive_rate": round(line_drive_rate, 3) if line_drive_rate is not None else None,
        "ground_ball_rate": round(ground_ball_rate, 3) if ground_ball_rate is not None else None
    })

core_stats_df = pd.DataFrame(core_stats)
core_stats_df = core_stats_df.sort_values("woba", ascending=False)
core_stats_df.to_csv("data/hitter_core_stats.csv", index=False)

print(f"Total hitters with core stats: {len(core_stats_df)}")
print(f"Total columns: {len(core_stats_df.columns)}")
print(core_stats_df.columns.tolist())
print(core_stats_df.head(10))