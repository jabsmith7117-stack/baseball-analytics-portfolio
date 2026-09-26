"""Entrypoint and explicit sidebar labels for the portfolio."""
import streamlit as st
from team_preferences import opening_team

st.set_page_config(page_title="Baseball Analytics Portfolio", layout="wide")

# Streamlit clears URL query parameters during multipage navigation. Capture
# the link's team once and retain it for selectors on subsequent pages.
team_from_link = st.query_params.get("team", "").upper()
if len(team_from_link) in (2, 3) and team_from_link.isalpha():
    st.session_state["portfolio_opening_team"] = team_from_link

page = st.navigation([
    st.Page("home.py", title="Home", default=True),
    st.Page("pages/1_Advanced_Scouting_Report.py", title="Advanced Scouting Report"),
    st.Page("pages/2_Pitcher_Arsenal_Stuff_Model.py", title="Pitcher Arsenal / Stuff+"),
    st.Page("pages/3_Batter_Pitcher_Matchup_Predictor.py", title="Matchup Predictor"),
    st.Page("pages/4_Scouting_Comparison_Tool.py", title="Scouting Comparison Tool"),
])
page.run()
