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

import math

def velo_band(speed):
    """2-mph band, e.g. '94-96'. Bands anchor at even numbers."""
    if pd.isna(speed):
        return None
    band_floor = math.floor(speed / 2) * 2
    band_ceiling = band_floor + 2
    return f"{band_floor}-{band_ceiling}"


for df in [performance, tendency]:
    df["is_swing"] = df["description"].isin(swing_descriptions)
    df["is_whiff"] = df["description"].isin(whiff_descriptions)
    df["is_hard_hit"] = df["launch_speed"] >= 95
    df["velo_band"] = df["release_speed"].apply(velo_band)

performance_pa = performance.dropna(subset=["woba_denom"])
performance_pa["velo_band"] = performance_pa["release_speed"].apply(velo_band)

performance_pa = performance.dropna(subset=["woba_denom"])
performance_pa["velo_rounded"] = performance_pa["release_speed"].round(0)

modelable_pitch_types = ["FF", "SI", "SL", "CH", "ST", "FC", "CU", "FS", "KC"]


def calculate_tendency_stats(tendency_pitches, total_pitches_this_type):
    total_pitches = len(tendency_pitches)

    if total_pitches < 10:
        return None

    swings = tendency_pitches[tendency_pitches["is_swing"]]
    swing_rate = len(swings) / total_pitches if total_pitches > 0 else None

    pct_of_pitch_type = (
        total_pitches / total_pitches_this_type if total_pitches_this_type > 0 else None
    )

    return {
        "tendency_pitches_seen": total_pitches,
        "pct_of_pitch_type": round(pct_of_pitch_type, 3) if pct_of_pitch_type is not None else None,
        "swing_rate": round(swing_rate, 3) if swing_rate is not None else None
    }


def calculate_performance_stats(perf_pitches, perf_pa):
    total_pa = len(perf_pa)

    if total_pa < 5:
        # Lower threshold than other splits (5, not 10) since
        # single-mph granularity naturally produces very thin PA
        # samples - documented tradeoff of this level of detail.
        return None

    woba = (
        perf_pa["woba_value"].sum() / perf_pa["woba_denom"].sum()
        if perf_pa["woba_denom"].sum() > 0 else None
    )

    singles = (perf_pa["events"] == "single").sum()
    doubles = (perf_pa["events"] == "double").sum()
    triples = (perf_pa["events"] == "triple").sum()
    home_runs = (perf_pa["events"] == "home_run").sum()
    walks = (perf_pa["events"] == "walk").sum()
    hit_by_pitch = (perf_pa["events"] == "hit_by_pitch").sum()
    sac_fly = (perf_pa["events"] == "sac_fly").sum()
    sac_bunt = (perf_pa["events"] == "sac_bunt").sum()
    strikeouts = (perf_pa["events"] == "strikeout").sum()

    total_hits = singles + doubles + triples + home_runs
    total_bases = singles + (2 * doubles) + (3 * triples) + (4 * home_runs)
    at_bats = total_pa - walks - hit_by_pitch - sac_fly - sac_bunt

    batting_avg = total_hits / at_bats if at_bats > 0 else None
    slugging_pct = total_bases / at_bats if at_bats > 0 else None

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
        "strikeouts": strikeouts,
        "batting_avg": round(batting_avg, 3) if batting_avg is not None else None,
        "slugging_pct": round(slugging_pct, 3) if slugging_pct is not None else None,
        "woba": round(woba, 3) if woba is not None else None,
        "whiff_rate": round(whiff_rate, 3) if whiff_rate is not None else None,
        "hard_hit_rate": round(hard_hit_rate, 3) if hard_hit_rate is not None else None,
        "avg_exit_velo": round(avg_exit_velo, 1) if pd.notna(avg_exit_velo) else None
    }


velocity_rows = []

for batter_id, batter_tendency_pitches in tendency.groupby("batter"):

    batter_name = batter_tendency_pitches["batter_name"].iloc[0]
    current_team = batter_tendency_pitches["current_team"].iloc[0]

    batter_perf_pitches_all = performance[performance["batter"] == batter_id]

    for ptype in modelable_pitch_types:
        type_tendency = batter_tendency_pitches[batter_tendency_pitches["pitch_type"] == ptype]
        type_perf_all = batter_perf_pitches_all[batter_perf_pitches_all["pitch_type"] == ptype]
        total_pitches_this_type = len(type_tendency)

        band_values = type_tendency["velo_band"].dropna().unique()

        # Sort bands numerically by their floor value, not alphabetically
        # (alphabetical would put "100-102" before "94-96").
        band_values = sorted(band_values, key=lambda b: int(b.split("-")[0]))

        for band in band_values:
            mph_tendency = type_tendency[type_tendency["velo_band"] == band]
            mph_perf = type_perf_all[type_perf_all["velo_band"] == band]
            mph_perf_pa = performance_pa[
                (performance_pa["batter"] == batter_id)
                & (performance_pa["pitch_type"] == ptype)
                & (performance_pa["velo_band"] == band)
            ]

            tendency_stats = calculate_tendency_stats(mph_tendency, total_pitches_this_type)
            performance_stats = calculate_performance_stats(mph_perf, mph_perf_pa)

            if tendency_stats is None and performance_stats is None:
                continue

            row = {
                "batter": batter_id,
                "batter_name": batter_name,
                "current_team": current_team,
                "pitch_type": ptype,
                "velocity_band": band
            }
            if tendency_stats:
                row.update(tendency_stats)
            if performance_stats:
                row.update(performance_stats)

            velocity_rows.append(row)

velocity_df = pd.DataFrame(velocity_rows)

velocity_df = velocity_df.sort_values(["batter_name", "pitch_type", "velocity_band"])

velocity_df.to_csv("data/hitter_velocity_splits.csv", index=False)

print(f"Total batter/pitch-type/mph rows: {len(velocity_df)}")
print(f"Unique batters with at least one velocity split: {velocity_df['batter'].nunique()}")
print(f"Rows with performance data populated: {velocity_df['performance_pa'].notna().sum()}")
print(f"Rows with tendency-only (no performance): {velocity_df['performance_pa'].isna().sum()}")
print(velocity_df.head(15))