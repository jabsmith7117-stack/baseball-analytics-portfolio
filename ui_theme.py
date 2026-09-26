"""Team-inspired palettes selected by the optional opening-team link."""

import streamlit as st

DEFAULT = ("#0C2340", "#C8102E")
TEAM_PALETTES = {
    "ATH": ("#006141", "#FFB81C"), "OAK": ("#006141", "#FFB81C"),
    "ATL": ("#13274F", "#CE1141"), "AZ": ("#A71930", "#27251F"),
    "BAL": ("#27251F", "#DF4601"), "BOS": ("#0C2340", "#BD3039"),
    "CHC": ("#0E3386", "#CC3433"), "CIN": ("#C6011F", "#27251F"),
    "CLE": ("#0C2340", "#E31937"), "COL": ("#333366", "#27251F"),
    "CWS": ("#27251F", "#C4CED4"), "DET": ("#0C2340", "#FA4616"),
    "HOU": ("#002D62", "#EB6E1F"), "KC": ("#004687", "#BD9B60"),
    "LAA": ("#BA0021", "#003263"), "LAD": ("#005A9C", "#FFFFFF"),
    "MIA": ("#00A3E0", "#27251F"), "MIL": ("#12284B", "#FFC52F"),
    "MIN": ("#002B5C", "#D31145"), "NYM": ("#002D72", "#FF5910"),
    "NYY": ("#0C2340", "#FFFFFF"), "PHI": ("#E81828", "#002D72"),
    "PIT": ("#27251F", "#FDB827"), "SD": ("#2F241D", "#FFC425"),
    "SEA": ("#0C2C56", "#005C5C"), "SF": ("#27251F", "#FD5A1E"),
    "STL": ("#C41E3A", "#0C2340"), "TB": ("#092C5C", "#8FBCE6"),
    "TEX": ("#003278", "#C0111F"), "TOR": ("#134A8E", "#E8291C"),
    "WSH": ("#14225A", "#AB0003"),
}


def theme_colors():
    return TEAM_PALETTES.get(st.session_state.get("portfolio_opening_team"), DEFAULT)


def readable_text(color):
    rgb = tuple(int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    linear = tuple(x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in rgb)
    luminance = sum(x * weight for x, weight in zip(linear, (.2126, .7152, .0722)))
    return "#101820" if luminance > .18 else "#FFFFFF"


def apply_theme():
    primary, secondary = theme_colors()
    variables = (
        f":root {{ --team-primary: {primary}; --team-secondary: {secondary}; "
        f"--team-primary-text: {readable_text(primary)}; "
        f"--team-secondary-text: {readable_text(secondary)}; }}"
    )
    st.markdown(
        "<style>" + variables + """
        h1, h2, h3 { color: var(--team-primary); }
        h1 { border-bottom: 3px solid var(--team-secondary); padding-bottom: .35rem; }
        div[data-testid="stMetric"] {
            background: #f5f8fc; border: 1px solid #dce5ef;
            border-left: 4px solid var(--team-secondary);
            border-radius: .5rem; padding: .7rem .9rem;
        }
        div[data-testid="stMetricLabel"] { color: var(--team-primary); }
        div[data-testid="stMetricLabel"] p {
            white-space: normal !important;
            overflow-wrap: normal;
            line-height: 1.2;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--team-primary); border-bottom-color: var(--team-secondary);
        }
        div[data-testid="stDataFrame"] [role="columnheader"],
        div[data-testid="stDataFrame"] .gdg-header {
            background: #dce8f5 !important;
            color: var(--team-primary) !important;
            font-weight: 700 !important;
        }
        .baseball-table-wrap { max-height: 460px; overflow: auto; border: 1px solid #dce5ef; border-radius: .45rem; }
        .baseball-table { border-collapse: separate; border-spacing: 0; min-width: 100%; width: max-content; font-size: .9rem; }
        .baseball-table th { position: sticky; top: 0; z-index: 2; color: var(--team-primary-text); background: var(--team-primary); padding: .65rem .8rem; text-align: left; white-space: nowrap; }
        .baseball-table th:nth-child(even) { color: var(--team-secondary-text); background: var(--team-secondary); box-shadow: inset 0 -2px 0 var(--team-primary); }
        .baseball-table td { padding: .45rem .8rem; border-bottom: 1px solid #e6edf4; white-space: nowrap; background: white; }
        .baseball-table tbody tr:hover td { background: #e9f1fb; }
        .baseball-table th.sticky-column { left: 0; z-index: 4; }
        .baseball-table td.sticky-column { position: sticky; left: 0; z-index: 1; }
        .baseball-table tr.selected-player td { background: #e9f1fb; font-weight: 700; }
        .baseball-table tr.selected-player td { position: sticky; top: 38px; z-index: 2; }
        .baseball-table tr.selected-player td.sticky-column { left: 0; z-index: 3; }
        </style>
        """,
        unsafe_allow_html=True,
    )
