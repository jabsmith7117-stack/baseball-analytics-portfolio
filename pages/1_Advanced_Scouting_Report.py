import streamlit as st
import pandas as pd
from report_helpers import format_for_display, render_count_tree, show_table
from ui_theme import apply_theme
from roster_helpers import active_roster, roster_filter
from team_preferences import opening_team_index

apply_theme()

st.title("Advanced Scouting Report")
st.caption("N/A or blank means the underlying Statcast field was missing or that the split did not have enough eligible observations. It does not mean the player never saw or threw that pitch. Check sample sizes before drawing conclusions.")

st.write(
    """
    This tool generates opponent scouting reports using real Statcast
    pitch-level data from the 2023-2026 seasons, covering hitter and
    pitcher tendencies by platoon, pitch type, zone, count, release
    angle, and velocity.
    """
)

# Load core datasets needed for team/player selection.
hitter_core = pd.read_csv("data/hitter_core_stats.csv")
pitcher_core = pd.read_csv("data/pitcher_core_stats.csv")
roster = active_roster()
active_only = False
if roster is not None:
    st.caption(f"Active MLB rosters checked {roster['as_of_utc'].iloc[0]} UTC. Season statistics cover recorded 2026 games; newly called up players appear after they have sufficient Statcast data.")
    active_only = st.toggle("Show only current active rosters", value=True)
    if active_only:
        hitter_core = roster_filter(hitter_core, "batter", "current_team", roster)
        pitcher_core = roster_filter(pitcher_core, "pitcher", "current_team", roster, pitchers=True)
    else:
        pitcher_core = roster_filter(pitcher_core, "pitcher", "current_team", None, pitchers=True)
else:
    st.caption("Team assignments use each player's latest recorded 2026 appearance, not an official active roster. Run scripts/update_active_rosters.py to add a dated roster snapshot.")
    pitcher_core = roster_filter(pitcher_core, "pitcher", "current_team", None, pitchers=True)

st.header("Select Opponent")

all_teams = sorted(hitter_core["current_team"].dropna().unique())

selected_team = st.selectbox("Opponent Team", all_teams, index=opening_team_index(all_teams))

team_hitters = hitter_core[hitter_core["current_team"] == selected_team]
team_pitchers = pitcher_core[pitcher_core["current_team"] == selected_team]

tab_hitters, tab_pitchers = st.tabs(["Opponent Hitters", "Opponent Pitchers"])

with tab_hitters:
    st.subheader(f"{selected_team} Hitters")

    hitter_options = sorted(team_hitters["batter_name"].unique())
    selected_hitter = st.selectbox("Select A Hitter", hitter_options)

    hitter_row = team_hitters[team_hitters["batter_name"] == selected_hitter].iloc[0]
    selected_batter_id = hitter_row["batter"]

    st.caption("The selected player appears first in the core table. Each split table keeps its identifying column visible as you scroll across.")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("wOBA", f"{hitter_row['woba']:.3f}")
    col2.metric("xwOBA", f"{hitter_row['xwoba']:.3f}")
    col3.metric("OPS", f"{hitter_row['ops']:.3f}")
    col4.metric("K Rate", f"{hitter_row['k_rate']:.1%}")
    col5.metric("Hard-Hit Rate", f"{hitter_row['hard_hit_rate']:.1%}")

    (
        h_core, h_platoon, h_pitch_type, h_zone,
        h_count, h_release, h_velocity
    ) = st.tabs([
        "Core", "Platoon", "Pitch Type", "Zone",
        "Count", "Release Angle", "Velocity"
    ])

    with h_core:
        display_df = format_for_display(
            team_hitters.assign(selected=team_hitters["batter"].eq(selected_batter_id))
            .sort_values(["selected", "woba"], ascending=[False, False])
            .drop(columns="selected")
        )
        show_table(display_df, use_container_width=True)

    with h_platoon:
        platoon_df = pd.read_csv("data/hitter_platoon_splits.csv")
        this_hitter_platoon = platoon_df[platoon_df["batter"] == selected_batter_id]
        st.write(f"**{selected_hitter} vs. LHP / RHP**")
        show_table(format_for_display(this_hitter_platoon), sticky_column="Vs. Throws", use_container_width=True)

    with h_pitch_type:
        pitch_type_df = pd.read_csv("data/hitter_pitch_type_splits.csv")
        this_hitter_pitch_type = pitch_type_df[pitch_type_df["batter"] == selected_batter_id]
        st.write(f"**{selected_hitter} By Pitch Type**")
        sort_col = "woba" if "woba" in this_hitter_pitch_type.columns else "pct_of_pitches_seen"
        show_table(
            format_for_display(this_hitter_pitch_type.sort_values(sort_col, ascending=False)),
            sticky_column="Pitch Type",
            use_container_width=True
        )

    with h_zone:
        zone_df = pd.read_csv("data/hitter_zone_splits.csv")
        this_hitter_zone = zone_df[zone_df["batter"] == selected_batter_id]
        st.write(f"**{selected_hitter} By Zone**")
        show_table(
            format_for_display(this_hitter_zone.sort_values("zone"), keep_sample_size=True, extra_drop=["in_strike_zone"]),
            sticky_column="Location",
            use_container_width=True
        )

    with h_count:
        count_group_df = pd.read_csv("data/hitter_count_group_splits.csv")
        this_hitter_count = count_group_df[count_group_df["batter"] == selected_batter_id]
        st.write(f"**{selected_hitter} By Count Situation**")
        show_table(format_for_display(this_hitter_count), sticky_column="Count Situation", use_container_width=True)
        st.caption("N/A means this split has no eligible result for that metric; pitch usage may still be available.")

        st.write("**Count Progression**")
        raw_count_df = pd.read_csv("data/hitter_raw_count_splits.csv")
        this_hitter_raw_count = raw_count_df[raw_count_df["batter"] == selected_batter_id]
        render_count_tree(this_hitter_raw_count, key_prefix=f"hitter_{selected_batter_id}")

        with st.expander("View Full Count Table Instead"):
            show_table(format_for_display(this_hitter_raw_count), sticky_column="Count", use_container_width=True)
    with h_release:
        release_df = pd.read_csv("data/hitter_release_angle_splits.csv")
        this_hitter_release = release_df[release_df["batter"] == selected_batter_id]
        st.write(f"**{selected_hitter} By Pitcher Release Angle**")
        show_table(format_for_display(this_hitter_release), sticky_column="Release Angle", use_container_width=True)

    with h_velocity:
        velocity_df = pd.read_csv("data/hitter_velocity_splits.csv")
        this_hitter_velocity = velocity_df[velocity_df["batter"] == selected_batter_id]
        st.write(f"**{selected_hitter} By Pitch Velocity Band**")
        show_table(
            format_for_display(
                this_hitter_velocity.sort_values(["pitch_type", "velocity_band"])
            ),
            sticky_column="Pitch Type",
            use_container_width=True
        )

with tab_pitchers:
    st.subheader(f"{selected_team} Pitchers")

    pitcher_options = sorted(team_pitchers["pitcher_name"].unique())
    selected_pitcher = st.selectbox("Select A Pitcher", pitcher_options)

    pitcher_row = team_pitchers[team_pitchers["pitcher_name"] == selected_pitcher].iloc[0]
    selected_pitcher_id = pitcher_row["pitcher"]

    st.caption("The selected player appears first. Scroll across the table; Player stays visible.")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("wOBA Against", f"{pitcher_row['woba_against']:.3f}")
    col2.metric("xwOBA Against", f"{pitcher_row['xwoba_against']:.3f}")
    col3.metric("OPS Against", f"{pitcher_row['ops_against']:.3f}")
    col4.metric("K Rate", f"{pitcher_row['k_rate']:.1%}")
    col5.metric("CSW Rate", f"{pitcher_row['csw_rate']:.1%}")

    (
        p_core, p_platoon, p_pitch_type, p_zone, p_count
    ) = st.tabs([
        "Core", "Platoon", "Pitch Type", "Zone", "Count"
    ])

    with p_core:
        display_df = format_for_display(
            team_pitchers.assign(selected=team_pitchers["pitcher"].eq(selected_pitcher_id))
            .sort_values(["selected", "woba_against"], ascending=[False, True])
            .drop(columns="selected")
        )
        show_table(display_df, use_container_width=True)

    with p_platoon:
        platoon_df = pd.read_csv("data/pitcher_platoon_splits.csv")
        this_pitcher_platoon = platoon_df[platoon_df["pitcher"] == selected_pitcher_id]
        st.write(f"**{selected_pitcher} vs. LHH / RHH**")
        show_table(format_for_display(this_pitcher_platoon), sticky_column="Vs. Stand", use_container_width=True)

    with p_pitch_type:
        pitch_type_df = pd.read_csv("data/pitcher_pitch_type_splits.csv")
        this_pitcher_pitch_type = pitch_type_df[pitch_type_df["pitcher"] == selected_pitcher_id]
        st.write(f"**{selected_pitcher} Arsenal**")
        sort_col = "usage_rate" if "usage_rate" in this_pitcher_pitch_type.columns else "pitch_type"
        show_table(
            format_for_display(this_pitcher_pitch_type.sort_values(sort_col, ascending=False)),
            sticky_column="Pitch Type",
            use_container_width=True
        )

    with p_zone:
        zone_df = pd.read_csv("data/pitcher_zone_splits.csv")
        this_pitcher_zone = zone_df[zone_df["pitcher"] == selected_pitcher_id]
        st.write(f"**{selected_pitcher} By Zone**")
        sort_col = "location_usage_rate" if "location_usage_rate" in this_pitcher_zone.columns else "zone"
        show_table(
            format_for_display(
                this_pitcher_zone.sort_values(sort_col, ascending=False),
                keep_sample_size=True, extra_drop=["in_strike_zone"]
            ),
            sticky_column="Location",
            use_container_width=True
        )

    with p_count:
        count_group_df = pd.read_csv("data/pitcher_count_group_splits.csv")
        this_pitcher_count = count_group_df[count_group_df["pitcher"] == selected_pitcher_id]

        handedness_filter = st.radio(
            "Show tendencies against:",
            ["Right-Handed Hitters", "Left-Handed Hitters"],
            horizontal=True,
            key="pitcher_count_handedness"
        )
        stand_value = "R" if handedness_filter == "Right-Handed Hitters" else "L"

        filtered_count = this_pitcher_count[this_pitcher_count["vs_stand"] == stand_value]

        st.write(f"**{selected_pitcher} By Count Situation ({handedness_filter})**")
        st.caption("Grouped performance uses plate appearances ending on a pitch thrown in the group. N/A means the split lacks enough completed appearances.")
        show_table(
            format_for_display(filtered_count, extra_drop=["vs_stand"]),
            sticky_column="Count Situation",
            use_container_width=True
        )

        st.write("**Count Progression**")
        raw_count_df = pd.read_csv("data/pitcher_raw_count_splits.csv")
        this_pitcher_raw_count = raw_count_df[raw_count_df["pitcher"] == selected_pitcher_id]
        filtered_raw_count = this_pitcher_raw_count[this_pitcher_raw_count["vs_stand"] == stand_value]
        st.caption("Exact-count table uses 2026 data. Outcomes follow each plate appearance to its finish; pitch and swing measures describe pitches thrown at the selected count.")
        render_count_tree(filtered_raw_count, key_prefix=f"pitcher_{selected_pitcher_id}_{stand_value}")

        with st.expander("View Full Count Table Instead"):
            st.info(
                "**How to read this table:** Sample Size (Pitches) counts pitches thrown "
                "at this count. Sample Size (PA) counts plate appearances that reached it, including "
                "outcomes on later pitches. The sample can be small. At Bats excludes walks "
                "and other non-at-bat results, so zero hits and a .000 AVG can occur alongside "
                "a positive wOBA. N/A for Whiff Rate means no qualifying swings at that count; "
                "N/A for Hard-Hit Rate or Exit Velocity means no qualifying balls in play "
                "at that count. These values do not describe every pitch in the appearance."
            )
            show_table(
                format_for_display(filtered_raw_count, extra_drop=["vs_stand"], keep_sample_size=True),
                sticky_column="Count",
                use_container_width=True
            )
