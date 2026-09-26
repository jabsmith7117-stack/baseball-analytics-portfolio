import pandas as pd

pitches = pd.read_csv("data/pitcher_data_with_names.csv")

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

called_strike_descriptions = ["called_strike"]

pitches["is_swing"] = pitches["description"].isin(swing_descriptions)
pitches["is_whiff"] = pitches["description"].isin(whiff_descriptions)
pitches["is_called_strike"] = pitches["description"].isin(called_strike_descriptions)
pitches["is_csw"] = pitches["is_whiff"] | pitches["is_called_strike"]
pitches["is_chase"] = pitches["is_swing"] & (pitches["zone"] >= 11)
pitches["is_out_of_zone"] = pitches["zone"] >= 11
pitches["is_in_zone"] = pitches["zone"] <= 9
pitches["is_hard_hit"] = pitches["launch_speed"] >= 95
pitches["is_strike"] = pitches["type"].isin(["S", "X"])

pa_ending = pitches.dropna(subset=["woba_denom"])

core_stats = []

for pitcher_id, pitcher_pitches in pitches.groupby("pitcher"):

    pitcher_name = pitcher_pitches["pitcher_name"].iloc[0]
    current_team = pitcher_pitches["current_team"].iloc[0]
    throws = pitcher_pitches["p_throws"].iloc[0]

    pitcher_pa = pa_ending[pa_ending["pitcher"] == pitcher_id]

    total_pitches = len(pitcher_pitches)
    total_pa = len(pitcher_pa)

    if total_pa < 20:
        continue

    woba_against = pitcher_pa["woba_value"].sum() / pitcher_pa["woba_denom"].sum()
    xwoba_against = pitcher_pa["estimated_woba_using_speedangle"].mean()
    xba_against = pitcher_pa["estimated_ba_using_speedangle"].mean()

    contact_pa = pitcher_pa[pitcher_pa["bb_type"].notna()]
    xwobacon_against = (
        contact_pa["estimated_woba_using_speedangle"].mean()
        if len(contact_pa) > 0 else None
    )

    k_rate = (pitcher_pa["events"] == "strikeout").sum() / total_pa
    bb_rate = (pitcher_pa["events"] == "walk").sum() / total_pa

    singles = (pitcher_pa["events"] == "single").sum()
    doubles = (pitcher_pa["events"] == "double").sum()
    triples = (pitcher_pa["events"] == "triple").sum()
    home_runs = (pitcher_pa["events"] == "home_run").sum()
    walks = (pitcher_pa["events"] == "walk").sum()
    strikeouts = (pitcher_pa["events"] == "strikeout").sum()
    hit_by_pitch = (pitcher_pa["events"] == "hit_by_pitch").sum()
    sac_fly = (pitcher_pa["events"] == "sac_fly").sum()
    sac_bunt = (pitcher_pa["events"] == "sac_bunt").sum()

    total_hits_allowed = singles + doubles + triples + home_runs
    total_bases_allowed = singles + (2 * doubles) + (3 * triples) + (4 * home_runs)
    at_bats = total_pa - walks - hit_by_pitch - sac_fly - sac_bunt

    avg_against = total_hits_allowed / at_bats if at_bats > 0 else None
    obp_against = (
        (total_hits_allowed + walks + hit_by_pitch) /
        (at_bats + walks + hit_by_pitch + sac_fly)
        if (at_bats + walks + hit_by_pitch + sac_fly) > 0 else None
    )
    slg_against = total_bases_allowed / at_bats if at_bats > 0 else None
    ops_against = (
        obp_against + slg_against
        if obp_against is not None and slg_against is not None else None
    )

    strike_rate = pitcher_pitches["is_strike"].sum() / total_pitches
    zone_rate = pitcher_pitches["is_in_zone"].sum() / total_pitches
    csw_rate = pitcher_pitches["is_csw"].sum() / total_pitches

    out_of_zone_pitches = pitcher_pitches[pitcher_pitches["is_out_of_zone"]]
    chase_rate_induced = (
        out_of_zone_pitches["is_chase"].sum() / len(out_of_zone_pitches)
        if len(out_of_zone_pitches) > 0 else None
    )

    swings = pitcher_pitches[pitcher_pitches["is_swing"]]
    whiff_rate_induced = (
        swings["is_whiff"].sum() / len(swings)
        if len(swings) > 0 else None
    )

    balls_in_play = pitcher_pitches[pitcher_pitches["bb_type"].notna()]
    hard_hit_rate_allowed = (
        balls_in_play["is_hard_hit"].sum() / len(balls_in_play)
        if len(balls_in_play) > 0 else None
    )
    avg_exit_velo_allowed = balls_in_play["launch_speed"].mean()

    core_stats.append({
        "pitcher": pitcher_id,
        "pitcher_name": pitcher_name,
        "current_team": current_team,
        "throws": throws,
        "total_pitches": total_pitches,
        "total_pa": total_pa,
        "at_bats": at_bats,
        "hits_allowed": total_hits_allowed,
        "home_runs_allowed": home_runs,
        "walks_allowed": walks,
        "strikeouts": strikeouts,
        "avg_against": round(avg_against, 3) if avg_against is not None else None,
        "obp_against": round(obp_against, 3) if obp_against is not None else None,
        "slg_against": round(slg_against, 3) if slg_against is not None else None,
        "ops_against": round(ops_against, 3) if ops_against is not None else None,
        "woba_against": round(woba_against, 3),
        "xwoba_against": round(xwoba_against, 3),
        "xba_against": round(xba_against, 3) if pd.notna(xba_against) else None,
        "xwobacon_against": round(xwobacon_against, 3) if xwobacon_against is not None and pd.notna(xwobacon_against) else None,
        "k_rate": round(k_rate, 3),
        "bb_rate": round(bb_rate, 3),
        "strike_rate": round(strike_rate, 3),
        "zone_rate": round(zone_rate, 3),
        "csw_rate": round(csw_rate, 3),
        "chase_rate_induced": round(chase_rate_induced, 3) if chase_rate_induced is not None else None,
        "whiff_rate_induced": round(whiff_rate_induced, 3) if whiff_rate_induced is not None else None,
        "hard_hit_rate_allowed": round(hard_hit_rate_allowed, 3) if hard_hit_rate_allowed is not None else None,
        "avg_exit_velo_allowed": round(avg_exit_velo_allowed, 1) if pd.notna(avg_exit_velo_allowed) else None
    })

core_stats_df = pd.DataFrame(core_stats)

core_stats_df = core_stats_df.sort_values("woba_against", ascending=True)

core_stats_df.to_csv("data/pitcher_core_stats.csv", index=False)

print(f"Total pitchers with core stats: {len(core_stats_df)}")
print(f"Total columns: {len(core_stats_df.columns)}")
print(core_stats_df.columns.tolist())
print(core_stats_df.head(10))