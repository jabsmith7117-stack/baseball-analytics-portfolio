from ui_theme import apply_theme
import streamlit as st
import pandas as pd
from report_helpers import render_pitch_sequence_tree, compute_contributing_factors, PITCH_TYPE_NAMES, ZONE_NAMES, format_for_display, show_table
from roster_helpers import active_roster, roster_filter
from team_preferences import opening_team_index
apply_theme()

st.title("Batter-Pitcher Matchup Predictor")

st.write(
    """
    This tool uses R-based statistical models (logistic and linear regression)
    trained on real 2026 Statcast plate appearances to predict how a specific
    batter is likely to perform against a specific pitcher. The model predicts
    a **success probability** (reaching base via hit, walk, or HBP) alongside
    **expected quality metrics** (xwOBA, xBA, xwOBACON) specific to this
    exact matchup, factoring in each player's season-long tendencies and
    the platoon (handedness) matchup.
    """
)

predictions = pd.read_csv("data/matchup_predictions.csv")
roster = active_roster()
if roster is not None:
    st.caption(f"Active MLB rosters checked {roster['as_of_utc'].iloc[0]} UTC. Matchup predictions use 2026 Statcast data through the last data refresh.")
    if st.toggle("Show only current active rosters", value=True):
        predictions = roster_filter(predictions, "batter", "batter_current_team", roster)
        predictions = roster_filter(predictions, "pitcher", "pitcher_current_team", roster, pitchers=True)
    else:
        pitcher_ids = pd.read_csv("data/pitcher_core_stats.csv", usecols=["pitcher", "total_pitches"])
        predictions = predictions.merge(pitcher_ids[pitcher_ids.total_pitches >= 50][["pitcher"]], on="pitcher", how="inner")
else:
    st.caption("Team assignments follow each player's latest 2026 appearance; this is not an official active roster.")
    pitcher_ids = pd.read_csv("data/pitcher_core_stats.csv", usecols=["pitcher", "total_pitches"])
    predictions = predictions.merge(pitcher_ids[pitcher_ids.total_pitches >= 50][["pitcher"]], on="pitcher", how="inner")

st.header("Select A Matchup")

col1, col2 = st.columns(2)

with col1:
    st.write("**Batter**")
    batter_team_options = sorted(predictions["batter_current_team"].unique())
    selected_batter_team = st.selectbox("Batter's Team", batter_team_options, index=opening_team_index(batter_team_options), key="batter_team_select")

    batter_options = sorted(
        predictions[predictions["batter_current_team"] == selected_batter_team]["batter_name"].unique()
    )
    selected_batter = st.selectbox("Batter", batter_options, key="batter_select")

with col2:
    st.write("**Pitcher**")
    pitcher_team_options = sorted(predictions["pitcher_current_team"].unique())
    selected_pitcher_team = st.selectbox("Pitcher's Team", pitcher_team_options, index=opening_team_index(pitcher_team_options), key="pitcher_team_select")

    available_pitchers = predictions[
        (predictions["batter_name"] == selected_batter)
        & (predictions["pitcher_current_team"] == selected_pitcher_team)
    ]["pitcher_name"].unique()
    pitcher_options = sorted(available_pitchers)
    selected_pitcher = st.selectbox("Pitcher", pitcher_options, key="pitcher_select")

matchup_row = predictions[
    (predictions["batter_name"] == selected_batter)
    & (predictions["pitcher_name"] == selected_pitcher)
].iloc[0]

st.header(f"{selected_batter} vs. {selected_pitcher}")

effective_bats = ("L" if matchup_row["throws"] == "R" else "R") if matchup_row["bats"] == "S" else matchup_row["bats"]
batting_label = f"switch hitter batting {'left' if effective_bats == 'L' else 'right'}" if matchup_row["bats"] == "S" else f"bats {effective_bats}"
platoon_text = " | Platoon advantage for the batter" if matchup_row["platoon_advantage"] == 1 else ""

st.caption(
    f"{selected_batter}: {batting_label} | "
    f"{selected_pitcher} throws {matchup_row['throws']}{platoon_text}"
)

col1, col2, col3, col4 = st.columns([1.9, 1, 1, 1])

col1.metric(
    "Predicted Batter Success Probability",
    f"{matchup_row['predicted_success_probability']:.1%}"
)
col2.metric("Predicted xwOBA", matchup_row["predicted_xwoba"])
col3.metric("Predicted xBA", matchup_row["predicted_xba"])
col4.metric("Predicted xwOBACON", matchup_row["predicted_xwobacon"])

# League baseline success rate, calculated from the real 2026
# training data (roughly matches league-average on-base rate, since
# "success" is defined as reaching base via hit, walk, or HBP).
LEAGUE_AVG_SUCCESS_RATE = 0.314

success_prob = matchup_row["predicted_success_probability"]
gap = success_prob - LEAGUE_AVG_SUCCESS_RATE

if gap >= 0.05:
    favor_label = "This matchup favors the **batter**"
elif gap <= -0.05:
    favor_label = "This matchup favors the **pitcher**"
elif gap >= 0.015:
    favor_label = "This matchup slightly favors the **batter**"
elif gap <= -0.015:
    favor_label = "This matchup slightly favors the **pitcher**"
else:
    favor_label = "This matchup is close to the **league baseline**"

st.write(
    f"""
    **{favor_label}**, with a predicted success probability of
    **{success_prob:.1%}** compared to the model's 2026 reference baseline of
    **{LEAGUE_AVG_SUCCESS_RATE:.1%}**
    ({'+' if gap >= 0 else ''}{gap:.1%} relative to average).
    """
)

# Real, model-based contributing factor breakdown - uses the trained
# logistic regression's actual coefficients to show exactly how much
# each factor pushed this prediction, rather than hand-picked
# thresholds.
batter_core = pd.read_csv("data/hitter_core_stats.csv")
pitcher_core = pd.read_csv("data/pitcher_core_stats.csv")

population_means = {
    "batter_ops": batter_core["ops"].mean(),
    "batter_k_rate": batter_core["k_rate"].mean(),
    "batter_chase_rate": batter_core["chase_rate"].mean(),
    "batter_hard_hit_rate": batter_core["hard_hit_rate"].mean(),
    "batter_whiff_rate": batter_core["whiff_rate"].mean(),
    "pitcher_whiff_rate": pitcher_core["whiff_rate_induced"].mean(),
    "pitcher_chase_rate": pitcher_core["chase_rate_induced"].mean(),
    "pitcher_hard_hit_rate_allowed": pitcher_core["hard_hit_rate_allowed"].mean(),
    "pitcher_k_rate": pitcher_core["k_rate"].mean(),
    "pitcher_bb_rate": pitcher_core["bb_rate"].mean()
}

top_factors = compute_contributing_factors(matchup_row, population_means, top_n=5)

st.write("**Top Contributing Factors** (ranked by actual model impact):")

for factor in top_factors:
    direction_arrow = "favors hitter" if factor["favors"] == "hitter" else "favors pitcher"
    is_rate = factor["feature"].endswith("_rate") or factor["feature"] == "platoon_advantage"
    value = ("Yes" if factor["value"] else "No") if factor["feature"] == "platoon_advantage" else (f"{factor['value']:.1%}" if is_rate else f"{factor['value']:.3f}")
    average = "—" if factor["feature"] == "platoon_advantage" else (f"{factor['population_mean']:.1%}" if is_rate else f"{factor['population_mean']:.3f}")
    st.write(
        f"- **{factor['display_name']}**: {value} "
        f"(league avg: {average}) — {direction_arrow}"
    )

st.caption(
    """
    These factors are calculated directly from the trained logistic
    regression model's real coefficients, showing how much each
    feature actually contributed to this specific prediction relative
    to league average - not hand-picked rules of thumb.
    """
)

st.subheader("Matchup-Specific Prediction vs. Season Context")

outcome_comparison = pd.DataFrame({
    "Metric": ["xwOBA", "xBA", "xwOBACON"],
    "Predicted (This Matchup)": [
        matchup_row["predicted_xwoba"],
        matchup_row["predicted_xba"],
        matchup_row["predicted_xwobacon"]
    ],
    f"{selected_batter}'s Season": [
        matchup_row["batter_season_xwoba"],
        matchup_row["batter_season_xba"],
        matchup_row["batter_season_xwobacon"]
    ],
    f"{selected_pitcher}'s Season Against": [
        matchup_row["pitcher_season_xwoba_against"],
        matchup_row["pitcher_season_xba_against"],
        matchup_row["pitcher_season_xwobacon_against"]
    ]
})

st.write("**Expected Outcome Metrics**")
show_table(outcome_comparison, use_container_width=True)

st.write(
    f"""
    This tells you how the specific pairing of **{selected_batter}** and
    **{selected_pitcher}** compares to each player's independent season
    performance. If the matchup-predicted numbers are notably higher than
    {selected_pitcher}'s season average against all hitters, that suggests
    this particular batter presents an above-average threat to this
    pitcher relative to their typical opponent - and vice versa if lower.
    """
)

st.write("**Plate Discipline & Approach**")

approach_comparison = pd.DataFrame({
    "Metric": ["K Rate", "BB Rate", "Chase Rate"],
    "Predicted (This Matchup)": [
        f"{matchup_row['predicted_k_probability']:.1%}",
        f"{matchup_row['predicted_bb_probability']:.1%}",
        "N/A"
    ],
    f"{selected_batter}'s Season": [
        f"{matchup_row['batter_k_rate']:.1%}",
        f"{matchup_row['batter_bb_rate']:.1%}",
        f"{matchup_row['batter_chase_rate']:.1%}"
    ],
    f"{selected_pitcher}'s Season": [
        f"{matchup_row['pitcher_k_rate']:.1%}",
        f"{matchup_row['pitcher_bb_rate']:.1%}",
        f"{matchup_row['pitcher_chase_rate']:.1%}"
    ]
})

show_table(approach_comparison, use_container_width=True)

st.caption(
    """
    K rate and BB rate now include matchup-specific model predictions,
    trained on real 2026 plate appearances. Chase rate remains
    season-context only, since it's a pitch-level behavior rather than
    a plate-appearance outcome, and would require a separate pitch-level
    model to predict on a per-matchup basis - noted as a future
    improvement in the methodology below.
    """
)


st.header(f"Pitch Selection Guide: How {selected_pitcher} Should Attack {selected_batter}")

hitter_pitch_types = pd.read_csv("data/hitter_pitch_type_splits.csv")
pitcher_pitch_types = pd.read_csv("data/pitcher_pitch_type_splits.csv")

this_hitter_pitches = hitter_pitch_types[
    hitter_pitch_types["batter_name"] == selected_batter
].copy()

this_pitcher_arsenal = pitcher_pitch_types[
    pitcher_pitch_types["pitcher_name"] == selected_pitcher
].copy()

st.subheader(f"{selected_pitcher}'s Recorded Arsenal")
st.caption("Every pitch type in the 2026 pitcher pitch-type summary is shown here. The recommendation below uses a narrower usage and batter-sample threshold.")
if not this_pitcher_arsenal.empty:
    arsenal_columns = [c for c in ("pitch_type", "usage_rate", "tendency_pitches", "performance_pa", "avg_velocity", "avg_spin_rate") if c in this_pitcher_arsenal.columns]
    arsenal_display = this_pitcher_arsenal.sort_values("usage_rate", ascending=False)[arsenal_columns]
    show_table(format_for_display(arsenal_display, keep_sample_size=True), use_container_width=True)

# Only consider pitch types this SPECIFIC pitcher actually throws -
# a hitter's weakness against a pitch type is irrelevant advice if
# the pitcher on the mound doesn't have that pitch in their arsenal.
pitcher_arsenal_types = set(this_pitcher_arsenal["pitch_type"].unique())

MIN_USAGE_FOR_RECOMMENDATION = 0.10

# Only consider pitches this pitcher throws at a meaningful rate -
# a pitch thrown 1-2% of the time isn't a real, usable recommendation
# even if it's technically in their arsenal.
meaningful_arsenal = this_pitcher_arsenal[
    this_pitcher_arsenal["usage_rate"] >= MIN_USAGE_FOR_RECOMMENDATION
]
pitcher_arsenal_types = set(meaningful_arsenal["pitch_type"].unique())

this_hitter_pitches_in_arsenal = this_hitter_pitches[
    this_hitter_pitches["pitch_type"].isin(pitcher_arsenal_types)
]

this_hitter_pitches_reliable = this_hitter_pitches_in_arsenal[
    this_hitter_pitches_in_arsenal["performance_pa"].notna()
    & (this_hitter_pitches_in_arsenal["performance_pa"] >= 25)
]

from report_helpers import PITCH_TYPE_NAMES

if len(this_pitcher_arsenal) == 0:
    st.info(f"No pitch-type data available for {selected_pitcher}.")
elif this_hitter_pitches_reliable["pitch_type"].nunique() < 2 or this_hitter_pitches_reliable["woba"].nunique() < 2:
    strength_pool = meaningful_arsenal.copy()
    if strength_pool.empty:
        strength_pool = this_pitcher_arsenal.copy()
    strength_pool = strength_pool[
        strength_pool["woba_against"].notna() & strength_pool["performance_pa"].ge(10)
    ] if {"woba_against", "performance_pa"}.issubset(strength_pool.columns) else strength_pool.iloc[0:0]
    if not strength_pool.empty:
        strongest = strength_pool.sort_values("woba_against").iloc[0]
        st.success(
            f"**Pitcher-strength suggestion: {PITCH_TYPE_NAMES.get(strongest['pitch_type'], strongest['pitch_type'])}** "
            f"— {selected_pitcher} has allowed a {strongest['woba_against']:.3f} wOBA on this pitch "
            f"({int(strongest['performance_pa'])} PA; {strongest['usage_rate']:.1%} usage)."
        )
    else:
        strongest = this_pitcher_arsenal.sort_values("usage_rate", ascending=False).iloc[0]
        st.info(
            f"**Most-used pitch: {PITCH_TYPE_NAMES.get(strongest['pitch_type'], strongest['pitch_type'])}** "
            f"({strongest['usage_rate']:.1%} usage). Pitcher outcome samples are too small for a strength ranking."
        )
    st.caption("The batter lacks two distinct qualifying pitch-type results (at least 25 PA each), so a batter-favored pitch is not identified.")
else:
    worst_pitch_for_hitter = this_hitter_pitches_reliable.sort_values("woba").iloc[0]
    best_pitch_for_hitter = this_hitter_pitches_reliable.sort_values("woba", ascending=False).iloc[0]

    # Pull this pitcher's actual usage rate for the recommended pitch,
    # so the suggestion reflects a pitch they genuinely feature, not
    # just something they've thrown once or twice.
    worst_pitch_usage = this_pitcher_arsenal[
        this_pitcher_arsenal["pitch_type"] == worst_pitch_for_hitter["pitch_type"]
    ]["usage_rate"].iloc[0]

    best_pitch_usage = this_pitcher_arsenal[
        this_pitcher_arsenal["pitch_type"] == best_pitch_for_hitter["pitch_type"]
    ]["usage_rate"].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.success(
            f"""
            **Best observed pitch for the pitcher: {PITCH_TYPE_NAMES.get(worst_pitch_for_hitter['pitch_type'], worst_pitch_for_hitter['pitch_type'])}**

            {selected_batter}'s wOBA against this pitch type:
            **{worst_pitch_for_hitter['woba']}**
            ({int(worst_pitch_for_hitter['performance_pa'])} PA sample).

            {selected_pitcher} throws this pitch **{worst_pitch_usage:.1%}** of the time.
            """
        )

    with col2:
        st.error(
            f"""
            **Best observed pitch for the batter: {PITCH_TYPE_NAMES.get(best_pitch_for_hitter['pitch_type'], best_pitch_for_hitter['pitch_type'])}**

            {selected_batter}'s wOBA against this pitch type:
            **{best_pitch_for_hitter['woba']}**
            ({int(best_pitch_for_hitter['performance_pa'])} PA sample).

            {selected_pitcher} throws this pitch **{best_pitch_usage:.1%}** of the time.
            """
        )

if not this_pitcher_arsenal.empty:
    st.write(f"**{selected_batter}'s results against {selected_pitcher}'s pitch types**")
    st.caption("All recorded arsenal pitch types appear here. Batter results combine opponents, not just this matchup. Recommendation samples need at least 25 PA per pitch type.")
    display_columns = [c for c in ("pitch_type", "woba", "xwoba", "whiff_rate", "hard_hit_rate", "performance_pa") if c in this_hitter_pitches.columns]
    breakdown = this_pitcher_arsenal[["pitch_type", "usage_rate"]].merge(
        this_hitter_pitches[display_columns], on="pitch_type", how="left"
    ).sort_values("usage_rate", ascending=False)
    breakdown["Recommendation Sample"] = breakdown["performance_pa"].map(
        lambda pa: "Yes" if pd.notna(pa) and pa >= 25 else "No"
    )
    show_table(format_for_display(breakdown, keep_sample_size=True), sticky_column="Pitch Type", use_container_width=True)

st.header(f"Pitch Sequencing: {selected_pitcher} vs. {selected_batter}")

st.write(
    """
    Explore the pitcher's recorded arsenal at each count. Count-specific
    rates describe pitches followed by another pitch in the same plate
    appearance; season usage is shown when that sample is absent. Choose
    a pitch and then its ball, strike, foul, or plate-appearance result.
    """
)

pitch_choice_df = pd.read_csv("data/sequencing_pitch_choice.csv")
outcome_df = pd.read_csv("data/sequencing_count_outcomes.csv")
hitter_pitch_type_by_count_df = pd.read_csv("data/hitter_pitch_type_by_count.csv")

this_pitcher_pitch_choices = pitch_choice_df[
    (pitch_choice_df["pitcher"] == matchup_row["pitcher"])
    & (pitch_choice_df["vs_stand"] == effective_bats)
]
this_pitcher_outcomes = outcome_df[
    (outcome_df["pitcher"] == matchup_row["pitcher"])
    & (outcome_df["vs_stand"] == effective_bats)
]

if this_pitcher_arsenal.empty:
    st.info(f"No recorded arsenal is available for {selected_pitcher}.")
else:
    st.caption(f"Observed continuing-pitch choices against {effective_bats}-handed batters; every recorded arsenal pitch remains selectable. An unobserved outcome has no estimated probability.")
    render_pitch_sequence_tree(
        pitch_choice_df=this_pitcher_pitch_choices,
        outcome_df=this_pitcher_outcomes,
        hitter_pitch_type_by_count_df=hitter_pitch_type_by_count_df,
        batter_name=selected_batter,
        pitcher_throws=matchup_row["throws"],
        key_prefix=f"seq_{selected_pitcher}_{selected_batter}",
        pitcher_arsenal=this_pitcher_arsenal,
    )

st.caption(
    """
    Count-specific rates are built from observed 2026 transitions for
    this pitcher against hitters of this handedness. Because ending
    pitches do not have a next pitch, these rates are conditional on
    the plate appearance continuing. Paths without such observations
    are exploratory and carry no estimated rate.
    """
)
st.header("Methodology")

st.write(
    """
    This tool uses four separate statistical models, all trained in R on
    real 2026 Statcast plate appearances: a logistic regression predicting
    success probability (reaching base via hit, walk, or hit-by-pitch),
    and three linear regressions predicting expected batting average
    (xBA), expected weighted on-base average (xwOBA), and expected wOBA
    on contact specifically (xwOBACON).

    Each model uses independent season-long features for both the batter
    (OPS, strikeout rate, chase rate, hard-hit rate, whiff rate) and the
    pitcher (whiff rate induced, chase rate induced, hard-hit rate
    allowed, strikeout rate, walk rate), along with whether the matchup
    is a platoon advantage for the batter (opposite-handed pairing).

    Platoon advantage was found to be a statistically significant
    predictor (p < 0.001) across all four models, consistent with
    well-established research on batter-pitcher handedness effects.
    """
)

st.header("Limitations")

st.write(
    """
    Predicting a single plate appearance is inherently difficult and a single at-bat's outcome
    is influenced by many factors beyond season-long tendencies (specific
    pitch sequencing, defensive positioning, park factors, and simple
    variance). In testing, these models explained only a small share of
    the variance in individual outcomes (R-squared values of roughly
    1-2%).
    """
)
