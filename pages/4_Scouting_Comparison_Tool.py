from ui_theme import apply_theme, theme_colors
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from roster_helpers import active_roster, roster_filter
from report_helpers import show_table

apply_theme()

st.title("Scouting Comparison Tool")

st.write(
    """
    This tool uses a real SQL database built from 2026 Statcast data to support
    player evaluation, undervalued hitter discovery, and statistical player
    comparisons.
    """
)

connection = sqlite3.connect("sql/baseball_real.db")
roster = active_roster()
show_active = False
if roster is not None:
    st.caption(f"Active MLB rosters checked {roster['as_of_utc'].iloc[0]} UTC; SQL statistics cover 2026 appearances through the data refresh.")
    show_active = st.toggle("Show only current active rosters", value=True)
else:
    st.caption("The SQL database uses latest 2026 appearance for team assignment; it is not an official active roster.")

total_hitters = pd.read_sql_query("SELECT COUNT(*) AS count FROM hitters", connection)["count"].iloc[0]
total_pitchers = pd.read_sql_query("SELECT COUNT(*) AS count FROM pitchers", connection)["count"].iloc[0]
qualified_hitters = pd.read_sql_query("SELECT COUNT(*) AS count FROM hitter_profile", connection)["count"].iloc[0]

table_count = pd.read_sql_query(
    """
    SELECT COUNT(*) AS count
    FROM sqlite_master
    WHERE type = 'table'
    """,
    connection
)["count"].iloc[0]

st.header("Database Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Hitters", total_hitters)
col2.metric("Pitchers", total_pitchers)
col3.metric("Qualified Hitters", qualified_hitters)
col4.metric("SQL Tables", table_count)

tab_gaps, tab_similarity = st.tabs(["Expected Production Gaps", "Player Comp Finder"])

with tab_gaps:
    st.header("Expected vs. Observed Production")
    st.write("A positive xwOBA − wOBA gap means expected production is higher than observed production; a negative gap means observed production is higher. These are exploratory differences, not proof of future performance.")

    gaps_query = """
    SELECT hitters.batter_id, hitters.batter_name, hitters.bats,
           teams.team_abbr, hitter_season_stats.total_pa,
           hitter_season_stats.woba, hitter_season_stats.xwoba,
           hitter_season_stats.barrel_rate, hitter_season_stats.hard_hit_rate,
           hitter_season_stats.avg_bat_speed,
           (hitter_season_stats.xwoba - hitter_season_stats.woba) AS xwoba_gap
    FROM hitters
    JOIN teams ON hitters.team_abbr = teams.team_abbr
    JOIN hitter_season_stats ON hitters.batter_id = hitter_season_stats.batter_id
    WHERE hitter_season_stats.total_pa >= 50
      AND hitter_season_stats.woba IS NOT NULL
      AND hitter_season_stats.xwoba IS NOT NULL
    ORDER BY xwoba_gap DESC
    """
    with st.expander("View SQL query for this analysis"):
        st.code(gaps_query, language="sql")
    gaps = pd.read_sql_query(gaps_query, connection)
    if show_active:
        gaps = roster_filter(gaps, "batter_id", "team_abbr", roster)

    min_pa = st.slider("Minimum Plate Appearances", 50, 300, 100, 25)
    gap_size = st.slider("Minimum absolute xwOBA gap", 0.0, 0.10, 0.0, 0.005)
    direction = st.radio("Show", ["Both directions", "Expected higher", "Observed higher"], horizontal=True)
    qualified = gaps[gaps.total_pa.ge(min_pa)].copy()
    positive_count = int(qualified.xwoba_gap.gt(0).sum())
    negative_count = int(qualified.xwoba_gap.lt(0).sum())
    st.write(f"Among **{len(qualified)}** players meeting the plate-appearance threshold, **{positive_count}** have expected production above observed production and **{negative_count}** have observed production above expected production.")
    filtered = qualified[qualified.xwoba_gap.abs().ge(gap_size)].copy()
    if direction == "Expected higher":
        filtered = filtered[filtered.xwoba_gap.gt(0)]
    elif direction == "Observed higher":
        filtered = filtered[filtered.xwoba_gap.lt(0)]

    st.subheader("Players matching these filters")
    shown = filtered[["batter_name", "team_abbr", "bats", "total_pa", "woba", "xwoba", "xwoba_gap", "barrel_rate", "hard_hit_rate"]].copy()
    shown = shown.rename(columns={"batter_name": "Player", "team_abbr": "Team", "bats": "Bats", "total_pa": "PA", "woba": "wOBA", "xwoba": "xwOBA", "xwoba_gap": "xwOBA Gap", "barrel_rate": "Barrel Rate", "hard_hit_rate": "Hard-Hit Rate"})
    for col in ("wOBA", "xwOBA", "xwOBA Gap"):
        shown[col] = shown[col].map(lambda x: f"{x:+.3f}" if col == "xwOBA Gap" else f"{x:.3f}")
    for col in ("Barrel Rate", "Hard-Hit Rate"):
        shown[col] = shown[col].map(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
    show_table(shown)
    if not filtered.empty:
        chart_data = pd.concat([filtered.nlargest(10, "xwoba_gap"), filtered.nsmallest(10, "xwoba_gap")]).drop_duplicates("batter_id")
        chart_data = chart_data.sort_values("xwoba_gap")
        fig = px.bar(chart_data, x="xwoba_gap", y="batter_name", orientation="h",
                     color="xwoba_gap", color_continuous_scale=[theme_colors()[0], "#f5f8fc", theme_colors()[1]],
                     color_continuous_midpoint=0,
                     labels={"xwoba_gap": "xwOBA − wOBA", "batter_name": "Player"},
                     title="Largest gaps in the filtered group")
        fig.update_traces(hovertemplate="%{y}<br>xwOBA − wOBA: %{x:.3f}<extra></extra>")
        fig.update_yaxes(tickmode="array", tickvals=chart_data["batter_name"].tolist(),
                         ticktext=chart_data["batter_name"].tolist(), automargin=True)
        fig.update_layout(yaxis_title=None, coloraxis_showscale=False,
                          height=max(600, len(chart_data) * 34 + 130), margin=dict(l=150, r=35, t=70, b=55))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No players match these filters. Lower the minimum gap or plate-appearance threshold.")

with tab_similarity:
    st.header("Player Comp Finder")

    st.write(
        """
        Select a hitter to find statistically similar players based on a
        multi-dimensional hitting profile. This section answers a different
        question than the expected production gap tab: who looks like this
        player statistically?
        """
    )

    hitter_profile_df = pd.read_sql_query("SELECT * FROM hitter_profile", connection)
    st.caption("Comparisons include 2026 hitters with complete profiles, including players currently injured or off the active roster.")

    similarity_features = [
        "woba",
        "k_rate",
        "chase_rate",
        "hard_hit_rate",
        "barrel_rate",
        "avg_bat_speed",
        "avg_swing_length"
    ]

    comparison_pool = hitter_profile_df.dropna(subset=similarity_features).copy()

    player_options = sorted(comparison_pool["batter_name"].unique())
    selected_player = st.selectbox("Select A Hitter", player_options)

    target_row = comparison_pool[comparison_pool["batter_name"] == selected_player].iloc[0]
    others = comparison_pool[comparison_pool["batter_name"] != selected_player].copy()

    for feature in similarity_features:
        feature_mean = comparison_pool[feature].mean()
        feature_std = comparison_pool[feature].std()

        others[f"{feature}_scaled"] = (others[feature] - feature_mean) / feature_std
        target_scaled_value = (target_row[feature] - feature_mean) / feature_std
        others[f"{feature}_target_diff_sq"] = (
            others[f"{feature}_scaled"] - target_scaled_value
        ) ** 2

    diff_columns = [f"{feature}_target_diff_sq" for feature in similarity_features]
    others["distance"] = others[diff_columns].sum(axis=1) ** 0.5

    max_results = st.slider(
        "Number Of Similar Players To Show",
        min_value=5,
        max_value=25,
        value=10,
        step=5
    )

    show_hidden_gems_only = st.checkbox(
        "Show Hidden Gem Candidates",
        value=False
    )
    st.caption("Filter: fewer than 300 PA, fewer PA than the selected hitter, and xwOBA at least .030 above wOBA. This does not identify an unknown or undervalued player; established stars can meet the same criteria after an injury-shortened season.")

    similarity_results = others.sort_values("distance").copy()

    if show_hidden_gems_only:
        similarity_results = similarity_results[
            (similarity_results["total_pa"] < min(300, target_row["total_pa"]))
            & (similarity_results["xwoba_gap"] >= 0.030)
        ]

    most_similar = similarity_results.head(max_results)

    st.subheader(f"Players Most Similar To {selected_player}")

    nearest_display = most_similar[
            [
                "batter_name",
                "team_abbr",
                "bats",
                "total_pa",
                "woba",
                "xwoba",
                "barrel_rate",
                "avg_bat_speed",
                "avg_swing_length",
                "distance"
            ]
        ].copy().rename(columns={
            "batter_name": "Player", "team_abbr": "Team", "bats": "Bats",
            "total_pa": "PA", "woba": "wOBA", "xwoba": "xwOBA",
            "barrel_rate": "Barrel Rate", "avg_bat_speed": "Avg Bat Speed (mph)",
            "avg_swing_length": "Avg Swing Length (ft)", "distance": "Similarity Distance"
        })
    nearest_display["Barrel Rate"] = nearest_display["Barrel Rate"].map(lambda x: f"{x:.1%}")
    nearest_display["Similarity Distance"] = nearest_display["Similarity Distance"].map(
        lambda x: f"{float(x):.4f}" if pd.notna(x) else "N/A"
    )
    show_table(nearest_display)

    st.subheader("Selected Player vs Similar Players")

    target_comparison = target_row[
        [
            "batter_name",
            "team_abbr",
            "bats",
            "woba",
            "k_rate",
            "chase_rate",
            "hard_hit_rate",
            "barrel_rate",
            "avg_bat_speed",
            "avg_swing_length"
        ]
    ].to_frame().T

    target_comparison["comparison_type"] = "Selected Player"
    target_comparison["distance"] = 0.0

    similar_comparison = most_similar[
        [
            "batter_name",
            "team_abbr",
            "bats",
            "woba",
            "k_rate",
            "chase_rate",
            "hard_hit_rate",
            "barrel_rate",
            "avg_bat_speed",
            "avg_swing_length",
            "distance"
        ]
    ].copy()

    similar_comparison["comparison_type"] = "Similar Player"

    comparison_table = pd.concat(
        [target_comparison, similar_comparison],
        ignore_index=True
    )

    comparison_table = comparison_table[
        [
            "comparison_type",
            "batter_name",
            "team_abbr",
            "bats",
            "woba",
            "k_rate",
            "chase_rate",
            "hard_hit_rate",
            "barrel_rate",
            "avg_bat_speed",
            "avg_swing_length",
            "distance"
        ]
    ]

    comparison_display = comparison_table.rename(columns={
        "comparison_type": "Role", "batter_name": "Player", "team_abbr": "Team",
        "bats": "Bats", "woba": "wOBA", "k_rate": "K Rate",
        "chase_rate": "Chase Rate", "hard_hit_rate": "Hard-Hit Rate",
        "barrel_rate": "Barrel Rate", "avg_bat_speed": "Avg Bat Speed (mph)",
        "avg_swing_length": "Avg Swing Length (ft)", "distance": "Similarity Distance"
    }).copy()
    for col in ("K Rate", "Chase Rate", "Hard-Hit Rate", "Barrel Rate"):
        comparison_display[col] = comparison_display[col].map(lambda x: f"{float(x):.1%}" if pd.notna(x) else "N/A")
    for col in ("Avg Bat Speed (mph)", "Avg Swing Length (ft)"):
        comparison_display[col] = comparison_display[col].map(lambda x: f"{float(x):.1f}" if pd.notna(x) else "N/A")
    for col in ("wOBA",):
        comparison_display[col] = comparison_display[col].map(lambda x: f"{float(x):.3f}" if pd.notna(x) else "N/A")
    comparison_display["Similarity Distance"] = comparison_display["Similarity Distance"].map(lambda x: f"{float(x):.4f}" if pd.notna(x) else "N/A")
    comparison_display = comparison_display[["Player"] + [c for c in comparison_display.columns if c != "Player"]]
    st.caption("The selected player is highlighted first. The Player column remains visible when you scroll across.")
    show_table(comparison_display)
    if len(others) > 0:
        closest_name = others.sort_values("distance").iloc[0]["batter_name"]
        comparison_names = sorted(others["batter_name"].unique())
        comparison_name = st.selectbox("Compare selected hitter with", comparison_names,
                                       index=comparison_names.index(closest_name))
        comparison_row = comparison_pool[comparison_pool["batter_name"] == comparison_name].iloc[0]

        st.subheader("Feature Comparison")

        feature_labels = {
            "woba": "wOBA",
            "k_rate": "K Rate",
            "chase_rate": "Chase Rate",
            "hard_hit_rate": "Hard-Hit Rate",
            "barrel_rate": "Barrel Rate",
            "avg_bat_speed": "Avg Bat Speed",
            "avg_swing_length": "Avg Swing Length"
        }

        # Normalize each feature using the comparison pool, so speed in mph
        # cannot visually overwhelm rates that range from 0 to 1.
        heatmap_rows = []
        for feature in similarity_features:
            mean = comparison_pool[feature].mean()
            std = comparison_pool[feature].std()
            if not pd.notna(std) or std == 0:
                continue
            for player_name, row in ((selected_player, target_row),
                                     (comparison_name, comparison_row)):
                value = float(row[feature])
                label = f"{value:.1%}" if feature in {"k_rate", "chase_rate", "hard_hit_rate", "barrel_rate"} else f"{value:.3f}" if feature == "woba" else f"{value:.1f}"
                heatmap_rows.append({"Feature": feature_labels[feature], "Player": player_name,
                                     "Standardized value": (value - mean) / std, "Observed": label})
        heatmap = pd.DataFrame(heatmap_rows)
        fig = px.imshow(
            heatmap.pivot(index="Player", columns="Feature", values="Standardized value"),
            color_continuous_scale=[theme_colors()[0], "#f5f8fc", theme_colors()[1]],
            color_continuous_midpoint=0, aspect="auto",
            labels={"color": "Standard deviations from pool"},
            title=f"{selected_player} vs. {comparison_name}, relative to the player pool",
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Each column uses its own league-pool scale; red indicates above the pool average and navy below. Higher is not necessarily better for every feature, especially strikeout and chase rates. Exact values appear in the comparison table above.")
    st.subheader("Similarity Distance")

    similarity_chart_df = most_similar.sort_values("distance", ascending=True)

    similarity_fig = px.bar(
        similarity_chart_df,
        x="distance",
        y="batter_name",
        orientation="h",
        text="distance",
        labels={
            "distance": "Similarity Distance",
            "batter_name": "Hitter"
        },
        title=f"Closest Statistical Matches To {selected_player}"
    )

    similarity_fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")

    similarity_fig.update_layout(
        showlegend=False, yaxis_title=None,
        height=max(500, len(similarity_chart_df) * 34 + 130),
        margin=dict(l=155, r=65, t=70, b=55),
    )
    similarity_fig.update_yaxes(
        autorange="reversed", tickmode="array",
        tickvals=similarity_chart_df["batter_name"].tolist(),
        ticktext=similarity_chart_df["batter_name"].tolist(),
        automargin=True,
    )

    st.plotly_chart(similarity_fig, use_container_width=True)

    st.caption(
        """
        Lower distance means a closer statistical match across the selected
        hitting profile features.
        """
    )

    if show_hidden_gems_only and len(most_similar) > 0:
        top_gem = most_similar.iloc[0]

        st.subheader("Closest lower-PA positive-gap comp")

        st.write(
            f"""
            **{top_gem["batter_name"]}** is the closest player matching the lower-PA positive-gap filter to
            **{selected_player}** based on this similarity model.

            He has a similarity distance of **{top_gem["distance"]:.2f}**, an
            xwOBA gap of **{top_gem["xwoba_gap"]:.3f}**, and has accumulated
            **{int(top_gem["total_pa"])}** plate appearances compared with
            **{int(target_row["total_pa"])}** for {selected_player}.

            This is an exploratory statistical comparison. It does not establish that this player is overlooked or undervalued.
            """
        )
    elif show_hidden_gems_only and len(most_similar) == 0:
        st.info(
            "No players met the lower-PA positive-gap filter for this comparison. Choose another hitter or turn off the filter."
        )

    with st.expander("View actual SQL view used for player comparisons"):
        view_sql = pd.read_sql_query(
            "SELECT sql FROM sqlite_master WHERE type = 'view' AND name = 'hitter_profile'",
            connection,
        )
        if not view_sql.empty:
            st.code(view_sql.iloc[0]["sql"], language="sql")
        else:
            st.info("The hitter profile SQL view is not present in this database.")
        st.caption("The SQL view joins player and season records. Python then standardizes the seven features and calculates similarity distance.")

connection.close()

st.header("Methodology")

st.write(
    """
    This tool is built on a real SQLite database containing qualified hitters
    and pitchers from the 2026 MLB season, sourced from Statcast pitch-level
    data.

    The Expected Production Gaps tab uses a SQL join and a signed xwOBA minus wOBA difference to show both expected-above-observed and observed-above-expected production.

    The Player Comp Finder uses the SQL hitter_profile view as its source data,
    then applies a standardized distance calculation across seven hitting
    profile features.
    """
)

st.header("Limitations")

st.write(
    """
    This database reflects 2026 games through the most recent local data refresh, so some player samples remain limited. A positive xwOBA gap is a useful scouting flag, not a
    guarantee of future performance.

    The similarity model weighs all selected features equally after
    standardization. A more advanced version could weight features based on
    predictive importance or role-specific scouting needs.
    """
)
