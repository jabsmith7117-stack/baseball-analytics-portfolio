import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from ui_theme import apply_theme, theme_colors
from roster_helpers import active_roster, roster_filter
from team_preferences import opening_team_index
from report_helpers import colorful_columns, show_table

apply_theme()
st.title("Pitcher Arsenal / Stuff+ Model")
st.write(
    "Explore pitch shapes for pitchers with 2026 Statcast data. "
    "Select a row to open that pitcher's full arsenal below."
)
st.info(
    "This is a custom Stuff+ score, not an official MLB or FanGraphs grade. "
    "It uses a pitch-type XGBoost model and a 100-centered scale. "
    "The underlying summary pools multiple seasons (2023–2026); it cannot be filtered "
    "to 2026 alone until scores are aggregated by season."
)

pitcher_stuff = pd.read_csv("data/pitcher_stuff_summary.csv")
pitcher_core = pd.read_csv("data/pitcher_core_stats.csv")
roster_snapshot = active_roster()
active_only = False
if roster_snapshot is not None:
    st.caption(f"Active MLB rosters checked {roster_snapshot['as_of_utc'].iloc[0]} UTC. Custom Stuff+ pools 2023–2026 pitches.")
    active_only = st.toggle("Show only current active rosters", value=True)
    if active_only:
        pitcher_core = roster_filter(pitcher_core, "pitcher", "current_team", roster_snapshot, pitchers=True)
    else:
        pitcher_core = roster_filter(pitcher_core, "pitcher", "current_team", None, pitchers=True)
else:
    st.caption("Showing 2026 pitchers with at least 50 recorded pitches; latest appearance is not an official active roster.")
    pitcher_core = roster_filter(pitcher_core, "pitcher", "current_team", None, pitchers=True)
roster = pitcher_core[["pitcher_name", "current_team"]].drop_duplicates()

# The scoring export uses "Last, First" while the roster uses "First Last".
# Match scored pitches to pitchers in the 2026 Statcast data.
def roster_name(name):
    if isinstance(name, str) and ", " in name:
        last, first = name.split(", ", 1)
        return f"{first} {last}"
    return name

# Pitchers with fewer than 20 completed PAs are omitted from the core-stat
# table, but they can still have a pitch type with 20+ scored pitches.
index_path = Path("data/appearance_index_2026.csv")
if index_path.exists():
    recent = pd.read_csv(index_path)
    recent = recent[recent.role.eq("Pitcher") & ~recent.qualified].copy()
    if roster_snapshot is not None and active_only:
        official_pitchers = roster_snapshot[
            roster_snapshot.position.eq("P") | roster_snapshot.position_type.eq("Pitcher")
        ][["player_id", "team"]]
        recent = recent.merge(official_pitchers, on="player_id", how="inner")
        recent["current_team"] = recent["team"]
    else:
        recent["current_team"] = recent["last_team"]
        if roster_snapshot is not None:
            non_pitchers = roster_snapshot.loc[
                ~(roster_snapshot.position.eq("P") | roster_snapshot.position_type.eq("Pitcher")),
                "player_id",
            ]
            recent = recent[~recent.player_id.isin(non_pitchers)]
    recent["pitcher_name"] = recent["name"].map(roster_name)
    roster = pd.concat([roster, recent[["pitcher_name", "current_team"]]], ignore_index=True)
    roster = roster.drop_duplicates(subset="pitcher_name", keep="first")

pitcher_stuff["pitcher_name"] = pitcher_stuff["player_name"].map(roster_name)
pitcher_stuff = pitcher_stuff.merge(roster, on="pitcher_name", how="inner", validate="many_to_one")

st.header("Pitchers")
team_options = ["All teams"] + sorted(pitcher_stuff["current_team"].dropna().unique())
selected_team = st.selectbox("Team", team_options, index=opening_team_index(team_options))
visible = pitcher_stuff if selected_team == "All teams" else pitcher_stuff[
    pitcher_stuff["current_team"] == selected_team
]
visible = visible.sort_values("avg_stuff_plus", ascending=False).reset_index(drop=True)

view = visible[[
    "pitcher_name", "current_team", "pitch_type", "avg_stuff_plus",
    "avg_velocity", "avg_spin_rate", "usage_rate", "pitch_count"
]].rename(columns={
    "pitcher_name": "Pitcher", "current_team": "Team", "pitch_type": "Pitch Type",
    "avg_stuff_plus": "Custom Stuff+", "avg_velocity": "Avg Velocity (mph)",
    "avg_spin_rate": "Avg Spin Rate (rpm)", "usage_rate": "Usage Rate",
    "pitch_count": "Pitch Count"
})
view["Usage Rate"] = view["Usage Rate"] * 100

event = st.dataframe(
    view, hide_index=True, use_container_width=True, on_select="rerun",
    selection_mode="single-row", key=f"arsenal_overview_{selected_team}",
    column_config=colorful_columns(view, {
        "Pitcher": st.column_config.TextColumn("Pitcher", pinned=True, width="medium"),
        "Usage Rate": st.column_config.NumberColumn("Usage Rate", format="%.1f%%"),
        "Custom Stuff+": st.column_config.NumberColumn("Custom Stuff+", format="%.1f"),
    }),
)

pitcher_options = sorted(visible["pitcher_name"].unique())
if not pitcher_options:
    st.warning("No rostered pitchers match this team.")
    st.stop()

if st.session_state.get("arsenal_pitcher") not in pitcher_options:
    st.session_state["arsenal_pitcher"] = pitcher_options[0]

rows = event.selection.rows
selected_row = (selected_team, rows[0]) if rows else None
if selected_row is not None and selected_row != st.session_state.get("last_arsenal_row"):
    st.session_state["arsenal_pitcher"] = visible.iloc[rows[0]]["pitcher_name"]
    st.session_state["last_arsenal_row"] = selected_row

selected_pitcher = st.selectbox("Selected pitcher", pitcher_options, key="arsenal_pitcher")
pitcher_data = visible[visible["pitcher_name"] == selected_pitcher].sort_values(
    "usage_rate", ascending=False
)

if index_path.exists():
    if selected_pitcher in set(recent["pitcher_name"]):
        st.warning("Limited MLB sample: each displayed pitch type has at least 20 scored pitches, but this pitcher has fewer than 20 completed plate appearances. Treat the grades as exploratory.")

st.header(f"{selected_pitcher} Arsenal")
best_pitch_row = pitcher_data.sort_values("avg_stuff_plus", ascending=False).iloc[0]
primary_pitch_row = pitcher_data.iloc[0]
col1, col2, col3 = st.columns(3)
col1.metric("Best Pitch (Custom Stuff+)", f"{best_pitch_row['pitch_type']}: {best_pitch_row['avg_stuff_plus']:.1f}")
col2.metric("Primary Pitch", f"{primary_pitch_row['pitch_type']} ({primary_pitch_row['usage_rate']:.1%} usage)")
col3.metric("Pitch Types Tracked", len(pitcher_data))

arsenal = pitcher_data[[
    "pitch_type", "avg_stuff_plus", "avg_velocity", "avg_spin_rate",
    "usage_rate", "pitch_count"
]].rename(columns={
    "pitch_type": "Pitch Type", "avg_stuff_plus": "Custom Stuff+",
    "avg_velocity": "Avg Velocity (mph)", "avg_spin_rate": "Avg Spin Rate (rpm)",
    "usage_rate": "Usage Rate", "pitch_count": "Pitch Count"
})
arsenal["Usage Rate"] = arsenal["Usage Rate"] * 100
arsenal["Usage Rate"] = arsenal["Usage Rate"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
arsenal["Custom Stuff+"] = arsenal["Custom Stuff+"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
show_table(arsenal)

st.header("Arsenal Breakdown")
arsenal_fig = px.bar(
    pitcher_data, x="pitch_type", y="avg_stuff_plus", text="avg_stuff_plus",
    labels={"pitch_type": "Pitch Type", "avg_stuff_plus": "Custom Stuff+"},
    title=f"{selected_pitcher} Custom Stuff+ by Pitch Type",
    color_discrete_sequence=[theme_colors()[0]],
)
arsenal_fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
arsenal_fig.add_hline(y=100, line_dash="dash", line_color=theme_colors()[1],
                      annotation_text="Model average (100)")
arsenal_fig.update_layout(showlegend=False, plot_bgcolor="white")
st.plotly_chart(arsenal_fig, use_container_width=True)
