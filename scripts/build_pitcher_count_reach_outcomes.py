"""Build consistent 2026 pitch and eventual PA measures for exact counts.

Pitch-level metrics in the raw count table describe 2026 pitches
thrown at that count. Outcome metrics describe the final result of plate
appearances that reached it. Repeated foul balls do not duplicate a PA.
"""

from pathlib import Path
import pandas as pd

RAW = Path("data/statcast_2023_2026_full.csv")
TABLE = Path("data/pitcher_raw_count_splits.csv")
KEY = ["game_pk", "at_bat_number", "pitcher"]
COUNT_KEY = ["pitcher", "vs_stand", "balls", "strikes"]
OUTCOME_COLUMNS = [
    "performance_pa", "at_bats", "hits_allowed", "home_runs_allowed",
    "avg_against", "slg_against", "woba_against", "k_rate",
]
PITCH_COLUMNS = [
    "tendency_pitches", "most_used_pitch", "most_used_pitch_rate",
    "swing_rate_induced", "whiff_rate_induced", "hard_hit_rate_allowed",
    "avg_exit_velo_allowed",
]


def update_raw_count_outcomes(raw_path=RAW, table_path=TABLE):
    fields = KEY + [
        "pitch_number", "game_year", "stand", "balls", "strikes",
        "events", "woba_value", "woba_denom", "pitch_type",
        "description", "bb_type", "launch_speed", "type",
    ]
    raw = pd.read_csv(raw_path, usecols=fields)
    raw = raw.loc[raw.game_year.eq(2026)].dropna(
        subset=KEY + ["pitch_number", "stand", "balls", "strikes"]
    ).copy()
    raw["balls"] = raw["balls"].astype(int)
    raw["strikes"] = raw["strikes"].astype(int)
    raw = raw[raw.balls.between(0, 3) & raw.strikes.between(0, 2)]
    raw = raw[raw["type"].notna()].copy()
    raw["vs_stand"] = raw["stand"]
    raw["is_swing"] = raw.description.isin([
        "hit_into_play", "foul", "foul_tip", "swinging_strike",
        "swinging_strike_blocked",
    ])
    raw["is_whiff"] = raw.description.isin([
        "swinging_strike", "swinging_strike_blocked",
    ])
    raw["is_bip"] = raw.bb_type.notna()
    raw["is_hard_hit"] = raw.launch_speed.ge(95) & raw.is_bip
    pitches = raw.groupby(COUNT_KEY, as_index=False).agg(
        tendency_pitches=("pitch_number", "size"),
        swings=("is_swing", "sum"), whiffs=("is_whiff", "sum"),
        balls_in_play=("is_bip", "sum"), hard_hits=("is_hard_hit", "sum"),
        avg_exit_velo_allowed=("launch_speed", "mean"),
    )
    pitch_types = (
        raw.dropna(subset=["pitch_type"]).groupby(COUNT_KEY + ["pitch_type"])
        .size().rename("pitch_count").reset_index()
        .sort_values(COUNT_KEY + ["pitch_count", "pitch_type"],
                     ascending=[True, True, True, True, False, True])
        .drop_duplicates(COUNT_KEY)
    )
    pitches = pitches.merge(pitch_types, on=COUNT_KEY, how="left", validate="one_to_one")
    pitches["most_used_pitch"] = pitches.pitch_type
    pitches["most_used_pitch_rate"] = pitches.pitch_count / pitches.tendency_pitches
    pitches["swing_rate_induced"] = pitches.swings / pitches.tendency_pitches
    pitches["whiff_rate_induced"] = pitches.whiffs / pitches.swings.where(pitches.swings.gt(0))
    pitches["hard_hit_rate_allowed"] = pitches.hard_hits / pitches.balls_in_play.where(pitches.balls_in_play.gt(0))
    pitches["avg_exit_velo_allowed"] = pitches.avg_exit_velo_allowed.where(pitches.balls_in_play.gt(0))
    pitches[PITCH_COLUMNS[2:]] = pitches[PITCH_COLUMNS[2:]].round(3)

    reached = raw[KEY + ["stand", "balls", "strikes"]].drop_duplicates(
        KEY + ["stand", "balls", "strikes"]
    )
    terminal = (
        raw.loc[raw.events.notna(), KEY + [
            "pitch_number", "events", "woba_value", "woba_denom",
        ]]
        .sort_values("pitch_number")
        .drop_duplicates(KEY, keep="last")
        .drop(columns="pitch_number")
    )
    followed = reached.merge(terminal, on=KEY, how="inner", validate="many_to_one")
    followed = followed.rename(columns={"stand": "vs_stand"})
    events = followed.events
    followed["hit"] = events.isin(["single", "double", "triple", "home_run"]).astype(int)
    followed["home_run"] = events.eq("home_run").astype(int)
    followed["total_bases"] = events.map({
        "single": 1, "double": 2, "triple": 3, "home_run": 4,
    }).fillna(0)
    followed["excluded_ab"] = events.isin([
        "walk", "intent_walk", "hit_by_pitch", "sac_fly", "sac_bunt",
        "catcher_interf",
    ]).astype(int)
    followed["strikeout"] = events.eq("strikeout").astype(int)
    followed["woba_value"] = pd.to_numeric(followed.woba_value, errors="coerce")
    followed["woba_denom"] = pd.to_numeric(followed.woba_denom, errors="coerce")

    summary = followed.groupby(COUNT_KEY, as_index=False).agg(
        performance_pa=("events", "size"),
        excluded_ab=("excluded_ab", "sum"),
        hits_allowed=("hit", "sum"),
        home_runs_allowed=("home_run", "sum"),
        total_bases=("total_bases", "sum"),
        strikeouts=("strikeout", "sum"),
        woba_value=("woba_value", "sum"),
        woba_denom=("woba_denom", "sum"),
    )
    summary["at_bats"] = summary.performance_pa - summary.excluded_ab
    summary["avg_against"] = (
        summary.hits_allowed / summary.at_bats.where(summary.at_bats.gt(0))
    ).round(3)
    summary["slg_against"] = (
        summary.total_bases / summary.at_bats.where(summary.at_bats.gt(0))
    ).round(3)
    summary["woba_against"] = (
        summary.woba_value / summary.woba_denom.where(summary.woba_denom.gt(0))
    ).round(3)
    summary["k_rate"] = (summary.strikeouts / summary.performance_pa).round(3)

    table = pd.read_csv(table_path)
    table = table.drop(columns=[c for c in OUTCOME_COLUMNS + PITCH_COLUMNS if c in table.columns])
    table = table.merge(pitches[COUNT_KEY + PITCH_COLUMNS], on=COUNT_KEY,
                        how="left", validate="one_to_one")
    table = table.merge(
        summary[COUNT_KEY + OUTCOME_COLUMNS], on=COUNT_KEY,
        how="left", validate="one_to_one",
    )
    table = table.sort_values(["pitcher_name", "vs_stand", "balls", "strikes"])
    table.to_csv(table_path, index=False)
    print(
        f"Updated {len(table)} count rows from {len(followed)} "
        "2026 plate-appearance/count observations."
    )


if __name__ == "__main__":
    update_raw_count_outcomes()
