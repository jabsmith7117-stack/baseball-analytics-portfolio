import pandas as pd
from html import escape

PITCH_TYPE_NAMES = {
    "FF": "Four-Seam Fastball",
    "SI": "Sinker",
    "SL": "Slider",
    "CH": "Changeup",
    "ST": "Sweeper",
    "FC": "Cutter",
    "CU": "Curveball",
    "FS": "Splitter",
    "KC": "Knuckle Curve"
}

# Zone layout follows Statcast's standard 3x3 grid for the strike
# zone (1-9) plus four chase-zone quadrants just outside it (11-14).
# Left/Right here is from the catcher's/broadcast view (the
# standard charting convention), not "in" or "away," since that
# depends on the specific batter's handedness.
ZONE_NAMES = {
    1: "Top-Left (In Zone)",
    2: "Top-Middle (In Zone)",
    3: "Top-Right (In Zone)",
    4: "Middle-Left (In Zone)",
    5: "Middle-Middle (In Zone)",
    6: "Middle-Right (In Zone)",
    7: "Bottom-Left (In Zone)",
    8: "Bottom-Middle (In Zone)",
    9: "Bottom-Right (In Zone)",
    11: "Top-Left (Chase)",
    12: "Top-Right (Chase)",
    13: "Bottom-Left (Chase)",
    14: "Bottom-Right (Chase)"
}

# Explicit rename map for stat columns - handles proper capitalization
# for abbreviations (wOBA, OPS, etc.) that generic title-casing would
# get wrong (e.g. "Woba" instead of "wOBA").
COLUMN_RENAME = {
    "batter_name": "Player",
    "pitcher_name": "Player",
    "current_team": "Team",
    "bats": "Bats",
    "vs_throws": "Vs. Throws",
    "vs_stand": "Vs. Stand",
    "throws": "Throws",
    "pitch_type": "Pitch Type",
    "zone": "Location",
    "in_strike_zone": "In Zone",
    "count_group": "Count Situation",
    "count": "Count",
    "balls": "Balls",
    "strikes": "Strikes",
    "release_bucket": "Release Angle",
    "velocity_band": "Velocity Band",
    "usage_rate": "Usage Rate",
    "location_usage_rate": "Location Usage Rate",
    "pct_of_pitches_seen": "Pct Of Pitches Seen",
    "pct_of_pitch_type": "Pct Of This Pitch Type",
    "most_used_pitch": "Most Used Pitch",
    "most_used_pitch_rate": "Most Used Pitch Rate",
    "avg_velocity": "Avg Velocity",
    "avg_spin_rate": "Avg Spin Rate",
    "swing_rate": "Swing Rate",
    "swing_rate_induced": "Swing Rate",
    "chase_rate": "Chase Rate",
    "chase_rate_induced": "Chase Rate",
    "whiff_rate": "Whiff Rate",
    "whiff_rate_induced": "Whiff Rate",
    "hard_hit_rate": "Hard-Hit Rate",
    "hard_hit_rate_allowed": "Hard-Hit Rate",
    "avg_exit_velo": "Avg Exit Velo",
    "avg_exit_velo_allowed": "Avg Exit Velo",
    "batting_avg": "AVG",
    "avg_against": "AVG Against",
    "on_base_pct": "OBP",
    "obp_against": "OBP Against",
    "slugging_pct": "SLG",
    "slg_against": "SLG Against",
    "ops": "OPS",
    "ops_against": "OPS Against",
    "woba": "wOBA",
    "woba_against": "wOBA Against",
    "xwoba": "xwOBA",
    "xwoba_against": "xwOBA Against",
    "k_rate": "K Rate",
    "bb_rate": "BB Rate",
    "csw_rate": "CSW Rate",
    "zone_rate": "Zone Rate",
    "strike_rate": "Strike Rate",
    "hits": "Hits",
    "hits_allowed": "Hits Allowed",
    "home_runs": "HR",
    "home_runs_allowed": "HR Allowed",
    "strikeouts": "Strikeouts",
    "performance_pa": "Sample Size (PA)",
    "at_bats": "At Bats",
    "tendency_pitches": "Sample Size (Pitches)",
    "tendency_pitches_seen": "Sample Size (Pitches)"
}

THREE_DECIMAL_COLUMNS = {
    "batting_avg", "avg_against", "on_base_pct", "obp_against",
    "slugging_pct", "slg_against", "ops", "ops_against", "woba",
    "woba_against", "xwoba", "xwoba_against", "xba",
    "xba_against", "xwobacon", "xwobacon_against", "iso", "babip"
}

COLUMN_RENAME.update({
    "total_pitches_seen": "Pitches Seen", "total_pitches": "Pitches",
    "total_pa": "Plate Appearances", "at_bats": "At Bats",
    "walks": "Walks", "walks_allowed": "Walks Allowed",
    "singles": "Singles", "doubles": "Doubles", "triples": "Triples",
    "iso": "ISO", "babip": "BABIP", "xba": "xBA",
    "xba_against": "xBA Against", "xwobacon": "xwOBACON",
    "xwobacon_against": "xwOBACON Against", "avg_bat_speed": "Avg Bat Speed",
    "avg_swing_length": "Avg Swing Length", "barrel_rate": "Barrel Rate",
    "sweet_spot_rate": "Sweet Spot Rate", "in_zone_contact_rate": "In-Zone Contact Rate",
    "out_zone_contact_rate": "Out-of-Zone Contact Rate",
    "pulled_flyball_rate": "Pulled Fly Ball Rate", "fly_ball_rate": "Fly Ball Rate",
    "line_drive_rate": "Line Drive Rate", "ground_ball_rate": "Ground Ball Rate"
})

# Columns that are stored as decimals (e.g. 0.275) and should be
# displayed as percentages (e.g. "27.5%").
RATE_COLUMNS = [
    "usage_rate", "location_usage_rate", "pct_of_pitches_seen",
    "pct_of_pitch_type", "most_used_pitch_rate", "swing_rate",
    "swing_rate_induced", "chase_rate", "chase_rate_induced",
    "whiff_rate", "whiff_rate_induced", "hard_hit_rate",
    "hard_hit_rate_allowed", "k_rate", "bb_rate", "csw_rate",
    "zone_rate", "strike_rate", "barrel_rate", "sweet_spot_rate",
    "in_zone_contact_rate",
    "out_zone_contact_rate", "pulled_flyball_rate", "fly_ball_rate",
    "line_drive_rate", "ground_ball_rate"
]

# ID columns to always drop from display - internal keys only.
ID_COLUMNS = ["batter", "pitcher"]

# Columns to drop everywhere EXCEPT the zone tab, per report scope -
# sample size columns clutter most views but matter for judging
# reliability specifically on the zone tab.
SAMPLE_SIZE_COLUMNS = ["performance_pa", "tendency_pitches", "tendency_pitches_seen"]

HBP_COLUMNS = ["hit_by_pitch"]


def format_for_display(df, keep_sample_size=False, extra_drop=None):
    """Apply all standard display formatting: drop ID/HBP columns,
    optionally drop sample size columns, map pitch types and zones
    to readable labels, convert rates to percentage strings, and
    rename columns to clean, properly capitalized headers."""

    display_df = df.copy()

    columns_to_drop = list(ID_COLUMNS) + list(HBP_COLUMNS)
    if not keep_sample_size:
        columns_to_drop += SAMPLE_SIZE_COLUMNS
    if extra_drop:
        columns_to_drop += extra_drop

    display_df = display_df.drop(
        columns=[c for c in columns_to_drop if c in display_df.columns]
    )

    if "pitch_type" in display_df.columns:
        display_df["pitch_type"] = display_df["pitch_type"].map(PITCH_TYPE_NAMES).fillna(display_df["pitch_type"])

    if "zone" in display_df.columns:
        display_df["zone"] = display_df["zone"].map(ZONE_NAMES).fillna(display_df["zone"])

    for col in RATE_COLUMNS:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "N/A"
            )

    for col in THREE_DECIMAL_COLUMNS.intersection(display_df.columns):
        display_df[col] = display_df[col].apply(
            lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
        )

    # Non-rate numeric splits retain their numeric type for table sorting.
    # Streamlit renders remaining missing values as blank rather than 'None'.

    rename_map = {k: v for k, v in COLUMN_RENAME.items() if k in display_df.columns}
    display_df = display_df.rename(columns=rename_map)

    display_df = display_df.rename(columns={
        col: col.replace("_", " ").title()
        for col in display_df.columns if "_" in col
    })

    for col in display_df.select_dtypes(include="object"):
        display_df[col] = display_df[col].fillna("N/A")

    return display_df


def show_table(df, sticky_column=None, **kwargs):
    """Scrollable report table with filled headers and a fixed identifying column."""
    sticky_index = df.columns.get_loc(sticky_column) if sticky_column in df.columns else 0
    headers = "".join(
        f'<th class="sticky-column">{escape(str(col))}</th>' if index == sticky_index
        else f"<th>{escape(str(col))}</th>"
        for index, col in enumerate(df.columns)
    )
    rows = ""
    for row in df.itertuples(index=False, name=None):
        selected = " class=\"selected-player\"" if "Role" in df.columns and row[df.columns.get_loc("Role")] == "Selected Player" else ""
        rows += "<tr" + selected + ">" + "".join(
            f'<td class="sticky-column">{escape(str(value)) if pd.notna(value) else "N/A"}</td>'
            if index == sticky_index else
            f"<td>{escape(str(value)) if pd.notna(value) else 'N/A'}</td>"
            for index, value in enumerate(row)
        ) + "</tr>"
    table = f"""<div class="baseball-table-wrap"><table class="baseball-table">
    <thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>"""
    st.markdown(table, unsafe_allow_html=True)


def colorful_columns(df, overrides=None):
    """Native grid header labels; CSS colors native headers when supported."""
    overrides = dict(overrides or {})
    for index, name in enumerate(df.columns):
        if name not in overrides:
            overrides[name] = st.column_config.Column(str(name))
    return overrides
import streamlit as st


def render_count_tree(raw_count_df, key_prefix, keep_sample_size=False):
    """Interactive count navigator: starts at 0-0, lets the user
    click Ball or Strike to drill into the next count, showing that
    count's stats at each step. Uses Streamlit session_state to
    track the current position in the tree, keyed per-widget-group
    so hitter and pitcher trees (and different selected players)
    don't interfere with each other."""

    balls_key = f"{key_prefix}_tree_balls"
    strikes_key = f"{key_prefix}_tree_strikes"

    if balls_key not in st.session_state:
        st.session_state[balls_key] = 0
    if strikes_key not in st.session_state:
        st.session_state[strikes_key] = 0

    current_balls = st.session_state[balls_key]
    current_strikes = st.session_state[strikes_key]

    st.write(f"### Count: {current_balls}-{current_strikes}")

    current_row = raw_count_df[
        (raw_count_df["balls"] == current_balls)
        & (raw_count_df["strikes"] == current_strikes)
    ]

    if len(current_row) == 0:
        st.info("No data available at this count (sample too small).")
    else:
        display_row = format_for_display(
            current_row, extra_drop=["balls", "strikes", "count"],
            keep_sample_size=keep_sample_size,
        )
        show_table(display_row, use_container_width=True)

    col_ball, col_strike, col_reset = st.columns(3)

    with col_ball:
        can_go_ball = current_balls < 3
        if st.button(
            f"⚾ Ball → {current_balls + 1}-{current_strikes}" if can_go_ball else "Ball → Walk",
            disabled=not can_go_ball,
            key=f"{key_prefix}_ball_btn"
        ):
            st.session_state[balls_key] += 1
            st.rerun()

    with col_strike:
        can_go_strike = current_strikes < 2
        if st.button(
            f"❌ Strike → {current_balls}-{current_strikes + 1}" if can_go_strike else "Strike → Out",
            disabled=not can_go_strike,
            key=f"{key_prefix}_strike_btn"
        ):
            st.session_state[strikes_key] += 1
            st.rerun()

    with col_reset:
        if st.button("↺ Reset To 0-0", key=f"{key_prefix}_reset_btn"):
            st.session_state[balls_key] = 0
            st.session_state[strikes_key] = 0
            st.rerun()
def generate_pitch_sequence_guide(
    batter_name, pitcher_name, batter_stand,
    pitcher_raw_count_df, hitter_pitch_type_df, pitcher_pitch_type_df,
    hitter_zone_df
):
    """Shows this specific pitcher's real, actual pitch usage in each
    count (against hitters of this handedness), alongside this hitter's
    known season performance against that pitch type - as context, not
    a recommendation. Deliberately does NOT try to override the
    pitcher's real tendency, since doing so would require modeling
    pitch-sequencing/predictability tradeoffs that this data can't
    support (see page methodology).
    """

    all_counts = [
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 1), (1, 2),
        (2, 0), (2, 1), (2, 2),
        (3, 0), (3, 1), (3, 2)
    ]

    this_pitcher_counts = pitcher_raw_count_df[
        (pitcher_raw_count_df["pitcher_name"] == pitcher_name)
        & (pitcher_raw_count_df["vs_stand"] == batter_stand)
    ]

    this_hitter_pitches = hitter_pitch_type_df[
        hitter_pitch_type_df["batter_name"] == batter_name
    ]

    this_hitter_zones = hitter_zone_df[
        (hitter_zone_df["batter_name"] == batter_name)
        & (hitter_zone_df["performance_pa"].notna())
        & (hitter_zone_df["performance_pa"] >= 10)
    ]
    weakest_zone = None
    if len(this_hitter_zones) > 0:
        weakest_zone = this_hitter_zones.sort_values("woba").iloc[0]["zone"]

    sequence = []

    for balls, strikes in all_counts:
        count_row = this_pitcher_counts[
            (this_pitcher_counts["balls"] == balls)
            & (this_pitcher_counts["strikes"] == strikes)
        ]

        if len(count_row) == 0:
            sequence.append({
                "count": f"{balls}-{strikes}",
                "pitcher_typical_pitch": None,
                "note": "Insufficient data for this count"
            })
            continue

        typical_pitch = count_row.iloc[0]["most_used_pitch"]
        typical_usage = count_row.iloc[0]["most_used_pitch_rate"]

        hitter_vs_pitch = this_hitter_pitches[
            this_hitter_pitches["pitch_type"] == typical_pitch
        ]

        hitter_woba = (
            hitter_vs_pitch.iloc[0]["woba"]
            if len(hitter_vs_pitch) > 0 and hitter_vs_pitch.iloc[0].get("woba") is not None
            else None
        )

        if hitter_woba is not None:
            if hitter_woba < 0.290:
                note = f"Hitter has struggled against this pitch (wOBA {hitter_woba:.3f})"
            elif hitter_woba > 0.400:
                note = f"Hitter has handled this pitch well (wOBA {hitter_woba:.3f})"
            else:
                note = f"Roughly average result for hitter (wOBA {hitter_woba:.3f})"
        else:
            note = "No reliable 2026 sample for hitter against this pitch"

        sequence.append({
            "count": f"{balls}-{strikes}",
            "pitcher_typical_pitch": typical_pitch,
            "usage_rate": typical_usage,
            "note": note
        })

    return sequence, weakest_zone
def render_pitch_sequence_tree(pitch_choice_df, outcome_df, hitter_pitch_type_by_count_df,
                               batter_name, pitcher_throws, key_prefix, pitcher_arsenal):
    """Explore a pitcher's entire recorded arsenal through valid count outcomes.

    Pitch choice and outcome rates are conditional on a plate appearance
    continuing to another pitch. Ending pitches are not in those tables, so
    unobserved choices remain available without invented probabilities.
    """
    count_key = f"{key_prefix}_seq_count"
    history_key = f"{key_prefix}_seq_history"
    pending_key = f"{key_prefix}_seq_pending_pitch"
    finished_key = f"{key_prefix}_seq_finished"
    for key, default in ((count_key, "0-0"), (history_key, []),
                         (pending_key, None), (finished_key, None)):
        if key not in st.session_state:
            st.session_state[key] = default

    count = st.session_state[count_key]
    history = st.session_state[history_key]
    pending = st.session_state[pending_key]
    finished = st.session_state[finished_key]
    st.write("**Sequence so far:** " + " → ".join(history) + f" → **{count}**" if history
             else f"**Starting count: {count}**")

    if finished:
        st.success(f"Plate appearance complete: {finished}. Reset to explore another path.")
    elif pending is None:
        observed = pitch_choice_df[pitch_choice_df["count"] == count]
        options = pitcher_arsenal.sort_values("usage_rate", ascending=False)
        st.write(f"**Pitch {len(history) + 1}: choose a pitch at {count}**")
        for _, arsenal_row in options.iterrows():
            pitch_type = arsenal_row["pitch_type"]
            pitch_display = PITCH_TYPE_NAMES.get(pitch_type, pitch_type)
            choice = observed[observed["pitch_type"] == pitch_type]
            if not choice.empty:
                row = choice.iloc[0]
                pitch_note = (f"{row['pitch_rate']:.1%} among {int(row['total_pitches_at_count'])} "
                              "pitches with a recorded next pitch")
            else:
                usage = arsenal_row.get("usage_rate")
                pitch_note = (f"{usage:.1%} season usage; no continuing-pitch sample at this count"
                              if pd.notna(usage) else "recorded arsenal pitch; no continuing-pitch sample")
            hitter_row = hitter_pitch_type_by_count_df[
                (hitter_pitch_type_by_count_df["batter_name"] == batter_name)
                & (hitter_pitch_type_by_count_df["pitch_type"] == pitch_type)
                & (hitter_pitch_type_by_count_df["count"] == count)
                & (hitter_pitch_type_by_count_df["vs_throws"] == pitcher_throws)
            ]
            hitter_note = ""
            if not hitter_row.empty and pd.notna(hitter_row.iloc[0].get("woba")):
                row = hitter_row.iloc[0]
                hitter_note = f" | hitter wOBA {row['woba']:.3f} ({int(row['performance_pa'])} PA)"
            if st.button(f"{pitch_display} ({pitch_note}){hitter_note}",
                         key=f"{key_prefix}_pitch_{count}_{pitch_type}"):
                st.session_state[pending_key] = pitch_type
                st.rerun()
    else:
        balls, strikes = map(int, count.split("-"))
        pitch_display = PITCH_TYPE_NAMES.get(pending, pending)
        observed = outcome_df[(outcome_df["count"] == count)
                              & (outcome_df["pitch_type"] == pending)]
        st.write(f"**Pitch {len(history) + 1} result: {pitch_display} at {count}**")
        st.caption("Observed rates below are conditional on another pitch following in the same plate appearance. Missing rates do not make a baseball outcome impossible.")

        def add_result(label, next_count=None, ending=None):
            sample = observed[observed["resulting_count"] == next_count] if next_count else observed.iloc[0:0]
            if next_count:
                note = (f" ({sample.iloc[0]['outcome_rate']:.1%} of continuing pitches)"
                        if not sample.empty else " (no continuing-pitch rate)")
            else:
                note = " (ending pitches excluded from transition table)"
            if st.button(label + note, key=f"{key_prefix}_result_{count}_{pending}_{label}"):
                st.session_state[history_key] = history + [f"{count} ({pitch_display}) → {label}"]
                st.session_state[pending_key] = None
                if ending:
                    st.session_state[finished_key] = ending
                else:
                    st.session_state[count_key] = next_count
                st.rerun()

        if balls < 3:
            add_result(f"Ball → {balls + 1}-{strikes}", f"{balls + 1}-{strikes}")
        else:
            add_result("Ball four → Walk", ending="Walk")
        if strikes < 2:
            add_result(f"Strike → {balls}-{strikes + 1}", f"{balls}-{strikes + 1}")
        else:
            add_result("Foul → count stays", count)
            add_result("Strike three → Strikeout", ending="Strikeout")
        add_result("Ball in play → PA ends", ending="Ball in play")
        if st.button("← Back to pitch selection", key=f"{key_prefix}_back_{count}"):
            st.session_state[pending_key] = None
            st.rerun()

    if st.button("↺ Reset Sequence", key=f"{key_prefix}_seq_reset"):
        st.session_state[count_key] = "0-0"
        st.session_state[history_key] = []
        st.session_state[pending_key] = None
        st.session_state[finished_key] = None
        st.rerun()

# Exact coefficients from the trained success probability model
# (R's glm() logistic regression, matchup_success_model.rds).
SUCCESS_MODEL_COEFFICIENTS = {
    "platoon_advantage": 0.08895,
    "batter_ops": 1.47310,
    "batter_k_rate": -0.45183,
    "batter_chase_rate": -0.90921,
    "batter_hard_hit_rate": -0.25933,
    "batter_whiff_rate": 0.08040,
    "pitcher_whiff_rate": -0.18615,
    "pitcher_chase_rate": 0.07364,
    "pitcher_hard_hit_rate_allowed": 0.79596,
    "pitcher_k_rate": -1.52383,
    "pitcher_bb_rate": 3.75693
}

FACTOR_DISPLAY_NAMES = {
    "platoon_advantage": "Platoon matchup",
    "batter_ops": "Batter's OPS",
    "batter_k_rate": "Batter's strikeout rate",
    "batter_chase_rate": "Batter's chase rate",
    "batter_hard_hit_rate": "Batter's hard-hit rate",
    "batter_whiff_rate": "Batter's whiff rate",
    "pitcher_whiff_rate": "Pitcher's whiff rate induced",
    "pitcher_chase_rate": "Pitcher's chase rate induced",
    "pitcher_hard_hit_rate_allowed": "Pitcher's hard-hit rate allowed",
    "pitcher_k_rate": "Pitcher's strikeout rate",
    "pitcher_bb_rate": "Pitcher's walk rate"
}


def compute_contributing_factors(matchup_row, population_means, top_n=5):
    """Decomposes the success probability prediction into per-feature
    log-odds contributions, using the model's real trained coefficients
    and how this matchup's actual feature values compare to the
    population average. Returns the top N factors by magnitude,
    ranked, with direction (favors hitter/pitcher)."""

    feature_value_map = {
        "platoon_advantage": matchup_row["platoon_advantage"],
        "batter_ops": matchup_row.get("batter_ops"),
        "batter_k_rate": matchup_row.get("batter_k_rate"),
        "batter_chase_rate": matchup_row.get("batter_chase_rate"),
        "batter_hard_hit_rate": matchup_row.get("batter_hard_hit_rate"),
        "batter_whiff_rate": matchup_row.get("batter_whiff_rate"),
        "pitcher_whiff_rate": matchup_row.get("pitcher_whiff_rate"),
        "pitcher_chase_rate": matchup_row.get("pitcher_chase_rate"),
        "pitcher_hard_hit_rate_allowed": matchup_row.get("pitcher_hard_hit_rate_allowed"),
        "pitcher_k_rate": matchup_row.get("pitcher_k_rate"),
        "pitcher_bb_rate": matchup_row.get("pitcher_bb_rate")
    }

    factors = []

    for feature, coefficient in SUCCESS_MODEL_COEFFICIENTS.items():
        value = feature_value_map.get(feature)
        mean = population_means.get(feature)

        if value is None or mean is None:
            continue

        if feature == "platoon_advantage":
            # Binary feature: contribution is simply coefficient * 1 or 0,
            # not centered around a population average.
            contribution = coefficient * value
        else:
            contribution = coefficient * (value - mean)

        factors.append({
            "feature": feature,
            "display_name": FACTOR_DISPLAY_NAMES.get(feature, feature),
            "value": value,
            "population_mean": mean,
            "contribution": contribution,
            "favors": "hitter" if contribution > 0 else "pitcher"
        })

    factors_sorted = sorted(factors, key=lambda f: abs(f["contribution"]), reverse=True)

    return factors_sorted[:top_n]        
